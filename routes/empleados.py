from flask import Blueprint, render_template, request, redirect, url_for, flash
from database.conexion import get_connection
from utils.seguridad import login_requerido, admin_requerido

empleados_bp = Blueprint('empleados', __name__, url_prefix="/empleados")

# --- LISTA DE EMPLEADOS ---
@empleados_bp.route('/')
@login_requerido
@admin_requerido
def lista_empleados():
    buscar = request.args.get('buscar', '').strip()
    rol_filtro = request.args.get('rol', '').strip()
    estado = request.args.get('estado', '').strip()

    conexion = get_connection()
    cursor = conexion.cursor()

    sql = "SELECT * FROM empleado WHERE 1=1"
    valores = []

    # BUSQUEDA POR NOMBRE, PUESTO, CORREO
    if buscar:
        sql += " AND (nombre LIKE %s OR puesto LIKE %s OR correo LIKE %s)"
        valores += [f"%{buscar}%", f"%{buscar}%", f"%{buscar}%"]

    # FILTRO POR ROL
    if rol_filtro:
        sql += " AND rol = %s"
        valores.append(rol_filtro)

    # FILTRO POR ESTADO
    if estado:
        sql += " AND estado = %s"
        valores.append(estado)

    cursor.execute(sql, valores)
    empleados = cursor.fetchall()
    conexion.close()

    return render_template("empleados.html", empleados=empleados,
                           buscar=buscar, rol=rol_filtro, estado=estado)

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

    cursor.execute("SELECT * FROM empleado WHERE correo = %s", (correo,))
    if cursor.fetchone():
        flash("Ya existe un empleado con ese correo.")
        return redirect(url_for('empleados.lista_empleados'))
    
    if "@" not in correo or "." not in correo:
        flash("Correo inválido.")
        return redirect(url_for('empleados.lista_empleados'))
    
    if telefono and not telefono.isdigit():
        flash("El teléfono solo debe tener números.")
        return redirect(url_for('empleados.lista_empleados'))

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

    cursor.execute("SELECT * FROM venta WHERE idEmpleado=%s", (id,))
    if cursor.fetchone():
        conexion.close()
        flash("No se puede eliminar: el empleado tiene ventas registradas.")
        return redirect(url_for('empleados.lista_empleados'))
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

    cursor.execute("SELECT idEmpleado FROM empleado WHERE correo = %s AND idEmpleado != %s", 
               (correo, id))
    if cursor.fetchone():
        flash("Correo ya registrado por otro empleado.")
        return redirect(url_for('empleados.get_empleado', id=id))
    
    # Validación correo
    if "@" not in correo or "." not in correo:
        flash("Correo inválido.")
        return redirect(url_for('empleados.get_empleado', id=id))

    # Validación teléfono
    if telefono and not telefono.isdigit():
        flash("El teléfono solo debe tener números.")
        return redirect(url_for('empleados.get_empleado', id=id))

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

@empleados_bp.route('/estado/<int:id>/<string:nuevo_estado>')
@login_requerido
@admin_requerido
def cambiar_estado_empleado(id, nuevo_estado):

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""
        UPDATE empleado
        SET estado = %s
        WHERE idEmpleado = %s
    """, (nuevo_estado, id))

    conexion.commit()
    conexion.close()

    flash("Estado del empleado actualizado.")
    return redirect(url_for('empleados.lista_empleados'))