"""Rutas de autenticación: login y logout.

Un Blueprint es un "módulo de rutas": agrupa endpoints relacionados
para no meter todo en un solo archivo gigante.
"""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.models import User

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    # Si ya está logueado, no tiene sentido mostrarle el login
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)  # guarda el id del usuario en la cookie de sesión
            # Si venía de una página protegida, Flask-Login agrega ?next=/esa/pagina
            next_page = request.args.get("next")
            # Solo aceptamos rutas internas (que empiecen con "/") para evitar
            # que alguien arme un link que redirija a un sitio malicioso
            if next_page and next_page.startswith("/"):
                return redirect(next_page)
            return redirect(url_for("dashboard.index"))

        flash("Usuario o contraseña incorrectos", "error")

    return render_template("login.html")


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
