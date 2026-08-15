from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import ScanResult, ScanUpload

User = get_user_model()


def _fake_image(name="receipt.jpg"):
    return SimpleUploadedFile(name, b"fake image bytes", content_type="image/jpeg")


class LoginRequiredTests(TestCase):
    def setUp(self):
        self.other_user = User.objects.create_user(username="bob", password="pw12345!")
        scan = ScanUpload.objects.create(user=self.other_user, image=_fake_image())
        self.other_users_result = ScanResult.objects.create(
            upload=scan, scan_date=date(2026, 1, 1)
        )

    def test_upload_scan_requires_login(self):
        response = self.client.get(reverse("upload_scan"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("login")))

    def test_scan_list_requires_login(self):
        response = self.client.get(reverse("scan_list"))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_edit_scan_result_requires_login(self):
        response = self.client.get(
            reverse("edit_scan_result", args=[self.other_users_result.pk])
        )
        self.assertEqual(response.status_code, 302)

    def test_delete_scan_requires_login(self):
        response = self.client.get(
            reverse("delete_scan", args=[self.other_users_result.upload.pk])
        )
        self.assertEqual(response.status_code, 302)


class ScanScopingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="pw12345!")
        self.other_user = User.objects.create_user(username="bob", password="pw12345!")
        other_scan = ScanUpload.objects.create(user=self.other_user, image=_fake_image())
        self.other_users_result = ScanResult.objects.create(
            upload=other_scan, scan_date=date(2026, 1, 1)
        )
        self.client.force_login(self.user)

    def test_edit_scan_result_scoped_to_owner(self):
        response = self.client.get(
            reverse("edit_scan_result", args=[self.other_users_result.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_delete_scan_scoped_to_owner(self):
        response = self.client.get(
            reverse("delete_scan", args=[self.other_users_result.upload.pk])
        )
        self.assertEqual(response.status_code, 404)
        self.assertTrue(
            ScanUpload.objects.filter(pk=self.other_users_result.upload.pk).exists()
        )

    def test_scan_list_only_shows_own_scans(self):
        own_scan = ScanUpload.objects.create(user=self.user, image=_fake_image())
        ScanResult.objects.create(upload=own_scan, scan_date=date(2026, 1, 2))

        response = self.client.get(reverse("scan_list"))

        self.assertEqual(list(response.context["scans"]), [own_scan])

    def test_delete_scan_removes_only_own_scan(self):
        scan = ScanUpload.objects.create(user=self.user, image=_fake_image())
        ScanResult.objects.create(upload=scan, scan_date=date(2026, 1, 2))

        response = self.client.post(reverse("delete_scan", args=[scan.pk]))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(ScanUpload.objects.filter(pk=scan.pk).exists())


class UploadScanTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="pw12345!")
        self.client.force_login(self.user)

    @patch("scans.views.extract_text", return_value="fake ocr text")
    def test_upload_scan_creates_a_result_per_file(self, mock_extract_text):
        parsed_fields = [
            {"scan_date": date(2026, 1, 1), "weight_lb": None},
            {"scan_date": date(2026, 1, 2), "weight_lb": None},
        ]
        with patch("scans.views.parse_inbody_text", side_effect=parsed_fields):
            response = self.client.post(
                reverse("upload_scan"),
                {"images": [_fake_image("a.jpg"), _fake_image("b.jpg")]},
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(ScanUpload.objects.filter(user=self.user).count(), 2)
        self.assertEqual(ScanResult.objects.filter(upload__user=self.user).count(), 2)
        self.assertEqual(mock_extract_text.call_count, 2)

    @patch("scans.views.extract_text", return_value="fake ocr text")
    @patch(
        "scans.views.parse_inbody_text",
        return_value={"scan_date": None, "weight_lb": None},
    )
    def test_upload_scan_falls_back_to_upload_date_when_date_not_parsed(
        self, mock_parse_inbody_text, mock_extract_text
    ):
        self.client.post(reverse("upload_scan"), {"images": [_fake_image()]})

        result = ScanResult.objects.get(upload__user=self.user)
        self.assertEqual(result.scan_date, result.upload.uploaded_at.date())
