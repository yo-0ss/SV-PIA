from flask import session, redirect, url_for, flash
from functools import wraps

def login_requerido(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'idEmpleado' not in session:
            flash("Debes iniciar sesión para acceder.")
            return redirect(url_for('login.login_form'))
        return func(*args, **kwargs)
    return wrapper


def admin_requerido(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if session.get('rol') != 'Admin':
            flash("No tienes permisos para esta acción.")
            return redirect(url_for('clientes.lista_clientes'))
        return func(*args, **kwargs)
    return wrapper

