from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database.conexion import get_connection
from werkzeug.security import check_password_hash, generate_password_hash

login_bp = Blueprint('login', __name__)

@login_bp.route('/')
def login_form():
    return render_template("login.html")


@login_bp.route('/login', methods=['POST'])
def login():
    usuario = request.form['usuario']
    password = request.form['password']

    conexion = get_connection()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM Empleado WHERE usuario=%s", (usuario,))
    empleado = cursor.fetchone()

    if empleado and check_password_hash(empleado['password_hash'], password):
        session['idEmpleado'] = empleado['idempleado']
        session['nombre'] = empleado['nombre']
        session['rol'] = empleado['rol']
        flash(f"Bienvenido, {empleado['nombre']}!")
        return redirect(url_for('clientes.lista_clientes'))
    else:
        flash("Usuario o contraseña incorrectos")
        return redirect(url_for('login.login_form'))


@login_bp.route('/logout')
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.")
    return redirect(url_for('login.login_form'))

