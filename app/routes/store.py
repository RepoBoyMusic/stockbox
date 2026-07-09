"""Tienda pública (sin login): catálogo, carrito y checkout.

Punto clave del diseño: la tienda NO tiene su propia base ni su propia
lista de productos. Lee la MISMA tabla `Product` que StockBox. Por eso no
hay nada que "sincronizar": si cambiás un precio o un stock en el panel,
la tienda lo refleja al instante, y una compra online descuenta stock
registrando un movimiento de venta, igual que cualquier salida de depósito.

Modelo de venta: pares únicos. Cada talle listado en un producto es UN par
físico. Comprar el talle 42 saca ese par de la lista y descuenta 1 de stock;
el mismo par no puede estar dos veces en un carrito ni venderse dos veces.

El carrito vive en la sesión del visitante (cookie firmada), no en la base:
un carrito a medio llenar no ensucia los datos del negocio.
"""
from decimal import Decimal

from flask import (
    Blueprint, flash, redirect, render_template, request, session, url_for,
)

from app import db
from app.models import Movement, Order, OrderItem, Product

bp = Blueprint("store", __name__, url_prefix="/tienda")

CARRITO = "carrito"  # clave del carrito en la sesión: {"product_id:talle": 1}


def _carrito():
    return session.get(CARRITO, {})


def _guardar_carrito(carrito):
    session[CARRITO] = carrito
    session.modified = True


def _lineas_carrito(carrito):
    """Reconstruye las líneas del carrito desde la base (precio y datos
    siempre frescos). Cada línea es un par único (cantidad 1). Ignora
    items cuyo producto ya no exista."""
    lineas, total = [], Decimal("0")
    for clave in carrito:
        pid, talle = clave.split(":", 1)
        producto = db.session.get(Product, int(pid))
        if not producto:
            continue
        total += producto.precio
        lineas.append({"clave": clave, "producto": producto, "talle": talle})
    return lineas, total


@bp.route("/")
def index():
    q = request.args.get("q", "").strip()
    categoria = request.args.get("categoria", "").strip()

    query = Product.query.filter(Product.stock > 0)  # solo lo que hay para vender
    if q:
        like = f"%{q}%"
        query = query.filter(db.or_(Product.nombre.ilike(like), Product.sku.ilike(like)))
    if categoria:
        query = query.filter_by(categoria=categoria)

    productos = query.order_by(Product.nombre).all()
    categorias = [
        c[0] for c in db.session.query(Product.categoria).distinct().order_by(Product.categoria)
    ]
    return render_template(
        "store/index.html",
        productos=productos, categorias=categorias, q=q, categoria_sel=categoria,
    )


@bp.route("/agregar/<int:product_id>", methods=["POST"])
def agregar(product_id):
    producto = db.get_or_404(Product, product_id)
    talle = request.form.get("talle", "").strip()
    if not talle:
        flash("Elegí un talle antes de agregar al carrito.", "error")
        return redirect(url_for("store.index"))
    # El talle tiene que ser un par que exista HOY (el form podría venir viejo)
    if talle not in producto.talles_lista or producto.stock < 1:
        flash(f"El par de {producto.nombre} talle {talle} ya no está disponible.", "error")
        return redirect(url_for("store.index"))

    carrito = _carrito()
    clave = f"{product_id}:{talle}"
    if clave in carrito:
        flash(f"Ese par ({producto.nombre} talle {talle}) ya está en tu carrito — es único.", "error")
        return redirect(url_for("store.index"))

    carrito[clave] = 1  # un par por talle: la cantidad es siempre 1
    _guardar_carrito(carrito)
    flash(f"{producto.nombre} (talle {talle}) agregado al carrito.", "ok")
    return redirect(url_for("store.index"))


@bp.route("/carrito")
def carrito():
    lineas, total = _lineas_carrito(_carrito())
    return render_template("store/carrito.html", lineas=lineas, total=total)


@bp.route("/carrito/quitar/<path:clave>", methods=["POST"])
def quitar(clave):
    carrito = _carrito()
    if clave in carrito:
        del carrito[clave]
        _guardar_carrito(carrito)
    return redirect(url_for("store.carrito"))


@bp.route("/checkout", methods=["GET", "POST"])
def checkout():
    lineas, total = _lineas_carrito(_carrito())
    if not lineas:
        flash("Tu carrito está vacío.", "error")
        return redirect(url_for("store.index"))

    if request.method == "POST":
        cliente = request.form.get("cliente", "").strip()
        telefono = request.form.get("telefono", "").strip()
        nota = request.form.get("nota", "").strip()
        errores = []
        if not cliente:
            errores.append("Necesitamos tu nombre.")
        if not telefono:
            errores.append("Necesitamos un teléfono de contacto.")

        # Revalidamos CONTRA LA BASE al confirmar: entre que armó el carrito
        # y confirmó, ese par único pudo habérselo llevado otro cliente.
        for linea in lineas:
            producto, talle = linea["producto"], linea["talle"]
            if talle not in producto.talles_lista or producto.stock < 1:
                errores.append(
                    f"El par {producto.nombre} talle {talle} se vendió mientras comprabas."
                )

        if errores:
            for e in errores:
                flash(e, "error")
            return render_template(
                "store/checkout.html", lineas=lineas, total=total,
                valores={"cliente": cliente, "telefono": telefono, "nota": nota},
            )

        # Todo en una transacción: el pedido, sus renglones, los movimientos
        # de venta y el descuento de stock se confirman juntos o no se confirma
        # nada. Así nunca queda un pedido sin descontar stock, ni al revés.
        pedido = Order(cliente=cliente, telefono=telefono, nota=nota, estado="confirmado")
        db.session.add(pedido)
        db.session.flush()  # necesitamos el id del pedido para la nota del movimiento

        for linea in lineas:
            producto, talle = linea["producto"], linea["talle"]
            db.session.add(OrderItem(
                order_id=pedido.id, product_id=producto.id, sku=producto.sku,
                nombre=producto.nombre, talle=talle, cantidad=1,
                precio_unitario=producto.precio,
            ))
            db.session.add(Movement(
                product_id=producto.id, tipo="salida", motivo="venta",
                cantidad=1, nota=f"Pedido #{pedido.id} · talle {talle} · tienda",
            ))
            producto.quitar_talle(talle)  # ese par único ya no está disponible
            producto.stock -= 1

        db.session.commit()
        _guardar_carrito({})  # vaciamos el carrito
        return redirect(url_for("store.gracias", order_id=pedido.id))

    return render_template("store/checkout.html", lineas=lineas, total=total, valores={})


@bp.route("/gracias/<int:order_id>")
def gracias(order_id):
    pedido = db.get_or_404(Order, order_id)
    return render_template("store/gracias.html", pedido=pedido)
