"""Pedidos de la tienda, vistos desde el panel (requiere login).

Solo lectura: los pedidos se crean en la tienda pública. Acá el negocio
los consulta, ve el detalle y el contacto del cliente para coordinar la
entrega por WhatsApp.
"""
from flask import Blueprint, render_template
from flask_login import login_required

from app import db
from app.models import Order

bp = Blueprint("orders", __name__, url_prefix="/pedidos")


@bp.route("/")
@login_required
def index():
    pedidos = Order.query.order_by(Order.creado_en.desc()).all()
    return render_template("orders/list.html", pedidos=pedidos)


@bp.route("/<int:order_id>")
@login_required
def detalle(order_id):
    pedido = db.get_or_404(Order, order_id)
    return render_template("orders/detail.html", pedido=pedido)
