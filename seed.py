"""Carga datos de demostración: usuario demo, productos de kiosco y
dos semanas de movimientos simulados.

Uso:  python seed.py

- Si la base ya tiene productos, no hace nada (evita duplicar).
- random.seed fijo: la demo es reproducible, siempre genera lo mismo.
"""
import random
from datetime import datetime, timedelta, timezone

from app import create_app, db
from app.models import Movement, Product, User

random.seed(42)

#         SKU          Nombre                       Categoría    Precio  Stock  Mín  Ubicación
PRODUCTOS = [
    ("COCA-500", "Coca Cola 500ml",           "Bebidas",   1800, 24, 6,  "Pasillo 1 · Estante A"),
    ("AGUA-15",  "Agua Villa del Sur 1.5L",   "Bebidas",   1200, 30, 8,  "Pasillo 1 · Estante B"),
    ("CERV-473", "Cerveza Quilmes 473ml",     "Bebidas",   2200, 36, 12, "Pasillo 1 · Heladera"),
    ("ALFA-BON", "Alfajor Bon o Bon",         "Golosinas",  900, 48, 12, "Mostrador · Exhibidor"),
    ("CHOC-MIL", "Chocolate Milka 55g",       "Golosinas", 2500, 20, 5,  "Mostrador · Exhibidor"),
    ("CHIC-BEL", "Chicles Beldent Menta",     "Golosinas",  700, 60, 15, "Mostrador · Caja"),
    ("PAPA-LAY", "Papas Lays Clásicas 85g",   "Snacks",    2100, 25, 6,  "Pasillo 2 · Estante A"),
    ("MANI-100", "Maní Pelado 100g",          "Snacks",    1000, 15, 4,  "Pasillo 2 · Estante A"),
    ("YERB-PLA", "Yerba Playadito 500g",      "Almacén",   3800, 18, 5,  "Pasillo 3 · Estante A"),
    ("AZUC-LED", "Azúcar Ledesma 1kg",        "Almacén",   1600, 22, 6,  "Pasillo 3 · Estante B"),
    ("LAVA-AYU", "Lavandina Ayudín 1L",       "Limpieza",  1400, 12, 3,  "Pasillo 4 · Estante A"),
    ("PAPH-X4",  "Papel Higiénico x4",        "Limpieza",  2900, 16, 4,  "Pasillo 4 · Estante B"),
]


def sembrar():
    if Product.query.count():
        print("La base ya tiene productos: seed omitido (no se duplica nada).")
        return

    # Usuario demo para que cualquiera pueda probar la app
    if not User.query.filter_by(username="demo").first():
        demo = User(username="demo")
        demo.set_password("demo1234")
        db.session.add(demo)

    ahora = datetime.now(timezone.utc)

    for sku, nombre, categoria, precio, stock_inicial, minimo, ubicacion in PRODUCTOS:
        producto = Product(
            sku=sku, nombre=nombre, categoria=categoria, precio=precio,
            stock=0, stock_minimo=minimo, ubicacion=ubicacion,
        )
        db.session.add(producto)
        db.session.flush()  # necesitamos el id para los movimientos

        stock = stock_inicial
        movimientos = [
            Movement(
                product_id=producto.id, tipo="entrada", motivo="ajuste",
                cantidad=stock_inicial, nota="Stock inicial",
                fecha=ahora - timedelta(days=14),
            )
        ]

        # Simulamos ~2 semanas de actividad: ventas y reposiciones
        for dias_atras in range(13, 0, -1):
            if random.random() < 0.45:
                continue  # día sin movimientos para este producto
            fecha = ahora - timedelta(days=dias_atras, hours=random.randint(0, 10))
            if random.random() < 0.65 and stock > 2:
                cantidad = random.randint(1, max(1, stock // 3))
                stock -= cantidad
                movimientos.append(Movement(
                    product_id=producto.id, tipo="salida", motivo="venta",
                    cantidad=cantidad, fecha=fecha,
                ))
            else:
                cantidad = random.randint(5, 20)
                stock += cantidad
                movimientos.append(Movement(
                    product_id=producto.id, tipo="entrada", motivo="compra",
                    cantidad=cantidad, nota="Reposición proveedor", fecha=fecha,
                ))

        producto.stock = stock  # el stock final coincide con el historial
        db.session.add_all(movimientos)

    db.session.commit()
    print(f"Seed OK: {len(PRODUCTOS)} productos, usuario demo/demo1234.")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        sembrar()
