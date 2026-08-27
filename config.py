"""
Loads configuration from .env (via python-dotenv) so the connection
string and backend choice never get hardcoded into the app.
"""

import os
from dotenv import load_dotenv

load_dotenv()  # no-op if .env doesn't exist (e.g. in CI) — falls back to defaults below

DB_BACKEND = os.getenv("DB_BACKEND", "sqlite")  # "sqlite" or "postgres"
DATABASE_URL = os.getenv("DATABASE_URL", "")
SQLITE_PATH = os.getenv("SQLITE_PATH", "tasks.db")
