"""Accounts API views: registration, OTP, sign-in, tokens, profile and password.

Every view declares permission_classes explicitly (SE-4) and a throttle
scope. Customer self-registration is the only way to create an account
through the API; staff, technician, administrator and branch manager
accounts are created in the Django admin.
"""

from django.conf import settings
from django.contrib.auth import authenticate, user_logged_in
from django.core.cache import cache
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import Throttled, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from . import services
from .serializers import (
    DetailSerializer,
    EmailSerializer,
    LoginSerializer,
    OTPCodeSerializer,
    PasswordChangeSerializer,
    ProfileSerializer,
    ProfileUpdateResponseSerializer,
    ProfileUpdateSerializer,
    RefreshSerializer,
    RegisterResponseSerializer,
    RegisterSerializer,
    TokenPairSerializer,
    UserSummarySerializer,
    VerifyOTPSerializer,
)

# SE-8: the same message whatever the reason, so it never reveals whether an
# account exists, is unverified or is disabled.
GENERIC_LOGIN_FAILURE = "Unable to sign in with the details provided."
GENERIC_OTP_FAILURE = "The code is invalid or has expired."

AUTH_TAG = "Authentication"
PROFILE_TAG = "Profile"


class _ThrottledView(APIView):
    throttle_classes = [ScopedRateThrottle]


class _PublicView(_ThrottledView):
    """Anonymous endpoints: no authentication is attempted at all."""

    permission_classes = [AllowAny]
    authentication_classes: list = []


class RegisterView(_PublicView):
    """SE-7: create an inactive customer account and send an OTP by SMS."""

    throttle_scope = "auth_register"

    @extend_schema(
        tags=[AUTH_TAG],
        summary="Register as a customer",
        request=RegisterSerializer,
        responses={201: RegisterResponseSerializer, 400: OpenApiResponse(description="Invalid")},
        examples=[
            OpenApiExample(
                "Register",
                request_only=True,
                value={
                    "email": "asha@example.com",
                    "password": "Str0ng!Passw0rd",
                    "name": "Asha Rao",
                    "mobile_no": "+919812345678",
                    "address": "14 Hill Road, Bandra (W), Mumbai 400050",
                    "date_of_birth": "1996-04-12",
                    "emergency_contact_name": "Ravi Rao",
                    "emergency_contact_mobile": "+919812300000",
                },
            )
        ],
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer = services.register_customer(**serializer.validated_data, request=request)
        body = {
            "email": customer.user.email,
            "detail": "Account created. Enter the code sent by SMS to verify your mobile number.",
        }
        return Response(body, status=status.HTTP_201_CREATED)


class VerifyOTPView(_PublicView):
    """SE-7: verify the registration code and activate the account."""

    throttle_scope = "auth_otp_verify"

    @extend_schema(
        tags=[AUTH_TAG],
        summary="Verify the registration OTP",
        request=VerifyOTPSerializer,
        responses={200: DetailSerializer, 400: DetailSerializer},
        examples=[
            OpenApiExample(
                "Verify", request_only=True, value={"email": "asha@example.com", "code": "123456"}
            )
        ],
    )
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            services.activate_account(**serializer.validated_data, request=request)
        except services.OTPError as exc:
            raise ValidationError({"detail": GENERIC_OTP_FAILURE}) from exc
        return Response({"detail": "Your account is verified. You can now sign in."})


class ResendOTPView(_PublicView):
    """Send a new registration code; the previous one stops working."""

    throttle_scope = "auth_otp_resend"

    @extend_schema(
        tags=[AUTH_TAG],
        summary="Resend the registration OTP",
        request=EmailSerializer,
        responses={200: DetailSerializer, 429: DetailSerializer},
        examples=[OpenApiExample("Resend", request_only=True, value={"email": "asha@example.com"})],
    )
    def post(self, request):
        serializer = EmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower()
        cooldown = settings.OTP_RESEND_COOLDOWN.total_seconds()
        # The cooldown applies to any address, so it reveals nothing either.
        if not cache.add(f"otp-resend:{email}", True, timeout=cooldown):
            raise Throttled(wait=cooldown, detail="Please wait before requesting another code.")
        services.resend_registration_otp(email, request)
        return Response(
            {"detail": "If an unverified account uses this address, a new code has been sent."}
        )


class LoginView(_PublicView):
    """Sign in and receive a JWT pair. SE-8 lockout is applied by django-axes."""

    throttle_scope = "auth_login"

    @extend_schema(
        tags=[AUTH_TAG],
        summary="Sign in",
        request=LoginSerializer,
        responses={
            200: TokenPairSerializer,
            401: DetailSerializer,
            403: OpenApiResponse(DetailSerializer, description="Account locked (SE-8)"),
        },
        examples=[
            OpenApiExample(
                "Sign in",
                request_only=True,
                value={"email": "customer@vrms.test", "password": "Demo@1234"},
            )
        ],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower()
        # The plain HttpRequest, so axes' flags reach AxesMiddleware.
        django_request = request._request
        user = authenticate(
            django_request, username=email, password=serializer.validated_data["password"]
        )
        if user is None:
            services.record_failed_login(email, request)
            # An explicit 401: with no authentication classes DRF would turn
            # AuthenticationFailed into a 403.
            return Response(
                {"detail": GENERIC_LOGIN_FAILURE, "code": "authentication_failed"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        # Resets the axes failure count (consecutive failures, SE-8).
        user_logged_in.send(sender=user.__class__, request=django_request, user=user)
        services.record_login(user, request)
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSummarySerializer(user).data,
            }
        )


class RefreshView(TokenRefreshView):
    """SE-9: trade a refresh token for a new pair; the old one is blacklisted."""

    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_token"

    @extend_schema(
        tags=[AUTH_TAG],
        summary="Refresh the token pair",
        examples=[OpenApiExample("Refresh", request_only=True, value={"refresh": "<refresh>"})],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class LogoutView(_ThrottledView):
    """Blacklist the refresh token so the session cannot be renewed."""

    permission_classes = [IsAuthenticated]
    throttle_scope = "auth_token"

    @extend_schema(
        tags=[AUTH_TAG],
        summary="Sign out",
        request=RefreshSerializer,
        responses={204: None, 400: DetailSerializer},
        examples=[OpenApiExample("Sign out", request_only=True, value={"refresh": "<refresh>"})],
    )
    def post(self, request):
        serializer = RefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            token = RefreshToken(serializer.validated_data["refresh"])
        except TokenError as exc:
            raise ValidationError({"detail": "The token is invalid or expired."}) from exc
        claim = settings.SIMPLE_JWT.get("USER_ID_CLAIM", "user_id")
        if str(token.get(claim)) != str(request.user.pk):
            raise ValidationError({"detail": "The token is invalid or expired."})
        token.blacklist()
        services.record_logout(request.user, request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordChangeView(_ThrottledView):
    """Change the password; every session ends and the user signs in again."""

    permission_classes = [IsAuthenticated]
    throttle_scope = "auth_password"

    @extend_schema(
        tags=[AUTH_TAG],
        summary="Change password",
        request=PasswordChangeSerializer,
        responses={200: DetailSerializer, 400: OpenApiResponse(description="Invalid")},
        examples=[
            OpenApiExample(
                "Change password",
                request_only=True,
                value={"current_password": "Demo@1234", "new_password": "N3w!Passw0rd-2026"},
            )
        ],
    )
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        services.change_password(request.user, serializer.validated_data["new_password"], request)
        return Response({"detail": "Password changed. Please sign in again."})


class MeView(_ThrottledView):
    """The signed-in user's own profile."""

    permission_classes = [IsAuthenticated]
    throttle_scope = "auth_profile"

    @extend_schema(tags=[PROFILE_TAG], summary="My profile", responses=ProfileSerializer)
    def get(self, request):
        return Response(ProfileSerializer(request.user).data)

    @extend_schema(
        tags=[PROFILE_TAG],
        summary="Update my profile",
        description=(
            "Name and address change at once. A new mobile number is applied only after "
            "the code sent to it is confirmed at /api/v1/me/verify-mobile/ (SE-7)."
        ),
        request=ProfileUpdateSerializer,
        responses=ProfileUpdateResponseSerializer,
        examples=[
            OpenApiExample("Change mobile", request_only=True, value={"mobile_no": "+919898989898"})
        ],
    )
    def patch(self, request):
        serializer = ProfileUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        pending = services.update_profile(request.user, serializer.validated_data, request)
        data = ProfileSerializer(request.user).data
        return Response({**data, "mobile_change_pending": pending})


class ConfirmMobileView(_ThrottledView):
    """SE-7: confirm a new mobile number with the code sent to it."""

    permission_classes = [IsAuthenticated]
    throttle_scope = "auth_otp_verify"

    @extend_schema(
        tags=[PROFILE_TAG],
        summary="Confirm a new mobile number",
        request=OTPCodeSerializer,
        responses={200: ProfileSerializer, 400: DetailSerializer},
        examples=[OpenApiExample("Confirm", request_only=True, value={"code": "123456"})],
    )
    def post(self, request):
        serializer = OTPCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = services.confirm_mobile_change(
                request.user, serializer.validated_data["code"], request
            )
        except services.OTPError as exc:
            raise ValidationError({"detail": GENERIC_OTP_FAILURE}) from exc
        return Response(ProfileSerializer(user).data)
