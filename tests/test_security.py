import os
from unittest.mock import patch

os.environ["JWT_SECRET"] = "ci_test_secret_key_for_ automated_validation"

from fastapi.testclient import TestClient
from app.main import app
from app.security import create_jwt_token

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_unauthenticated_vault_access_blocked():
    
    response = client.get("/vault-data")
    assert response.status_code in [401, 403]


def test_tampered_jwt_blocked():
    
    response = client.get(
        "/vault-data", headers={"Authorization": "Bearer fake.tampered.token"}
    )
    assert response.status_code == 401
    assert "Invalid or tampered token" in response.json()["detail"]


@patch("app.security.redis_client.get", return_value=None)
def test_rbac_viewer_blocked_from_admin_endpoint(mock_redis):
   
    viewer_token = create_jwt_token(username="guest", role="viewer")
    response = client.delete(
        "/admin/purge-logs",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert response.status_code == 403
    assert "Requires 'admin' role" in response.json()["detail"]


@patch("app.security.redis_client.get", return_value=None)
def test_rbac_admin_allowed_on_admin_endpoint(mock_redis):
    
    admin_token = create_jwt_token(username="alex", role="admin")
    response = client.delete(
        "/admin/purge-logs",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()["executed_by"] == "alex"


@patch("app.security.redis_client.get", return_value="revoked")
def test_revoked_token_blocked_by_redis_blacklist(mock_redis):
   
    revoked_token = create_jwt_token(username="alex", role="admin")
    response = client.get(
        "/vault-data",
        headers={"Authorization": f"Bearer {revoked_token}"},
    )
    assert response.status_code == 401
    assert "revoked" in response.json()["detail"]