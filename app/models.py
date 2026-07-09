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
    # Pares físicos disponibles, un par por talle: "40, 42, 43" = 3 pares.
    # La tienda vende por talle: al vender el 42, se quita de esta lista.
    talles = db.Column(db.String(60))
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

    @property
    def talles_lista(self):
        """Los talles disponibles como lista: '40, 42, 43' -> ['40','42','43']."""
        if not self.talles:
            return []
        return [t.strip() for t in self.talles.split(",") if t.strip()]

    def quitar_talle(self, talle):
        """Saca un par vendido de la lista de talles disponibles."""
        restantes = [t for t in self.talles_lista if t != talle]
        self.talles = ", ".join(restantes)

    def devolver_talle(self, talle):
        """Reincorpora un par (pedido eliminado/devolución), ordenado."""
        talles = self.talles_lista
        if talle not in talles:
            talles.append(talle)
            talles.sort(key=lambda t: (len(t), t))  # orden numérico para '38' < '40'
        self.talles = ", ".join(talles)


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


class Order(db.Model):
    """Pedido de la tienda pública. Al confirmarse descuenta stock registrando
    movimientos de venta (nota con el número de pedido): la venta online entra
    por el mismo circuito auditable que cualquier salida de depósito."""

    # "order" es palabra reservada en SQL; usamos un nombre de tabla explícito.
    __tablename__ = "pedido"

    ESTADOS = ("pendiente", "confirmado", "entregado", "cancelado")

    id = db.Column(db.Integer, primary_key=True)
    cliente = db.Column(db.String(80), nullable=False)
    telefono = db.Column(db.String(40), nullable=False)  # WhatsApp del cliente
    nota = db.Column(db.String(200))
    estado = db.Column(db.String(20), nullable=False, default="pendiente")
    creado_en = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    items = db.relationship(
        "OrderItem", backref="pedido", lazy=True, cascade="all, delete-orphan"
    )

    @property
    def total(self):
        return sum(item.cantidad * item.precio_unitario for item in self.items)


class OrderItem(db.Model):
    """Renglón de un pedido. Guarda una FOTO del producto al momento de comprar
    (nombre, sku, precio): si el producto cambia de precio o se elimina, el
    pedido conserva su historia intacta (por eso product_id puede quedar NULL)."""

    __tablename__ = "pedido_item"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("pedido.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=True)
    sku = db.Column(db.String(40), nullable=False)
    nombre = db.Column(db.String(120), nullable=False)
    talle = db.Column(db.String(10), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)

    # Si se borra el producto, el default del ORM deja product_id en NULL
    # y el renglón sobrevive gracias al snapshot.
    producto = db.relationship("Product", backref="renglones_pedido")
