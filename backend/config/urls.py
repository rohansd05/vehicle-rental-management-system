"""Root URL configuration.

/api/v1/      versioned REST API (CO-4)
/api/schema/  OpenAPI 3.0 schema
/api/docs/    Swagger UI
/admin/       Django admin
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

api_v1 = [
    path("", include("apps.core.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("fleet/", include("apps.fleet.urls")),
    path("pricing/", include("apps.pricing.urls")),
    path("bookings/", include("apps.bookings.urls")),
    path("rentals/", include("apps.rentals.urls")),
    path("payments/", include("apps.payments.urls")),
    path("maintenance/", include("apps.maintenance.urls")),
    path("notifications/", include("apps.notifications.urls")),
    path("reports/", include("apps.reports.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(api_v1)),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]

if "debug_toolbar" in settings.INSTALLED_APPS:
    from debug_toolbar.toolbar import debug_toolbar_urls

    urlpatterns += debug_toolbar_urls()
