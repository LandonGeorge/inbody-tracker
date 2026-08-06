import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import ScanUploadForm
from .models import ScanResult
from .ocr import extract_text, parse_inbody_text


@login_required
def upload_scan(request):
    if request.method == "POST":
        form = ScanUploadForm(request.POST, request.FILES)
        if form.is_valid():
            scan = form.save(commit=False)
            scan.user = request.user
            scan.save()

            raw_text = extract_text(scan.image.path)
            scan.raw_ocr_text = raw_text
            scan.processed = True
            scan.save()

            parsed = parse_inbody_text(raw_text)
            ScanResult.objects.create(
                upload=scan, scan_date=scan.uploaded_at.date(), **parsed
            )

            return redirect("scan_list")
    else:
        form = ScanUploadForm()

    return render(request, "scans/upload.html", {"form": form})


def scan_list(request):
    return render(request, "scans/list.html", {"scans": request.user.scans.all()})


@login_required
def dashboard(request):
    results = ScanResult.objects.filter(upload__user=request.user).order_by("scan_date")

    chart_data = {
        "labels": [r.scan_date.strftime("%b %d, %Y") for r in results],
        "weight": [float(r.weight_lb) if r.weight_lb else None for r in results],
        "muscle_mass": [
            float(r.skeletal_muscle_mass_lb) if r.skeletal_muscle_mass_lb else None
            for r in results
        ],
        "body_fat_pct": [
            float(r.percent_body_fat) if r.percent_body_fat else None for r in results
        ],
    }

    return render(
        request, "scans/dashboard.html", {"chart_data_json": json.dumps(chart_data)}
    )
