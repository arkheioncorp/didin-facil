import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_auth_endpoints_missing(async_client: AsyncClient):
    # Verify Email
    response = await async_client.get("/auth/verify-email?token=test")
    assert response.status_code == 200
    assert response.json() == {"message": "Email verified successfully"}

    # Forgot Password
    response = await async_client.post(
        "/auth/forgot-password", json={"email": "test@example.com"}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Password reset email sent"}

    # Reset Password
    response = await async_client.post(
        "/auth/reset-password",
        json={
            "token": "test",
            "new_password": "password123",
            "confirm_password": "password123",
        },
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Password reset successfully"}


@pytest.mark.asyncio
async def test_product_endpoints_missing(async_client: AsyncClient, test_app):
    # Override auth dependency
    from api.middleware.auth import get_current_user

    test_app.dependency_overrides[get_current_user] = lambda: {
        "id": "test",
        "plan": "pro",
    }

    # Export
    response = await async_client.post(
        "/products/export", json={"product_ids": ["1", "2"], "format": "csv"}
    )
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]

    # Stats
    response = await async_client.get("/products/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "trending" in data

    # Clean up
    del test_app.dependency_overrides[get_current_user]
