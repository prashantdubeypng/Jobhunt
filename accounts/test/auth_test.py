# accounts/tests/test_auth.py

import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_user_signup(api_client):
    url = reverse("signup")
    data = {
        "email": "test@example.com",
        "password": "strongpassword123"
    }
    response = api_client.post(url, data)

    assert response.status_code == 201
    assert "id" in response.data