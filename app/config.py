import os
from typing import List

class Settings:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev_secret_key")
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    ALLOWED_USERS: List[str] = os.getenv("ALLOWED_USERS", "").split(",")
    AUTH_BYPASS: str = os.getenv("AUTH_BYPASS", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./revolut.db")

settings = Settings()
