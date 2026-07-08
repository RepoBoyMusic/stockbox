"""Modelos de datos: cada clase es una tabla en la base.

SQLAlchemy es un ORM: escribimos clases Python y él genera el SQL.
Convención que usamos: nombres de clase en inglés (Product, Movement),
columnas en español porque la UI y el dominio son en español.
"""
from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login guarda el id del usuario en la sesión (cookie firmada).
    En cada request usa esta función para recuperar el usuario completo."""
    return db.session.get(User, int(user_id))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    # NUNCA se guarda la contraseña real: solo un hash irreversible.
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(40), unique=True, nullable=False)
    nombre = db.Column(db.String(120), nullable=False)
    categoria = db.Column(db.String(60), nullable=False, default="General")
    precio = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    stock = db.Column(db.Integer, nullable=False, default=0)
    stock_minimo = db.Column(db.Integer, nullable=False, default=0)
    ubicacion = db.Column(db.String(60))  # ej: "Depósito · Rack B2"
    talles = db.Column(db.String(60))  # curva de talles del modelo, ej: "35–45"
    creado_en = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Un producto tiene muchos movimientos; desde un movimiento se llega
    # al producto con `movimiento.producto`. cascade: al borrar el producto
    # se borra su historial (en un sistema real harías soft-delete).
    movimientos = db.relationship(
        "Movement", backref="producto", lazy=True, cascade="all, delete-orphan"
    )

    @property
    def bajo_stock(self):
        return self.stock <= self.stock_minimo


class Movement(db.Model):
    """Historial de entradas y salidas. El stock del producto se actualiza
    junto con cada movimiento: así siempre podés auditar por qué el stock
    está donde está (igual que un sistema de depósito real)."""

    TIPOS = ("entrada", "salida")
    MOTIVOS = ("compra", "venta", "ajuste", "devolucion")

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    tipo = db.Column(db.String(10), nullable=False)
    motivo = db.Column(db.String(20), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    nota = db.Column(db.String(200))
    fecha = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
