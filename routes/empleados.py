from flask import Blueprint, render_template, request, redirect, url_for, flash
from database.conexion import get_connection
from utils.seguridad import login_requerido, admin_requerido

empleados_bp = Blueprint('empleados', __name__, url_prefix="/empleados")

# --- LISTA DE EMPLEADOS ---
@empleados_bp.route('/')
@login_requerido
@admin_requerido
def lista_empleados():
    conexion = get_connection()
    cursor = conexion.cursor()
    cursor.execute("SELECT idEmpleado, nombre, puesto, telefono, correo, rol FROM empleado")
    empleados = cursor.fetchall()
    conexion.close()
    return render_template("empleados.html", empleados=empleados)

# --- AGREGAR EMPLEADO ---
@empleados_bp.route('/nuevo', methods=['POST'])
@login_requerido
@admin_requerido
def nuevo_empleado():
    nombre = request.form['nombre']
    puesto = request.form['puesto']
    telefono = request.form['telefono']
    correo = request.form['correo']
    usuario = request.form['usuario']
    password = request.form['password']
    rol = request.form['rol']

    from werkzeug.security import generate_password_hash
    hash_password = generate_password_hash(password)

    conexion = get_connection()
    cursor = conexion.cursor()
    cursor.execute("""
        INSERT INTO empleado(nombre, puesto, telefono, correo, usuario, password_hash, rol)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (nombre, puesto, telefono, correo, usuario, hash_password, rol))
    conexion.commit()
    conexion.close()

    flash("Empleado agregado correctamente.")
    return redirect(url_for('empleados.lista_empleados'))


# --- ELIMINAR EMPLEADO ---
@empleados_bp.route('/eliminar/<int:id>')
@login_requerido
@admin_requerido
def eliminar_empleado(id):
    conexion = get_connection()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM empleado WHERE idEmpleado=%s", (id,))
    conexion.commit()
    conexion.close()

    flash("Empleado eliminado.")
    return redirect(url_for('empleados.lista_empleados'))

# --- GET EMPLEADO ---
@empleados_bp.route('/detalle/<int:id>', methods=['GET'])
@login_requerido
@admin_requerido
def get_empleado(id):
    conexion = get_connection()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM empleado WHERE idEmpleado = %s", (id,))
    empleado = cursor.fetchone()
    conexion.close()

    if not empleado:
        flash("Empleado no encontrado.")
        return redirect(url_for('empleados.lista_empleados'))

    return render_template('edit-empleado.html', empleado=empleado)


# --- ACTUALIZAR EMPLEADO ---
@empleados_bp.route('/actualizar/<int:id>', methods=['POST'])
@login_requerido
@admin_requerido
def actualizar_empleado(id):

    nombre = request.form['nombre']
    puesto = request.form['puesto']
    telefono = request.form['telefono']
    correo = request.form['correo']
    usuario = request.form['usuario']
    rol = request.form['rol']

    nueva_password = request.form['password']  # contraseña SIN hash del formulario

    conexion = get_connection()
    cursor = conexion.cursor()

    # Si el usuario NO escribió nueva contraseña → NO modificar password_hash
    if nueva_password.strip() == "":
        cursor.execute("""
            UPDATE empleado 
            SET nombre=%s, puesto=%s, telefono=%s, correo=%s, usuario=%s, rol=%s
            WHERE idEmpleado=%s
        """, (nombre, puesto, telefono, correo, usuario, rol, id))

    else:
        # Si hay nueva contraseña → hash nuevo
        from werkzeug.security import generate_password_hash
        password_hash = generate_password_hash(nueva_password)

        cursor.execute("""
            UPDATE empleado 
            SET nombre=%s, puesto=%s, telefono=%s, correo=%s, usuario=%s, 
                password_hash=%s, rol=%s
            WHERE idEmpleado=%s
        """, (nombre, puesto, telefono, correo, usuario, password_hash, rol, id))

    conexion.commit()
    conexion.close()

    flash("Empleado actualizado correctamente.")
    return redirect(url_for('empleados.lista_empleados'))