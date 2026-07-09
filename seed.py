"""Carga datos de demostración: usuario demo y un catálogo de zapatillas
ORIGINALES a precio de retail argentino, como los maneja un revendedor
chico: 1 a 3 pares por modelo, donde cada talle listado es un par físico
real (un par por talle). Con historial de movimientos coherente.

Uso:  python seed.py

- Si la base ya tiene productos, no hace nada (evita duplicar).
- random.seed fijo: la demo es reproducible, siempre genera lo mismo.
"""
import random
from datetime import datetime, timedelta, timezone

from app import create_app, db
from app.models import Movement, Product, User

random.seed(42)

#         SKU          Nombre                            Categoría  Precio    Ubicación               Talles (un par por talle)
PRODUCTOS = [
    # ── Básquet ────────────────────────────────────────────────────────────
    ("JOR-4MB",    "Jordan 4 Military Black",        "Básquet", 479999, "Vidriera · Exhibidor", "42, 43"),
    ("JOR-1CHI",   "Jordan 1 High Chicago",          "Básquet", 429999, "Vidriera · Exhibidor", "41, 44"),
    ("JOR-1LOW",   "Jordan 1 Low Bred Toe",          "Básquet", 259999, "Salón · Pared A",      "40, 42, 43"),
    ("JOR-3WC",    "Jordan 3 White Cement",          "Básquet", 399999, "Vidriera · Exhibidor", "42"),
    # ── Retro ──────────────────────────────────────────────────────────────
    ("NKE-AM95",   "Nike Air Max 95 Big Bubble",     "Retro",   419999, "Vidriera · Exhibidor", "41, 43"),
    ("NKE-AM97",   "Nike Air Max 97",                "Retro",   359999, "Salón · Pared A",      "40, 42"),
    ("NKE-AM90",   "Nike Air Max 90",                "Retro",   289999, "Salón · Pared A",      "39, 41, 43"),
    ("NKE-TN",     "Nike Air Max Plus TN",           "Retro",   379999, "Vidriera · Exhibidor", "40, 41, 44"),
    ("NKE-AMDN",   "Nike Air Max DN",                "Retro",   349999, "Salón · Pared A",      "42, 43"),
    ("NKE-CORT",   "Nike Cortez",                    "Retro",   189999, "Depósito · Rack A1",   "38, 40"),
    ("NKE-V2K",    "Nike V2K Run",                   "Retro",   269999, "Salón · Pared B",      "37, 39, 41"),
    ("NKE-VOM5",   "Nike Zoom Vomero 5",             "Retro",   319999, "Salón · Pared B",      "40, 42"),
    ("NKE-P6K",    "Nike P-6000",                    "Retro",   239999, "Depósito · Rack A1",   "38, 41, 43"),
    ("NKE-SHOX",   "Nike Shox TL",                   "Retro",   329999, "Depósito · Rack A2",   "41, 42"),
    ("NB-530",     "New Balance 530",                "Retro",   239999, "Salón · Pared B",      "37, 39, 42"),
    ("NB-550",     "New Balance 550",                "Retro",   269999, "Depósito · Rack A2",   "40, 43"),
    ("NB-574",     "New Balance 574",                "Retro",   199999, "Depósito · Rack B1",   "38, 41"),
    ("NB-9060",    "New Balance 9060",               "Retro",   339999, "Salón · Pared B",      "41, 42"),
    ("NB-2002R",   "New Balance 2002R",              "Retro",   319999, "Depósito · Rack B1",   "42, 44"),
    ("ASC-2160",   "Asics GT-2160",                  "Retro",   259999, "Depósito · Rack B2",   "39, 41, 43"),
    ("ASC-1130",   "Asics Gel-1130",                 "Retro",   249999, "Depósito · Rack B2",   "38, 40"),
    ("ASC-KAY14",  "Asics Gel-Kayano 14",            "Retro",   289999, "Depósito · Rack B2",   "41, 43"),
    ("ASC-NYC",    "Asics Gel-NYC",                  "Retro",   279999, "Depósito · Rack B3",   "40, 42"),
    # ── Urbanas ────────────────────────────────────────────────────────────
    ("NKE-AF1",    "Nike Air Force 1 '07",           "Urbanas", 249999, "Salón · Pared A",      "39, 41, 43"),
    ("NKE-DUNK",   "Nike Dunk Low Panda",            "Urbanas", 299999, "Vidriera · Exhibidor", "38, 40, 42"),
    ("NKE-CVL",    "Nike Court Vision Low",          "Urbanas", 139999, "Depósito · Rack B3",   "40, 42, 44"),
    ("NKE-AMSC",   "Nike Air Max SC",                "Urbanas", 159999, "Depósito · Rack B4",   "39, 41"),
    ("NKE-AM270",  "Nike Air Max 270",               "Urbanas", 259999, "Depósito · Rack B4",   "40, 43"),
    ("YZY-350",    "Yeezy Boost 350 V2 Onyx",        "Urbanas", 389999, "Vidriera · Exhibidor", "41, 42"),
    ("YZY-SLIDE",  "Yeezy Slide Onyx",               "Urbanas", 179999, "Salón · Pared A",      "42, 44"),
    ("ADI-SAMBA",  "Adidas Samba OG",                "Urbanas", 269999, "Salón · Pared B",      "37, 39, 42"),
    ("ADI-GAZ",    "Adidas Gazelle",                 "Urbanas", 239999, "Salón · Pared B",      "36, 38, 41"),
    ("ADI-CAMP",   "Adidas Campus 00s",              "Urbanas", 249999, "Salón · Pared B",      "38, 40"),
    ("ADI-SPEZ",   "Adidas Handball Spezial",        "Urbanas", 259999, "Depósito · Rack C1",   "40, 42"),
    ("ADI-FORUM",  "Adidas Forum Low",               "Urbanas", 219999, "Depósito · Rack C1",   "39, 42"),
    ("ADI-SUPER",  "Adidas Superstar",               "Urbanas", 189999, "Depósito · Rack C2",   "37, 40, 43"),
    ("PUM-SPEED",  "Puma Speedcat OG",               "Urbanas", 229999, "Vidriera · Exhibidor", "38, 40, 41"),
    ("PUM-PAL",    "Puma Palermo",                   "Urbanas", 179999, "Depósito · Rack C2",   "37, 39"),
    ("PUM-SUEDE",  "Puma Suede XL",                  "Urbanas", 169999, "Depósito · Rack C3",   "40, 42"),
    ("PUM-CAVEN",  "Puma Caven 2.0",                 "Urbanas", 119999, "Depósito · Rack C3",   "41, 43"),
    ("VAN-OLD",    "Vans Old Skool",                 "Urbanas", 159999, "Depósito · Rack C4",   "38, 40, 42"),
    ("VAN-KNU",    "Vans Knu Skool",                 "Urbanas", 179999, "Depósito · Rack C4",   "39, 41"),
    ("CON-CHUCK",  "Converse Chuck Taylor All Star", "Urbanas", 129999, "Depósito · Rack D1",   "36, 39, 42"),
    ("CON-C70",    "Converse Chuck 70",              "Urbanas", 189999, "Depósito · Rack D1",   "40, 43"),
    ("REE-CLUB",   "Reebok Club C 85",               "Urbanas", 169999, "Depósito · Rack D2",   "39, 42"),
    ("FIL-DISR",   "Fila Disruptor II",              "Urbanas", 149999, "Depósito · Rack D2",   "36, 38"),
    # ── Running ────────────────────────────────────────────────────────────
    ("NKE-PEG41",  "Nike Pegasus 41",                "Running", 299999, "Depósito · Rack D3",   "41, 43"),
    ("NKE-REV7",   "Nike Revolution 7",              "Running", 119999, "Depósito · Rack D3",   "40, 42, 44"),
    ("NKE-DOWN",   "Nike Downshifter 13",            "Running", 109999, "Depósito · Rack D4",   "39, 41"),
    ("NB-1080",    "New Balance 1080v15",            "Running", 389999, "Depósito · Rack D4",   "42, 44"),
    ("ADI-UBL",    "Adidas Ultraboost Light",        "Running", 329999, "Depósito · Rack E1",   "41, 43"),
    ("ADI-EVOSL",  "Adidas Adizero Evo SL",          "Running", 299999, "Depósito · Rack E1",   "42"),
    ("ADI-DURA",   "Adidas Duramo SL",               "Running", 119999, "Depósito · Rack E2",   "38, 40, 43"),
    ("ADI-RUNF",   "Adidas Runfalcon 5",             "Running", 109999, "Depósito · Rack E2",   "37, 40, 42"),
    ("PUM-RIFT",   "Puma Softride Rift",             "Running", 139999, "Depósito · Rack E3",   "39, 41"),
    ("HOK-CLIF",   "Hoka Clifton 9",                 "Running", 349999, "Depósito · Rack E3",   "40, 42"),
    ("ON-CLOUDM",  "On Cloudmonster",                "Running", 369999, "Depósito · Rack E4",   "41, 43"),
    # ── Trail ──────────────────────────────────────────────────────────────
    ("SAL-XT6",    "Salomon XT-6",                   "Trail",   449999, "Vidriera · Exhibidor", "41, 43"),
    ("SAL-SPEED",  "Salomon Speedcross 6",           "Trail",   379999, "Depósito · Rack E4",   "40, 42"),
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
    total_movimientos = 0

    for sku, nombre, categoria, precio, ubicacion, talles in PRODUCTOS:
        pares = [t.strip() for t in talles.split(",")]
        stock_final = len(pares)  # un par por talle: el stock ES la cantidad de talles

        producto = Product(
            sku=sku, nombre=nombre, categoria=categoria, precio=precio,
            stock=0, ubicacion=ubicacion, talles=", ".join(pares),
            # Con pares únicos, el mínimo razonable es 1: avisar cuando queda
            # el último. Para modelos de un solo par no tiene sentido alertar.
            stock_minimo=1 if stock_final > 1 else 0,
        )
        db.session.add(producto)
        db.session.flush()  # necesitamos el id para los movimientos

        # Historia simple y coherente: la compra inicial de los pares y, en
        # algunos modelos, la venta de un par. Por eso la entrada puede traer
        # un par más que los talles listados hoy: ese par ya se vendió.
        vendio = random.random() < 0.35
        inicial = stock_final + (1 if vendio else 0)
        movimientos = [
            Movement(
                product_id=producto.id, tipo="entrada", motivo="compra",
                cantidad=inicial, nota="Compra de pares al proveedor",
                fecha=ahora - timedelta(days=14),
            )
        ]
        if vendio:
            movimientos.append(Movement(
                product_id=producto.id, tipo="salida", motivo="venta",
                cantidad=1, nota="Venta en persona",
                fecha=ahora - timedelta(days=random.randint(1, 12), hours=random.randint(0, 10)),
            ))

        producto.stock = stock_final  # el stock final coincide con el historial
        db.session.add_all(movimientos)
        total_movimientos += len(movimientos)

    db.session.commit()
    print(f"Seed OK: {len(PRODUCTOS)} modelos, {total_movimientos} movimientos, usuario demo/demo1234.")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        sembrar()
