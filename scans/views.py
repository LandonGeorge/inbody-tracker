from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import ScanUploadForm


@login_required
def upload_scan(request):
    if request.method == "POST":
        form = ScanUploadForm(request.POST, request.FILES)
        if form.is_valid():
            scan = form.save(commit=False)
            scan.user = request.user
            scan.save()
            return redirect("scan_list")
    else:
        form = ScanUploadForm()

    return render(request, "scans/upload.html", {"form": form})


def scan_list(request):
    return render(request, "scans/list.html", {"scans": request.user.scans.all()})
