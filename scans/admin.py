from django.contrib import admin

from .models import ScanResult, ScanUpload


# These classes are what change how data is displayed in the admin panel
@admin.register(ScanUpload)
class ScanUploadAdmin(admin.ModelAdmin):
    list_display = ("user", "uploaded_at", "processed")
    list_filter = ("processed", "uploaded_at")


@admin.register(ScanResult)
class ScanResultAdmin(admin.ModelAdmin):
    list_display = ("upload", "scan_date", "weight_lb", "percent_body_fat")
