from django import forms

from .models import ScanResult, ScanUpload


class MultipleFileInput(forms.ClearableFileInput):
    """Renders `<input type="file" multiple>`. Plain FileInput doesn't
    support the `multiple` attribute on its own.
    """

    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """A FileField that accepts and validates a list of uploaded files
    instead of just one. Django's documented pattern for handling
    `<input multiple>` in a form (FileField.clean() otherwise assumes a
    single file).
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(d, initial) for d in data]
        return single_file_clean(data, initial)


class ScanUploadForm(forms.Form):
    images = MultipleFileField(
        label="Receipt photo(s)",
        help_text="Select one or more InBody receipt photos to upload.",
    )


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
