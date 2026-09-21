"""Shared fixtures for backend tests."""
import os
import sys
import pytest
import requests
from pathlib import Path

# Ensure bot module is importable
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Load env from backend/.env before importing bot config
from dotenv import load_dotenv  # noqa: E402
load_dotenv(BACKEND_DIR / ".env")

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/") \
    if "REACT_APP_BACKEND_URL" in os.environ \
    else os.environ["WEBAPP_BASE_URL"].rstrip("/")


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture
def api_client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s
