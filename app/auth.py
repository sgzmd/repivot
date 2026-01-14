from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request
from fastapi import HTTPException, Depends, status
from .config import settings

# Helper to mock config for Authlib if needed, or just pass env vars
# Authlib Starlette client can take a Starlette Config object or dict
oauth = OAuth()

oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


async def get_current_user(request: Request):
    if settings.AUTH_BYPASS:
        return {"email": settings.AUTH_BYPASS, "name": "Dev User"}
    user = request.session.get("user")
    if not user:
        return None
    return user


async def require_auth(user: dict = Depends(get_current_user)):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    email = user.get("email")
    if email not in settings.ALLOWED_USERS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    return user
