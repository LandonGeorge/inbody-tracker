import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ScanResultEditForm, ScanUploadForm
from .models import ScanResult, ScanUpload
from .ocr import extract_text, parse_inbody_text


@login_required
def upload_scan(request):
    if request.method == "POST":
        form = ScanUploadForm(request.POST, request.FILES)
        if form.is_valid():
            for image in form.cleaned_data["images"]:
                scan = ScanUpload.objects.create(user=request.user, image=image)

                raw_text = extract_text(scan.image.path)
                scan.raw_ocr_text = raw_text
                scan.processed = True
                scan.save()

                parsed = parse_inbody_text(raw_text)
                scan_date = parsed.pop("scan_date") or scan.uploaded_at.date()

                ScanResult.objects.create(upload=scan, scan_date=scan_date, **parsed)

            return redirect("scan_list")
    else:
        form = ScanUploadForm()

    return render(request, "scans/upload.html", {"form": form})


@login_required
def scan_list(request):
    scans = request.user.scans.all()
    for scan in scans:
        if hasattr(scan, "result"):
            scan.date_likely_wrong = scan.result.scan_date == scan.uploaded_at.date()
        else:
            scan.date_likely_wrong = False

    return render(request, "scans/list.html", {"scans": scans})


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
        request,
        "scans/dashboard.html",
        {"chart_data_json": json.dumps(chart_data), "latest": results.last()},
    )


@login_required
def edit_scan_result(request, pk):
    result = get_object_or_404(ScanResult, pk=pk, upload__user=request.user)

    if request.method == "POST":
        form = ScanResultEditForm(request.POST, instance=result)
        if form.is_valid():
            form.save()
            return redirect("scan_list")
    else:
        form = ScanResultEditForm(instance=result)

    return render(request, "scans/edit_result.html", {"form": form})


@login_required
def delete_scan(request, pk):
    scan = get_object_or_404(ScanUpload, pk=pk, user=request.user)

    if request.method == "POST":
        scan.delete()
        return redirect("scan_list")

    return render(request, "scans/confirm_delete.html", {"scan": scan})
