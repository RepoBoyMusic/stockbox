"""Movimientos de stock: registrar entradas/salidas y ver el historial.

Regla de oro del diseño: el stock del producto y el movimiento se guardan
en UNA sola transacción (un solo commit). O pasan las dos cosas, o ninguna:
nunca puede quedar el stock cambiado sin su movimiento, ni al revés.
"""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.models import Movement, Product

bp = Blueprint("movements", __name__, url_prefix="/movimientos")


@bp.route("/")
@login_required
def index():
    # /movimientos?producto=3 filtra el historial de un producto puntual
    product_id = request.args.get("producto", type=int)

    query = Movement.query
    if product_id:
        query = query.filter_by(product_id=product_id)

    movimientos = query.order_by(Movement.fecha.desc()).limit(100).all()
    producto_sel = db.session.get(Product, product_id) if product_id else None
    return render_template(
        "movements/list.html", movimientos=movimientos, producto_sel=producto_sel
    )


@bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def crear():
    productos = Product.query.order_by(Product.nombre).all()

    if request.method == "POST":
        errores = []
        producto = db.session.get(Product, request.form.get("product_id", type=int) or 0)
        tipo = request.form.get("tipo", "")
        motivo = request.form.get("motivo", "")
        cantidad = request.form.get("cantidad", type=int)
        nota = request.form.get("nota", "").strip()

        if producto is None:
            errores.append("Elegí un producto.")
        # Validamos contra las listas del modelo: aunque el HTML sea un select,
        # el backend no confía en lo que llega del cliente.
        if tipo not in Movement.TIPOS:
            errores.append("Tipo de movimiento inválido.")
        if motivo not in Movement.MOTIVOS:
            errores.append("Motivo inválido.")
        if not cantidad or cantidad <= 0:
            errores.append("La cantidad debe ser un entero mayor a 0.")

        # La regla de negocio estrella: el stock nunca queda negativo
        if not errores and tipo == "salida" and cantidad > producto.stock:
            errores.append(
                f"Stock insuficiente: hay {producto.stock} unidades de '{producto.nombre}'."
            )

        if errores:
            for e in errores:
                flash(e, "error")
        else:
            producto.stock += cantidad if tipo == "entrada" else -cantidad
            db.session.add(
                Movement(
                    product_id=producto.id,
                    tipo=tipo,
                    motivo=motivo,
                    cantidad=cantidad,
                    nota=nota or None,
                )
            )
            db.session.commit()  # movimiento + stock nuevo: transacción atómica
            signo = "+" if tipo == "entrada" else "−"
            flash(
                f"{tipo.capitalize()} registrada: {signo}{cantidad} de '{producto.nombre}' "
                f"(stock actual: {producto.stock}).",
                "ok",
            )
            return redirect(url_for("movements.index"))

    # ?producto=3 permite llegar desde el listado con el producto preseleccionado
    producto_pre = request.args.get("producto", type=int)
    return render_template(
        "movements/form.html",
        productos=productos,
        producto_pre=producto_pre,
        motivos=Movement.MOTIVOS,
    )
