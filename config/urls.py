from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import RedirectView
from django.views.static import serve

urlpatterns = [
    path("", RedirectView.as_view(url="/accounts/login/", permanent=False)),
    path("admin/", admin.site.urls),
    path("scans/", include("scans.urls")),
    path("accounts/", include("accounts.urls")),
    # Django's static() helper only serves media when DEBUG=True, so it's
    # wired up manually here to also work in production (needed on Railway).
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
]
