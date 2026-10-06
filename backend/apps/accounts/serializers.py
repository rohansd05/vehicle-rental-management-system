"""Accounts serializers: input validation only. Business rules live in services.py."""

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import RegexValidator
from django.utils import timezone
from rest_framework import serializers

from .models import User

# Proposed (docs/decisions.md D20): 10-15 digits with an optional leading +.
mobile_validator = RegexValidator(
    r"^\+?[0-9]{10,15}$", "Enter a mobile number of 10 to 15 digits, optionally starting with +."
)


def otp_code_field() -> serializers.CharField:
    length = settings.OTP_CODE_LENGTH
    return serializers.RegexField(
        rf"^[0-9]{{{length}}}$",
        max_length=length,
        error_messages={"invalid": f"Enter the {length}-digit code."},
    )


def _check_password_rules(password: str, user: User) -> None:
    try:
        validate_password(password, user=user)
    except DjangoValidationError as exc:
        raise serializers.ValidationError({"password": list(exc.messages)}) from exc


class DetailSerializer(serializers.Serializer):
    detail = serializers.CharField()


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(
        write_only=True, trim_whitespace=False, style={"input_type": "password"}
    )
    name = serializers.CharField(max_length=150)
    mobile_no = serializers.CharField(max_length=15, validators=[mobile_validator])
    address = serializers.CharField()
    date_of_birth = serializers.DateField()
    emergency_contact_name = serializers.CharField(max_length=150)  # SA-4
    emergency_contact_mobile = serializers.CharField(max_length=15, validators=[mobile_validator])

    def validate_email(self, value: str) -> str:
        value = value.lower()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("An account with this e-mail address already exists.")
        return value

    def validate_date_of_birth(self, value):
        if value >= timezone.localdate():
            raise serializers.ValidationError("Enter a date of birth in the past.")
        return value

    def validate(self, attrs):
        candidate = User(email=attrs["email"], name=attrs["name"], mobile_no=attrs["mobile_no"])
        _check_password_rules(attrs["password"], candidate)
        return attrs


class RegisterResponseSerializer(serializers.Serializer):
    email = serializers.EmailField()
    detail = serializers.CharField()


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = otp_code_field()


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True, trim_whitespace=False, style={"input_type": "password"}
    )


class UserSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "name", "role"]


class TokenPairSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSummarySerializer()


class RefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "name", "mobile_no", "address", "role"]
        read_only_fields = fields


class ProfileUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150, required=False)
    mobile_no = serializers.CharField(max_length=15, required=False, validators=[mobile_validator])
    address = serializers.CharField(required=False, allow_blank=True)


class ProfileUpdateResponseSerializer(ProfileSerializer):
    mobile_change_pending = serializers.BooleanField()

    class Meta(ProfileSerializer.Meta):
        fields = [*ProfileSerializer.Meta.fields, "mobile_change_pending"]
        read_only_fields = fields


class OTPCodeSerializer(serializers.Serializer):
    code = otp_code_field()


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_current_password(self, value: str) -> str:
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError("The current password is incorrect.")
        return value

    def validate(self, attrs):
        _check_password_rules(attrs["new_password"], self.context["request"].user)
        return attrs
