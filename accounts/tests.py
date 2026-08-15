import pytest
from django.contrib.auth.models import User
from django.urls import reverse


@pytest.mark.django_db
def test_signup_creates_user_and_logs_in(client):
    response = client.post(
        reverse("signup"),
        {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "a-strong-password-1",
            "password2": "a-strong-password-1",
        },
    )

    assert response.status_code == 302
    assert User.objects.filter(username="newuser").exists()
    assert response.wsgi_request.user.is_authenticated


@pytest.mark.django_db
def test_signup_rerenders_form_on_password_mismatch(client):
    response = client.post(
        reverse("signup"),
        {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "a-strong-password-1",
            "password2": "does-not-match",
        },
    )

    assert response.status_code == 200
    assert not User.objects.filter(username="newuser").exists()
