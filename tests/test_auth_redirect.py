from fastapi.testclient import TestClient
from app.main import app
from app.auth import require_auth

client = TestClient(app)

def test_unauthenticated_request_exceptions():
    # Ensure require_auth is NOT overridden
    if require_auth in app.dependency_overrides:
        del app.dependency_overrides[require_auth]

    response = client.get("/reports", follow_redirects=False)
    
    # New behavior: 307 Redirect to /login due to exception handler
    assert response.status_code == 307
    assert response.headers["location"] == "/login"
