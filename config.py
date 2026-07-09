"""Configuración central de la app.

Lee variables desde .env (local) o del entorno (producción).
Si no hay DATABASE_URL definida, usa un SQLite local: cero fricción en desarrollo.
En producción (Render) apuntamos DATABASE_URL a un Postgres de Supabase, así
los datos —incluidos los pedidos de la tienda— persisten entre deploys.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _normalizar_db_url(url):
    """Algunos proveedores entregan la URL como 'postgres://', un esquema que
    SQLAlchemy 2.x ya no acepta: hay que usar 'postgresql://'. Normalizamos
    acá para que la misma variable funcione venga como venga."""
    if url and url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-solo-para-desarrollo")
    SQLALCHEMY_DATABASE_URI = _normalizar_db_url(
        os.environ.get("DATABASE_URL")
    ) or f"sqlite:///{BASE_DIR / 'stockbox.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # pool_pre_ping: descarta conexiones muertas antes de usarlas. Importante
    # con Postgres administrado, que cierra conexiones ociosas.
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
