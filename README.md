# 📦 StockBox

> Warehouse stock management, built by someone who actually worked the warehouse floor.

**[English](#english)** · **[Español](#español)**

---

## English

### Why this exists

I spent 5+ years working in warehouses and logistics using enterprise systems like SAP and Integra. StockBox is the tool I wish every small business had: simple stock control with a full audit trail, built with the workflows of a real warehouse in mind.

### Features

- 🔐 **Session-based auth** — password hashing (no plain-text, ever), protected routes, safe `?next=` redirects
- 📋 **Product CRUD** — search, category filters, SKU normalization, physical location (rack/shelf)
- ↕️ **Stock movements** — stock is never edited by hand: every change is an entry/exit with a reason (purchase, sale, adjustment, return). Full audit trail, like real WMS systems
- 🚫 **Business rules enforced server-side** — stock can never go negative; the backend re-validates everything, never trusting the client
- 📊 **Dashboard** — inventory value (aggregated in SQL, not Python), low-stock alerts sorted by criticality, one-click restock flow
- 🛍️ **Public storefront** — a customer-facing shop at `/tienda` reads the *same* product table: no sync, one source of truth. Cart, size picker and checkout; confirming an order deducts stock through the same audited sale movement as any warehouse exit, and the order lands in the admin panel with the customer's WhatsApp for delivery
- 🌱 **Reproducible demo data** — `seed.py` with a fixed random seed (see *Demo data* below)

### Demo data

`seed.py` loads a small sneaker-reseller catalog, ready to explore:

- **59 models** — the best sellers of the Argentine market (Air Force 1, Dunk, Jordan, Samba, New Balance, Asics…) at realistic Argentine retail prices
- Organized by category: `Básquet · Retro · Running · Trail · Urbanas`
- **Unique pairs**, like a real small reseller: 1–3 pairs per model, and each listed size is one physical pair — selling size 42 removes that exact pair from the storefront
- Physical locations (racks, showroom, shop window) and a coherent movement history (fixed random seed: always reproducible)

### Tech stack

| Layer | Tech |
|---|---|
| Backend | Python · Flask · SQLAlchemy · Flask-Login |
| Database | SQLite (dev) / PostgreSQL via `DATABASE_URL` (prod) |
| Frontend | Jinja2 · Tailwind CSS · vanilla JavaScript |
| Deploy | Gunicorn · Render |

### Run it locally

```bash
git clone https://github.com/<user>/stockbox.git
cd stockbox
python -m venv venv
venv\Scripts\activate        # Windows  ·  source venv/bin/activate on Linux/Mac
pip install -r requirements.txt
python seed.py               # demo data + demo user
python run.py
```

Open `http://127.0.0.1:5000` → log in with **demo / demo1234**.

Create your own user: `flask --app run create-admin <username> <password>`

### Design decisions (and honest tradeoffs)

- **Movements over edits**: stock changes only through recorded movements — you can always answer *"why is the stock what it is?"*. Deleting a product cascades its history (a real system would soft-delete).
- **Atomic transactions**: the new stock and its movement are committed together — either both persist or neither does.
- **PRG pattern** everywhere: POST → redirect → GET, so refreshing never double-submits.
- **Known tradeoffs** (deliberate for an MVP, on the roadmap): CSRF protection (Flask-WTF), row-locking for concurrent movements (`SELECT FOR UPDATE`), pagination, automated tests, soft-delete.

---

## Español

### Por qué existe

Trabajé más de 5 años en depósitos y logística usando sistemas enterprise como SAP e Integra. StockBox es la herramienta que me hubiera gustado que tuviera cualquier comercio chico: control de stock simple con historial completo, pensada con los flujos de un depósito real.

### Funcionalidades

- 🔐 **Login con sesiones** — contraseñas hasheadas, rutas protegidas, redirects seguros
- 📋 **ABM de productos** — búsqueda, filtros por categoría, ubicación física (rack/estante)
- ↕️ **Movimientos de stock** — el stock nunca se edita a mano: cada cambio es una entrada/salida con motivo. Historial auditable completo, como los WMS reales
- 🚫 **Reglas de negocio en el backend** — el stock nunca queda negativo; el servidor revalida todo
- 📊 **Dashboard** — valor del inventario (agregado en SQL), alertas de stock bajo ordenadas por criticidad, reposición en un clic
- 🛍️ **Tienda pública** — un frente de venta en `/tienda` lee la *misma* tabla de productos: no hay sincronización, hay una sola fuente de verdad. Carrito, selector de talle y checkout; al confirmar un pedido se descuenta stock con el mismo movimiento de venta auditado que cualquier salida de depósito, y el pedido aparece en el panel con el WhatsApp del cliente para coordinar la entrega
- 🌱 **Datos demo reproducibles** — `seed.py` con seed fijo (ver *Datos demo*)

### Datos demo

`seed.py` carga el catálogo de un revendedor chico de zapatillas, listo para explorar:

- **59 modelos** — los más vendidos del mercado argentino (Air Force 1, Dunk, Jordan, Samba, New Balance, Asics…) a precios reales de retail argentino
- Separados por categoría: `Básquet · Retro · Running · Trail · Urbanas`
- **Pares únicos**, como un revendedor real: 1–3 pares por modelo, y cada talle listado es un par físico — vender el talle 42 saca ese par exacto de la tienda
- Ubicaciones físicas (racks, salón, vidriera) e historial de movimientos coherente (seed fijo: siempre reproducible)

### Correrlo local

Los mismos pasos de arriba. Entrá con **demo / demo1234**.

### Decisiones de diseño

Ver la sección en inglés: movimientos en vez de ediciones (auditoría), transacciones atómicas, patrón PRG, y los tradeoffs conocidos del MVP declarados honestamente (CSRF, locking de concurrencia, paginación, tests).

---

Built by Mathias Vorrath · Buenos Aires, Argentina
