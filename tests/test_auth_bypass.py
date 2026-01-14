import pytest
from unittest.mock import MagicMock, patch
from app.auth import get_current_user


@pytest.mark.asyncio
async def test_auth_bypass_active():
    # Mock settings.AUTH_BYPASS
    with patch("app.config.settings.AUTH_BYPASS", "bypass@revolut.com"):
        request = MagicMock()
        user = await get_current_user(request)
        assert user["email"] == "bypass@revolut.com"
        assert user["name"] == "Dev User"


@pytest.mark.asyncio
async def test_auth_bypass_inactive():
    # Mock settings.AUTH_BYPASS as empty
    with patch("app.config.settings.AUTH_BYPASS", ""):
        request = MagicMock()
        # Mock session get
        request.session.get.return_value = None
        user = await get_current_user(request)
        assert user is None

        # With session
        request.session.get.return_value = {"email": "real@user.com"}
        user = await get_current_user(request)
        assert user["email"] == "real@user.com"
