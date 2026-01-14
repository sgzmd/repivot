from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

client = TestClient(app)


@patch("app.main.oauth.google.authorize_redirect")
def test_login_redirect_https_proxy(mock_authorize_redirect):
    """
    Verifies that when the X-Forwarded-Proto header is set to 'https',
    the redirect_uri passed to authorize_redirect uses 'https'.
    """
    # Setup mock to return a dummy response so the endpoint finishes
    mock_authorize_redirect.return_value = "mock_response"

    # Simulate a request coming through an HTTPS proxy
    # Cloudflare typically passes the original Host header and adds X-Forwarded-Proto
    headers = {"X-Forwarded-Proto": "https", "Host": "spend.repivot.com"}
    client.get("/login", headers=headers)

    # Check that authorize_redirect was called
    assert mock_authorize_redirect.called

    # Get the arguments passed to the mock
    call_args = mock_authorize_redirect.call_args
    # call_args[0] are positional args: (request, redirect_uri)
    # verify the redirect_uri (2nd argument) starts with https
    redirect_uri = str(call_args[0][1])

    assert redirect_uri.startswith(
        "https://"
    ), f"Expected HTTPS redirect URI, got {redirect_uri}"
    assert "spend.repivot.com" in redirect_uri
