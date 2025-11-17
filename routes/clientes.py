from flask import Blueprint, render_template, request, redirect, url_for, flash
from database.conexion import get_connection
from utils.seguridad import login_requerido, admin_requerido

clientes_bp = Blueprint('clientes', __name__, url_prefix="/clientes")

@clientes_bp.route('/')
@login_requerido
def lista_clientes():
    conexion = get_connection()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM cliente")
    clientes = cursor.fetchall()
    conexion.close()

    return render_template("clientes.html", clientes=clientes)

@clientes_bp.route('/nuevo', methods=['POST'])
@login_requerido
def nuevo_cliente():
    nombre = request.form['nombre']
    telefono = request.form['telefono']
    direccion = request.form['direccion']
    correo = request.form['correo']

    conexion = get_connection()
    cursor = conexion.cursor()
    cursor.execute("""
        INSERT INTO cliente(nombre, telefono, direccion, correo)
        VALUES (%s, %s, %s, %s)
    """, (nombre, telefono, direccion, correo))
    conexion.commit()
    conexion.close()

    flash("Cliente agregado correctamente.")
    return redirect(url_for('clientes.lista_clientes'))

# --- ELIMINAR CLIENTE ---
@clientes_bp.route('/eliminar/<int:id>')
@login_requerido
@admin_requerido
def eliminar_cliente(id):
    conexion = get_connection()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM cliente WHERE idCliente=%s", (id,))
    conexion.commit()
    conexion.close()

    flash("Cliente eliminado.")
    return redirect(url_for('clientes.lista_clientes'))


# --- GET CLIENTE ---
@clientes_bp.route('/detalle/<int:id>', methods=['GET'])
@login_requerido
@admin_requerido
def get_cliente(id):
    conexion = get_connection()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM cliente WHERE idCliente = %s", (id,))
    cliente = cursor.fetchone()
    conexion.close()

    if not cliente:
        flash("Cliente no encontrado.")
        return redirect(url_for('clientes.lista_clientes'))

    return render_template('edit-cliente.html', cliente=cliente)


# --- ACTUALIZAR EMPLEADO ---
@clientes_bp.route('/actualizar/<int:id>', methods=['POST'])
@login_requerido
@admin_requerido
def actualizar_cliente(id):

    nombre = request.form['nombre']
    telefono = request.form['telefono']
    direccion = request.form['direccion']
    correo = request.form['correo']
    estado = request.form['estado']

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""
        UPDATE cliente 
        SET nombre=%s, telefono=%s, direccion=%s, correo=%s, estado=%s
        WHERE idCliente=%s
    """, (nombre, telefono, direccion, correo, estado, id))

    conexion.commit()
    conexion.close()

    flash("Cliente actualizado correctamente.")
    return redirect(url_for('clientes.lista_clientes'))