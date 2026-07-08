"""Carga datos de demostración: usuario demo, catálogo de zapatillas
importadas separado por calidad (AAA → 1:1 → PK → OG → G5, de menor a
mayor gama), con curva de talles por modelo y dos semanas de
movimientos simulados.

Los stocks se generan con un tope de 15 pares por modelo: es un
criterio de armado de ESTE catálogo demo, no un límite de la app.

Uso:  python seed.py

- Si la base ya tiene productos, no hace nada (evita duplicar).
- random.seed fijo: la demo es reproducible, siempre genera lo mismo.
"""
import random
from datetime import datetime, timedelta, timezone

from app import create_app, db
from app.models import Movement, Product, User

random.seed(42)

#         SKU               Nombre                            Cat.   Precio   Stock  Mín  Ubicación                Talles
PRODUCTOS = [
    # ── G5 · gama top, casi indistinguibles del original ──────────────────
    ("JOR-4MB-G5",    "Jordan 4 Military Black",        "G5",  149999,  6, 2, "Vidriera · Exhibidor", "40–45"),
    ("JOR-1CHI-G5",   "Jordan 1 High Chicago",          "G5",  139999,  5, 2, "Vidriera · Exhibidor", "40–44"),
    ("YZY-350-G5",    "Yeezy Boost 350 V2 Onyx",        "G5",  129999,  8, 3, "Salón · Pared A",      "38–45"),
    ("NKE-TN-G5",     "Nike Air Max Plus TN",           "G5",  144999, 10, 4, "Vidriera · Exhibidor", "39–45"),
    ("NKE-AM95-G5",   "Nike Air Max 95 Big Bubble",     "G5",  139999,  7, 2, "Salón · Pared A",      "40–45"),
    ("NKE-DUNK-G5",   "Nike Dunk Low Panda",            "G5",  119999, 12, 4, "Salón · Pared A",      "36–45"),
    ("NKE-AF1-G5",    "Nike Air Force 1 '07",           "G5",   99999, 15, 5, "Salón · Pared B",      "35–46"),
    ("NKE-V2K-G5",    "Nike V2K Run",                   "G5",  119999,  9, 3, "Salón · Pared B",      "36–44"),
    ("ADI-SAMBA-G5",  "Adidas Samba OG",                "G5",  109999, 14, 5, "Salón · Pared B",      "35–45"),
    ("PUM-SPEED-G5",  "Puma Speedcat OG",               "G5",   99999, 11, 4, "Vidriera · Exhibidor", "35–44"),
    ("NB-9060-G5",    "New Balance 9060",               "G5",  134999,  6, 2, "Depósito · Rack A1",   "38–45"),
    ("NB-2002R-G5",   "New Balance 2002R",              "G5",  129999,  7, 3, "Depósito · Rack A1",   "38–45"),
    ("ASC-2160-G5",   "Asics GT-2160",                  "G5",  114999,  9, 3, "Depósito · Rack A2",   "39–45"),
    ("SAL-XT6-G5",    "Salomon XT-6",                   "G5",  144999,  5, 2, "Depósito · Rack A2",   "39–46"),
    # ── OG · gama alta ─────────────────────────────────────────────────────
    ("NKE-VOM5-OG",   "Nike Zoom Vomero 5",             "OG",  104999,  8, 3, "Depósito · Rack B1",   "38–45"),
    ("NKE-P6K-OG",    "Nike P-6000",                    "OG",   94999, 10, 3, "Depósito · Rack B1",   "36–44"),
    ("NKE-AM97-OG",   "Nike Air Max 97",                "OG",  107999,  7, 2, "Depósito · Rack B1",   "38–45"),
    ("NKE-AMDN-OG",   "Nike Air Max DN",                "OG",  109999,  6, 2, "Depósito · Rack B2",   "39–45"),
    ("JOR-1LOW-OG",   "Jordan 1 Low Bred Toe",          "OG",   92999, 11, 4, "Depósito · Rack B2",   "36–45"),
    ("ADI-GAZ-OG",    "Adidas Gazelle",                 "OG",   89999, 13, 4, "Depósito · Rack B2",   "35–44"),
    ("ADI-CAMP-OG",   "Adidas Campus 00s",              "OG",   92999, 12, 4, "Depósito · Rack B3",   "35–45"),
    ("ADI-SPEZ-OG",   "Adidas Handball Spezial",        "OG",   94999,  8, 3, "Depósito · Rack B3",   "36–44"),
    ("YZY-SLIDE-OG",  "Yeezy Slide Onyx",               "OG",   84999, 14, 5, "Depósito · Rack B3",   "36–46"),
    ("NB-550-OG",     "New Balance 550",                "OG",   99999,  9, 3, "Depósito · Rack B4",   "37–45"),
    ("ASC-1130-OG",   "Asics Gel-1130",                 "OG",   97999, 10, 3, "Depósito · Rack B4",   "38–45"),
    ("ASC-KAY14-OG",  "Asics Gel-Kayano 14",            "OG",  104999,  6, 2, "Depósito · Rack B4",   "39–45"),
    # ── PK · gama media-alta ───────────────────────────────────────────────
    ("NKE-AM90-PK",   "Nike Air Max 90",                "PK",   84999, 12, 4, "Depósito · Rack C1",   "38–45"),
    ("NKE-PEG41-PK",  "Nike Pegasus 41",                "PK",   82999, 10, 3, "Depósito · Rack C1",   "39–46"),
    ("NKE-SHOX-PK",   "Nike Shox TL",                   "PK",   89999,  7, 2, "Depósito · Rack C1",   "39–44"),
    ("NKE-CORT-PK",   "Nike Cortez",                    "PK",   74999, 11, 3, "Depósito · Rack C2",   "35–44"),
    ("JOR-3WC-PK",    "Jordan 3 White Cement",          "PK",   88999,  6, 2, "Depósito · Rack C2",   "40–45"),
    ("ADI-FORUM-PK",  "Adidas Forum Low",               "PK",   79999, 13, 4, "Depósito · Rack C2",   "36–45"),
    ("ADI-SUPER-PK",  "Adidas Superstar",               "PK",   74999, 15, 5, "Depósito · Rack C3",   "35–46"),
    ("ADI-EVOSL-PK",  "Adidas Adizero Evo SL",          "PK",   87999,  8, 3, "Depósito · Rack C3",   "39–45"),
    ("PUM-PAL-PK",    "Puma Palermo",                   "PK",   76999, 12, 4, "Depósito · Rack C3",   "35–44"),
    ("PUM-SUEDE-PK",  "Puma Suede XL",                  "PK",   72999, 10, 3, "Depósito · Rack C4",   "36–44"),
    ("NB-530-PK",     "New Balance 530",                "PK",   82999, 14, 5, "Depósito · Rack C4",   "36–45"),
    ("NB-1080-PK",    "New Balance 1080v15",            "PK",   89999,  5, 2, "Depósito · Rack C4",   "39–46"),
    ("ASC-NYC-PK",    "Asics Gel-NYC",                  "PK",   86999,  9, 3, "Depósito · Rack D1",   "38–44"),
    ("HOK-CLIF-PK",   "Hoka Clifton 9",                 "PK",   88999,  7, 2, "Depósito · Rack D1",   "38–46"),
    ("CON-C70-PK",    "Converse Chuck 70",              "PK",   71999, 11, 4, "Depósito · Rack D1",   "36–44"),
    # ── 1:1 · gama media ───────────────────────────────────────────────────
    ("NKE-AMSC-11",   "Nike Air Max SC",                "1:1",  61999, 13, 4, "Depósito · Rack D2",   "35–45"),
    ("NKE-REV7-11",   "Nike Revolution 7",              "1:1",  57999, 15, 5, "Depósito · Rack D2",   "36–46"),
    ("NKE-CVL-11",    "Nike Court Vision Low",          "1:1",  59999, 14, 5, "Depósito · Rack D2",   "36–45"),
    ("ADI-UBL-11",    "Adidas Ultraboost Light",        "1:1",  69999,  8, 3, "Depósito · Rack D3",   "38–45"),
    ("PUM-CAVEN-11",  "Puma Caven 2.0",                 "1:1",  55999, 12, 4, "Depósito · Rack D3",   "36–44"),
    ("NB-574-11",     "New Balance 574",                "1:1",  64999, 13, 4, "Depósito · Rack D3",   "35–45"),
    ("VAN-OLD-11",    "Vans Old Skool",                 "1:1",  59999, 15, 5, "Depósito · Rack D4",   "34–45"),
    ("VAN-KNU-11",    "Vans Knu Skool",                 "1:1",  64999, 10, 3, "Depósito · Rack D4",   "35–44"),
    ("CON-CHUCK-11",  "Converse Chuck Taylor All Star", "1:1",  54999, 15, 5, "Depósito · Rack D4",   "34–46"),
    ("SAL-SPEED-11",  "Salomon Speedcross 6",           "1:1",  69999,  6, 2, "Depósito · Rack E1",   "39–46"),
    ("ON-CLOUDM-11",  "On Cloudmonster",                "1:1",  69999,  7, 2, "Depósito · Rack E1",   "39–45"),
    # ── AAA · gama de entrada ──────────────────────────────────────────────
    ("NKE-AM270-AAA", "Nike Air Max 270",               "AAA",  52999, 14, 5, "Depósito · Rack E2",   "36–45"),
    ("NKE-DOWN-AAA",  "Nike Downshifter 13",            "AAA",  44999, 15, 5, "Depósito · Rack E2",   "35–46"),
    ("ADI-DURA-AAA",  "Adidas Duramo SL",               "AAA",  46999, 13, 4, "Depósito · Rack E2",   "36–46"),
    ("ADI-RUNF-AAA",  "Adidas Runfalcon 5",             "AAA",  44999, 15, 5, "Depósito · Rack E3",   "35–46"),
    ("PUM-RIFT-AAA",  "Puma Softride Rift",             "AAA",  49999, 12, 4, "Depósito · Rack E3",   "35–44"),
    ("REE-CLUB-AAA",  "Reebok Club C 85",               "AAA",  52999, 11, 4, "Depósito · Rack E3",   "36–45"),
    ("FIL-DISR-AAA",  "Fila Disruptor II",              "AAA",  47999, 10, 3, "Depósito · Rack E4",   "35–42"),
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

    for sku, nombre, categoria, precio, stock_inicial, minimo, ubicacion, talles in PRODUCTOS:
        producto = Product(
            sku=sku, nombre=nombre, categoria=categoria, precio=precio,
            stock=0, stock_minimo=minimo, ubicacion=ubicacion, talles=talles,
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
                espacio = 15 - stock  # tope de armado del catálogo demo: 15 pares por modelo
                if espacio < 1:
                    continue
                cantidad = random.randint(1, min(8, espacio))
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
