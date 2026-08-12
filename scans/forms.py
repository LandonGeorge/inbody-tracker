from django import forms

from .models import ScanResult, ScanUpload


class ScanUploadForm(forms.ModelForm):
    class Meta:
        model = ScanUpload
        fields = ["image"]


class ScanResultEditForm(forms.ModelForm):
    class Meta:
        model = ScanResult
        fields = [
            "scan_date",
            "weight_lb",
            "skeletal_muscle_mass_lb",
            "body_fat_mass_lb",
            "total_body_water_lb",
            "lean_body_mass_lb",
            "percent_body_fat",
            "bmi",
        ]
        widgets = {
            "scan_date": forms.DateInput(attrs={"type": "date"}),
        }
