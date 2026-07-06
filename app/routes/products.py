"""CRUD de productos: listar (con búsqueda/filtro), crear, editar, eliminar.

Patrón clave acá: PRG (Post → Redirect → Get). Después de un POST exitoso
NUNCA devolvemos HTML directo: redirigimos. Así, si el usuario refresca la
página, no se reenvía el formulario duplicando datos.
"""
from decimal import Decimal, InvalidOperation

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.models import Movement, Product

bp = Blueprint("products", __name__, url_prefix="/productos")


def _leer_formulario():
    """Extrae y valida los campos comunes del form. Devuelve (datos, errores).

    Validamos SIEMPRE en el servidor: el `required` del HTML es solo UX,
    cualquiera puede saltearlo (curl, devtools). La última palabra la tiene
    el backend.
    """
    datos = {
        "sku": request.form.get("sku", "").strip().upper(),
        "nombre": request.form.get("nombre", "").strip(),
        "categoria": request.form.get("categoria", "").strip() or "General",
        "ubicacion": request.form.get("ubicacion", "").strip(),
    }
    errores = []

    if not datos["sku"]:
        errores.append("El SKU es obligatorio.")
    if not datos["nombre"]:
        errores.append("El nombre es obligatorio.")

    try:
        datos["precio"] = Decimal(request.form.get("precio", "0") or "0")
        if datos["precio"] < 0:
            errores.append("El precio no puede ser negativo.")
    except InvalidOperation:
        errores.append("El precio debe ser un número.")
        datos["precio"] = Decimal("0")

    try:
        datos["stock_minimo"] = int(request.form.get("stock_minimo", "0") or "0")
        if datos["stock_minimo"] < 0:
            errores.append("El stock mínimo no puede ser negativo.")
    except ValueError:
        errores.append("El stock mínimo debe ser un número entero.")
        datos["stock_minimo"] = 0

    return datos, errores


@bp.route("/")
@login_required
def index():
    # Búsqueda y filtro vienen como query params: /productos?q=coca&categoria=Bebidas
    q = request.args.get("q", "").strip()
    categoria = request.args.get("categoria", "").strip()

    query = Product.query
    if q:
        like = f"%{q}%"
        query = query.filter(db.or_(Product.nombre.ilike(like), Product.sku.ilike(like)))
    if categoria:
        query = query.filter_by(categoria=categoria)

    productos = query.order_by(Product.nombre).all()
    categorias = [
        c[0]
        for c in db.session.query(Product.categoria).distinct().order_by(Product.categoria)
    ]
    return render_template(
        "products/list.html",
        productos=productos,
        categorias=categorias,
        q=q,
        categoria_sel=categoria,
    )


@bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def crear():
    if request.method == "POST":
        datos, errores = _leer_formulario()

        # El stock inicial solo existe al CREAR; después se mueve, no se edita
        try:
            stock_inicial = int(request.form.get("stock", "0") or "0")
            if stock_inicial < 0:
                errores.append("El stock inicial no puede ser negativo.")
        except ValueError:
            errores.append("El stock debe ser un número entero.")
            stock_inicial = 0

        if Product.query.filter_by(sku=datos["sku"]).first():
            errores.append(f"Ya existe un producto con SKU {datos['sku']}.")

        if errores:
            for e in errores:
                flash(e, "error")
            # Re-mostramos el form con lo que el usuario había escrito
            return render_template(
                "products/form.html", producto=None, valores={**datos, "stock": stock_inicial}
            )

        producto = Product(**datos, stock=stock_inicial)
        db.session.add(producto)
        if stock_inicial > 0:
            db.session.flush()  # fuerza el INSERT para que el producto tenga id
            db.session.add(
                Movement(
                    product_id=producto.id,
                    tipo="entrada",
                    motivo="ajuste",
                    cantidad=stock_inicial,
                    nota="Stock inicial",
                )
            )
        db.session.commit()
        flash(f"Producto '{producto.nombre}' creado.", "ok")
        return redirect(url_for("products.index"))

    return render_template("products/form.html", producto=None, valores={})


@bp.route("/<int:product_id>/editar", methods=["GET", "POST"])
@login_required
def editar(product_id):
    producto = db.get_or_404(Product, product_id)

    if request.method == "POST":
        datos, errores = _leer_formulario()

        # SKU único, pero permitiendo que el producto conserve el suyo
        existe = Product.query.filter(
            Product.sku == datos["sku"], Product.id != producto.id
        ).first()
        if existe:
            errores.append(f"Ya existe otro producto con SKU {datos['sku']}.")

        if errores:
            for e in errores:
                flash(e, "error")
            return render_template("products/form.html", producto=producto, valores=datos)

        for campo, valor in datos.items():
            setattr(producto, campo, valor)
        db.session.commit()
        flash(f"Producto '{producto.nombre}' actualizado.", "ok")
        return redirect(url_for("products.index"))

    valores = {
        "sku": producto.sku,
        "nombre": producto.nombre,
        "categoria": producto.categoria,
        "precio": producto.precio,
        "stock_minimo": producto.stock_minimo,
        "ubicacion": producto.ubicacion or "",
    }
    return render_template("products/form.html", producto=producto, valores=valores)


@bp.route("/<int:product_id>/eliminar", methods=["POST"])
@login_required
def eliminar(product_id):
    """Eliminar es POST, nunca GET: los links (GET) no deben tener efectos
    destructivos — un crawler o el prefetch del navegador podrían dispararlos."""
    producto = db.get_or_404(Product, product_id)
    db.session.delete(producto)  # cascade borra también sus movimientos
    db.session.commit()
    flash(f"Producto '{producto.nombre}' eliminado.", "ok")
    return redirect(url_for("products.index"))
