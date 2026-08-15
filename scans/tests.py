from datetime import date
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from .models import ScanResult, ScanUpload


def _fake_image(name="receipt.jpg"):
    return SimpleUploadedFile(name, b"fake image bytes", content_type="image/jpeg")


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(username="alice", password="pw12345!")


@pytest.fixture
def other_user(django_user_model):
    return django_user_model.objects.create_user(username="bob", password="pw12345!")


@pytest.fixture
def other_users_result(other_user):
    scan = ScanUpload.objects.create(user=other_user, image=_fake_image())
    return ScanResult.objects.create(upload=scan, scan_date=date(2026, 1, 1))


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url_name",
    ["upload_scan", "scan_list", "dashboard"],
)
def test_view_requires_login(client, url_name):
    response = client.get(reverse(url_name))
    assert response.status_code == 302
    assert response.url == f"{reverse('login')}?next={reverse(url_name)}"


@pytest.mark.django_db
def test_edit_scan_result_requires_login(client, other_users_result):
    response = client.get(reverse("edit_scan_result", args=[other_users_result.pk]))
    assert response.status_code == 302


@pytest.mark.django_db
def test_delete_scan_requires_login(client, other_users_result):
    response = client.get(reverse("delete_scan", args=[other_users_result.upload.pk]))
    assert response.status_code == 302


@pytest.mark.django_db
def test_edit_scan_result_scoped_to_owner(client, user, other_users_result):
    client.force_login(user)
    response = client.get(reverse("edit_scan_result", args=[other_users_result.pk]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_delete_scan_scoped_to_owner(client, user, other_users_result):
    client.force_login(user)
    response = client.get(reverse("delete_scan", args=[other_users_result.upload.pk]))
    assert response.status_code == 404
    assert ScanUpload.objects.filter(pk=other_users_result.upload.pk).exists()


@pytest.mark.django_db
def test_scan_list_only_shows_own_scans(client, user, other_users_result):
    own_scan = ScanUpload.objects.create(user=user, image=_fake_image())
    ScanResult.objects.create(upload=own_scan, scan_date=date(2026, 1, 2))

    client.force_login(user)
    response = client.get(reverse("scan_list"))

    scans = list(response.context["scans"])
    assert scans == [own_scan]


@pytest.mark.django_db
def test_delete_scan_removes_only_own_scan(client, user):
    scan = ScanUpload.objects.create(user=user, image=_fake_image())
    ScanResult.objects.create(upload=scan, scan_date=date(2026, 1, 2))

    client.force_login(user)
    response = client.post(reverse("delete_scan", args=[scan.pk]))

    assert response.status_code == 302
    assert not ScanUpload.objects.filter(pk=scan.pk).exists()


@pytest.mark.django_db
@patch("scans.views.extract_text", return_value="fake ocr text")
def test_upload_scan_creates_a_result_per_file(mock_extract_text, client, user):
    client.force_login(user)

    parsed_fields = [
        {"scan_date": date(2026, 1, 1), "weight_lb": None},
        {"scan_date": date(2026, 1, 2), "weight_lb": None},
    ]
    with patch("scans.views.parse_inbody_text", side_effect=parsed_fields):
        response = client.post(
            reverse("upload_scan"),
            {"images": [_fake_image("a.jpg"), _fake_image("b.jpg")]},
        )

    assert response.status_code == 302
    assert ScanUpload.objects.filter(user=user).count() == 2
    assert ScanResult.objects.filter(upload__user=user).count() == 2
    assert mock_extract_text.call_count == 2


@pytest.mark.django_db
@patch("scans.views.extract_text", return_value="fake ocr text")
@patch("scans.views.parse_inbody_text", return_value={"scan_date": None, "weight_lb": None})
def test_upload_scan_falls_back_to_upload_date_when_date_not_parsed(
    mock_parse, mock_extract_text, client, user
):
    client.force_login(user)

    client.post(reverse("upload_scan"), {"images": [_fake_image()]})

    result = ScanResult.objects.get(upload__user=user)
    assert result.scan_date == result.upload.uploaded_at.date()
