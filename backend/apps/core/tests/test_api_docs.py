"""OpenAPI schema and Swagger UI routes (CO-4)."""

import pytest

pytestmark = pytest.mark.django_db


def test_schema_is_served(api_client):
    response = api_client.get("/api/schema/")
    assert response.status_code == 200
    assert b"/api/v1/health/" in response.content


def test_swagger_ui_is_served(api_client):
    response = api_client.get("/api/docs/")
    assert response.status_code == 200
