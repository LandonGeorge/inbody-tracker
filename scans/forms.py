from django import forms

from .models import ScanUpload


class ScanUploadForm(forms.ModelForm):
    class Meta:
        model = ScanUpload
        fields = ["image"]
