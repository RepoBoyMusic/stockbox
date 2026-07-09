"""Tienda pública (sin login): catálogo, carrito y checkout.

Punto clave del diseño: la tienda NO tiene su propia base ni su propia
lista de productos. Lee la MISMA tabla `Product` que StockBox. Por eso no
hay nada que "sincronizar": si cambiás un precio o un stock en el panel,
la tienda lo refleja al instante, y una compra online descuenta stock
registrando un movimiento de venta, igual que cualquier salida de depósito.

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

CARRITO = "carrito"  # clave del carrito en la sesión


def _expandir_talles(rango):
    """'35–45' -> ['35','36',...,'45']. Tolera guion normal o en-dash y
    valores sueltos. Si no se puede parsear, devuelve el texto tal cual."""
    if not rango:
        return []
    texto = rango.replace("–", "-").replace("—", "-")
    if "-" in texto:
        try:
            desde, hasta = (int(x.strip()) for x in texto.split("-", 1))
            if desde <= hasta:
                return [str(n) for n in range(desde, hasta + 1)]
        except ValueError:
            pass
    return [t.strip() for t in texto.split(",") if t.strip()]


def _carrito():
    return session.get(CARRITO, {})


def _guardar_carrito(carrito):
    session[CARRITO] = carrito
    session.modified = True


def _lineas_carrito(carrito):
    """Reconstruye las líneas del carrito desde la base (precio y datos
    siempre frescos). Devuelve (lineas, total). Ignora items cuyo producto
    ya no exista."""
    lineas, total = [], Decimal("0")
    for clave, cantidad in carrito.items():
        pid, talle = clave.split(":", 1)
        producto = db.session.get(Product, int(pid))
        if not producto:
            continue
        subtotal = producto.precio * cantidad
        total += subtotal
        lineas.append({
            "clave": clave, "producto": producto, "talle": talle,
            "cantidad": cantidad, "subtotal": subtotal,
        })
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
    carrito = _carrito()
    return render_template(
        "store/index.html",
        productos=productos, categorias=categorias, q=q, categoria_sel=categoria,
        items_carrito=sum(carrito.values()),
        talles_por_producto={p.id: _expandir_talles(p.talles) for p in productos},
    )


@bp.route("/agregar/<int:product_id>", methods=["POST"])
def agregar(product_id):
    producto = db.get_or_404(Product, product_id)
    talle = request.form.get("talle", "").strip()
    if not talle:
        flash("Elegí un talle antes de agregar al carrito.", "error")
        return redirect(url_for("store.index"))

    carrito = _carrito()
    clave = f"{product_id}:{talle}"
    en_carrito = carrito.get(clave, 0)
    # No dejamos reservar más de lo que hay en stock
    if en_carrito + 1 > producto.stock:
        flash(f"No hay más stock de {producto.nombre} (talle {talle}).", "error")
        return redirect(url_for("store.index"))

    carrito[clave] = en_carrito + 1
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

        # Revalidamos stock CONTRA LA BASE en el momento de confirmar: entre
        # que armó el carrito y confirmó, el stock pudo cambiar.
        for linea in lineas:
            if linea["cantidad"] > linea["producto"].stock:
                errores.append(
                    f"Se quedó sin stock suficiente de {linea['producto'].nombre} "
                    f"(quedan {linea['producto'].stock})."
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
            producto = linea["producto"]
            cantidad = linea["cantidad"]
            db.session.add(OrderItem(
                order_id=pedido.id, product_id=producto.id, sku=producto.sku,
                nombre=producto.nombre, talle=linea["talle"], cantidad=cantidad,
                precio_unitario=producto.precio,
            ))
            db.session.add(Movement(
                product_id=producto.id, tipo="salida", motivo="venta",
                cantidad=cantidad,
                nota=f"Pedido #{pedido.id} · talle {linea['talle']} · tienda",
            ))
            producto.stock -= cantidad

        db.session.commit()
        _guardar_carrito({})  # vaciamos el carrito
        return redirect(url_for("store.gracias", order_id=pedido.id))

    return render_template("store/checkout.html", lineas=lineas, total=total, valores={})


@bp.route("/gracias/<int:order_id>")
def gracias(order_id):
    pedido = db.get_or_404(Order, order_id)
    return render_template("store/gracias.html", pedido=pedido)
