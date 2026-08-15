from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class SignupTests(TestCase):
    def test_signup_creates_user_and_logs_in(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "password1": "a-strong-password-1",
                "password2": "a-strong-password-1",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="newuser").exists())
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_signup_rerenders_form_on_password_mismatch(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "password1": "a-strong-password-1",
                "password2": "does-not-match",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="newuser").exists())
