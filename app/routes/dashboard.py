"""Dashboard: métricas del inventario en tiempo real.

Concepto clave: las agregaciones (contar, sumar) se hacen EN LA BASE con
func.count/func.sum, no trayendo todos los registros a Python para sumarlos
en un loop. Con 100 productos da igual; con 100.000, es la diferencia entre
milisegundos y colgar la app.
"""
from datetime import datetime, timezone

from flask import Blueprint, render_template
from flask_login import login_required
from sqlalchemy import func

from app import db
from app.models import Movement, Product

bp = Blueprint("dashboard", __name__)


@bp.route("/")
@login_required
def index():
    total_productos = db.session.query(func.count(Product.id)).scalar()

    # SUM(stock * precio) directo en SQL; coalesce evita None si no hay filas
    valor_inventario = db.session.query(
        func.coalesce(func.sum(Product.stock * Product.precio), 0)
    ).scalar()

    # Productos en alerta, los más críticos primero (más lejos de su mínimo)
    en_alerta = (
        Product.query.filter(Product.stock <= Product.stock_minimo)
        .order_by(Product.stock - Product.stock_minimo)
        .all()
    )

    # Movimientos de hoy (guardamos fechas en UTC)
    inicio_dia = datetime.combine(
        datetime.now(timezone.utc).date(), datetime.min.time()
    )
    movs_hoy = Movement.query.filter(Movement.fecha >= inicio_dia).count()

    ultimos = Movement.query.order_by(Movement.fecha.desc()).limit(8).all()

    return render_template(
        "dashboard.html",
        total_productos=total_productos,
        valor_inventario=valor_inventario,
        en_alerta=en_alerta,
        movs_hoy=movs_hoy,
        ultimos=ultimos,
    )
