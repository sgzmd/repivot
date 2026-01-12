from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse
from .config import settings
from .database import engine, Base
from .auth import oauth
from .routers import upload, reports
from .dependencies import templates

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="RePivot")

# Middleware
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

@app.exception_handler(401)
async def unauthorized_exception_handler(request: Request, exc: HTTPException):
    return RedirectResponse(url="/login")

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Routers
app.include_router(upload.router)
app.include_router(reports.router)

@app.get("/login")
async def login(request: Request):
    redirect_uri = request.url_for('auth')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth")
async def auth(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
         # Handle error, maybe redirect to login with error
         return RedirectResponse(url="/")
         
    user = token.get('userinfo')
    if user:
        request.session['user'] = user
    return RedirectResponse(url='/')

@app.get("/logout")
async def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse(url='/')

@app.get("/health")
def health_check():
    return {"status": "ok"}
