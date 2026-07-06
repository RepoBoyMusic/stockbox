"""Configuración central de la app.

Lee variables desde .env (local) o del entorno (producción).
Si no hay DATABASE_URL definida, usa un SQLite local: cero fricción en desarrollo.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-solo-para-desarrollo")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'stockbox.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
