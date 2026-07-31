from django.contrib.auth.models import User
from django.db import models


class ScanUpload(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="scans")
    image = models.ImageField(upload_to="scan_receipts/%Y/%m/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    raw_ocr_text = models.TextField(blank=True)
    processed = models.BooleanField(default=False)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"Scan by {self.user.username} on {self.uploaded_at.date()}"


# Create your models here.
class ScanResult(models.Model):
    upload = models.OneToOneField(
        ScanUpload, on_delete=models.CASCADE, related_name="result"
    )
    scan_date = models.DateField()

    weight_lb = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True
    )
    skeletal_muscle_mass_lb = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True
    )
    body_fat_mass_lb = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True
    )
    total_body_water_lb = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True
    )
    lean_body_mass_lb = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True
    )
    percent_body_fat = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True
    )
    bmi = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    basal_metabolic_rate_kcal = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Result for {self.upload.user.username} — {self.scan_date}"
