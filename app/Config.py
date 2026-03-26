"""
config.py - Application configuration loaded from environment variables
=========================================================================

WHY THIS FILE EXISTS:
Your app needs settings (database URL, secret keys, debug mode). These
settings are DIFFERENT in development vs production. Instead of hardcoding
them, we read them from environment variables.

This is a security practice: secrets live in .env (which is gitignored),
not in your code (which is on GitHub for anyone to see).

HOW IT WORKS:
1. You create a .env file with your settings (copied from .env.example)
2. python-dotenv loads those values into environment variables
3. This config file reads them and makes them available to your app

In production, you'd set environment variables on the server directly
(no .env file). The code doesn't care WHERE the variables come from —
it just reads them. That flexibility is the whole point.
"""

import os
from dotenv import load_dotenv

# Load variables from .env file (if it exists)
# In production, variables are set on the server, so .env won't exist — and
# that's fine. load_dotenv() simply does nothing if the file is missing.
load_dotenv()


# =============================================================================
# Application Settings
# =============================================================================
# os.getenv("NAME", "default") reads an environment variable.
# The second argument is the fallback if the variable isn't set.

APP_NAME: str = os.getenv("APP_NAME", "stock-control-api")
APP_ENV: str = os.getenv("APP_ENV", "development")
DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

# Server
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", "8000"))

# Database (Phase 2)
# Format: postgresql://user:password@host:port/database
DATABASE_URL: str = os.getenv("DATABASE_URL", "")

# Connection pool — how many DB connections to keep open
DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "5"))
DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))

# Auth (Phase 4 — not used yet)
SECRET_KEY: str = os.getenv("SECRET_KEY", "")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)