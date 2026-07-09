"""App factory: construye y configura la aplicación Flask.

Usamos el patrón "application factory" en vez de crear la app suelta a nivel
de módulo. Ventajas: podemos crear la app con distintas configs (desarrollo,
tests, producción) y evitamos imports circulares entre modelos y rutas.
"""
import click
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

# Extensiones a nivel de módulo, SIN app todavía.
# Se "atan" a la app dentro de create_app() con init_app().
db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)
    login_manager.init_app(app)
    # Si alguien entra a una página protegida sin loguearse, va acá:
    login_manager.login_view = "auth.login"

    # Importar los modelos ANTES de create_all para que SQLAlchemy los conozca
    from app import models  # noqa: F401

    # Blueprints: cada módulo de rutas se registra acá
    from app.routes.auth import bp as auth_bp
    from app.routes.dashboard import bp as dashboard_bp
    from app.routes.movements import bp as movements_bp
    from app.routes.orders import bp as orders_bp
    from app.routes.products import bp as products_bp
    from app.routes.store import bp as store_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(movements_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(store_bp)

    @app.cli.command("create-admin")
    @click.argument("username")
    @click.argument("password")
    def create_admin(username, password):
        """Crea un usuario. Uso: flask --app run create-admin <usuario> <contraseña>"""
        if models.User.query.filter_by(username=username).first():
            click.echo(f"El usuario '{username}' ya existe.")
            return
        user = models.User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Usuario '{username}' creado.")

    with app.app_context():
        db.create_all()

    return app
