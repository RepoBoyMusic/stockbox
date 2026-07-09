"""Pedidos de la tienda, vistos desde el panel (requiere login).

Los pedidos se crean en la tienda pública. Acá el negocio los consulta,
ve el detalle y el contacto del cliente para coordinar la entrega, y
puede eliminarlos (devolviendo el stock).
"""
from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import login_required

from app import db
from app.models import Movement, Order

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


@bp.route("/<int:order_id>/eliminar", methods=["POST"])
@login_required
def eliminar(order_id):
    """Elimina un pedido y DEVUELVE el stock al inventario.

    Es POST (no GET): borrar es una acción destructiva y no debe dispararse
    desde un link. Por cada renglón cuyo producto siga existiendo, registramos
    un movimiento de devolución —queda el rastro auditable— y reponemos el
    stock. Recién ahí borramos el pedido; el cascade elimina sus renglones y,
    con ellos, los datos personales del cliente (nombre y teléfono)."""
    pedido = db.get_or_404(Order, order_id)

    if pedido.estado != "cancelado":  # un pedido cancelado ya devolvió su stock
        for item in pedido.items:
            if item.producto is not None:
                db.session.add(Movement(
                    product_id=item.producto.id, tipo="entrada", motivo="devolucion",
                    cantidad=item.cantidad,
                    nota=f"Devolución por pedido #{pedido.id} eliminado",
                ))
                item.producto.stock += item.cantidad
                item.producto.devolver_talle(item.talle)  # el par vuelve a estar disponible

    db.session.delete(pedido)  # cascade borra los renglones (y los datos del cliente)
    db.session.commit()
    flash(f"Pedido #{order_id} eliminado y stock devuelto.", "ok")
    return redirect(url_for("orders.index"))
