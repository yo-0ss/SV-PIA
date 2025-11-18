from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database.conexion import get_connection
from utils.seguridad import login_requerido, admin_requerido

productos_bp = Blueprint('productos', __name__, url_prefix="/productos")

# ---- LISTAR PRODUCTOS ----
@productos_bp.route('/', methods=['GET'])
@login_requerido
def lista_productos():

    buscar = request.args.get('buscar', '').strip()

    conexion = get_connection()
    cursor = conexion.cursor()

    sql = "SELECT * FROM producto WHERE 1=1"
    valores = []

    # Si buscar es número → buscar por ID exacto
    if buscar.isdigit():
        sql += " AND idProducto = %s"
        valores.append(int(buscar))

    # Si buscar es texto → buscar nombre parcial
    elif buscar:
        sql += " AND nombre LIKE %s"
        valores.append(f"%{buscar}%")

    cursor.execute(sql, valores)
    productos = cursor.fetchall()
    conexion.close()

    return render_template("productos.html", productos=productos, buscar=buscar)

# ---- NUEVO PRODUCTO ----
@productos_bp.route('/nuevo', methods=['POST'])
@login_requerido
@admin_requerido
def nuevo_producto():
    nombre = request.form['nombre']
    categoria = request.form['categoria']
    precio = float(request.form['precio'])
    stock = int(request.form['stock'])

    # Validaciones
    if nombre.strip() == "":
        flash("El nombre no puede estar vacío.")
        return redirect(url_for('productos.lista_productos'))

    if precio < 0 or stock < 0:
        flash("El precio y el stock deben ser mayores o iguales a 0.")
        return redirect(url_for('productos.lista_productos'))

    conexion = get_connection()
    cursor = conexion.cursor()

    # Validación: nombre duplicado
    cursor.execute("SELECT * FROM producto WHERE nombre = %s", (nombre,))
    if cursor.fetchone():
        conexion.close()
        flash("Ya existe un producto con ese nombre.")
        return redirect(url_for('productos.lista_productos'))

    # INSERT con activo = 1 por defecto
    cursor.execute("""
        INSERT INTO producto(nombre, categoria, precio, stock)
        VALUES (%s, %s, %s, %s)
    """, (nombre, categoria, precio, stock))

    conexion.commit()
    conexion.close()

    flash("Producto agregado correctamente.")
    return redirect(url_for('productos.lista_productos'))

# ---- EDITAR PRODUCTO ----
@productos_bp.route('/detalle/<int:id>', methods=['GET'])
@login_requerido
@admin_requerido
def get_producto(id):
    conexion = get_connection()
    cursor = conexion.cursor()

    # Datos del producto
    cursor.execute("SELECT * FROM producto WHERE idProducto = %s", (id,))
    producto = cursor.fetchone()

    if not producto:
        conexion.close()
        flash("Producto no encontrado.")
        return redirect(url_for('productos.lista_productos'))

    # Historial de ajustes
    cursor.execute("SELECT * FROM vista_ajustes_producto WHERE idproducto = %s", (id,))
    ajustes = cursor.fetchall()

    conexion.close()

    return render_template("edit-producto.html", producto=producto, ajustes=ajustes)

# ---- ACTUALIZAR PRODUCTO ----
@productos_bp.route('/actualizar/<int:id>', methods=['POST'])
@login_requerido
@admin_requerido
def actualizar_producto(id):
    nombre = request.form['nombre']
    categoria = request.form['categoria']
    precio = float(request.form['precio'])
    activo = int(request.form['activo'])  # 0 o 1

    if precio < 0:
        flash("El precio no puede ser negativo.")
        return redirect(url_for('productos.editar_producto', id=id))

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""
        UPDATE producto
        SET nombre=%s, categoria=%s, precio=%s, activo=%s
        WHERE idProducto=%s
    """, (nombre, categoria, precio, activo, id))

    conexion.commit()
    conexion.close()

    flash("Producto actualizado correctamente.")
    return redirect(url_for('productos.lista_productos'))


# ---- ELIMINAR PRODUCTO ----
@productos_bp.route('/eliminar/<int:id>')
@login_requerido
@admin_requerido
def eliminar_producto(id):
    conexion = get_connection()
    cursor = conexion.cursor()

    # Evitar eliminación si el producto está en ventas (RP08)
    cursor.execute("SELECT * FROM detalle_venta WHERE idProducto=%s", (id,))
    if cursor.fetchone():
        conexion.close()
        flash("No se puede eliminar el producto porque tiene ventas registradas.")
        return redirect(url_for('productos.lista_productos'))

    cursor.execute("DELETE FROM producto WHERE idProducto=%s", (id,))
    conexion.commit()
    conexion.close()

    flash("Producto eliminado.")
    return redirect(url_for('productos.lista_productos'))

# ============================================================
#   FORMULARIO AJUSTE MANUAL DE STOCK (RP07)
# ============================================================
@productos_bp.route('/ajustar/<int:id>', methods=['GET'])
@login_requerido
@admin_requerido
def ajustar_stock_form(id):

    conexion = get_connection()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM producto WHERE idProducto = %s", (id,))
    producto = cursor.fetchone()
    conexion.close()

    if not producto:
        flash("Producto no encontrado.")
        return redirect(url_for('productos.lista_productos'))

    # Evitar ajustar stock de productos inactivos
    if producto['activo'] == 0:
        flash("No puedes ajustar stock de un producto inactivo.")
        return redirect(url_for('productos.lista_productos'))

    return render_template("ajuste-stock.html", producto=producto)

# ============================================================
#   PROCESAR AJUSTE MANUAL DE STOCK (RP07)
# ============================================================
@productos_bp.route('/ajustar/<int:id>', methods=['POST'])
@login_requerido
@admin_requerido
def procesar_ajuste(id):

    # VALIDAR CANTIDAD
    try:
        cantidad = int(request.form['cantidad'])
    except:
        flash("La cantidad debe ser un número entero.")
        return redirect(url_for('productos.ajustar_stock_form', id=id))

    if cantidad == 0:
        flash("La cantidad debe ser diferente de 0.")
        return redirect(url_for('productos.ajustar_stock_form', id=id))

    # VALIDAR MOTIVO
    motivo = request.form['motivo']
    if motivo.strip() == "":
        flash("El motivo del ajuste es obligatorio.")
        return redirect(url_for('productos.ajustar_stock_form', id=id))

    # OBTENER EMPLEADO
    idempleado = session.get('idEmpleado')

    conexion = get_connection()
    cursor = conexion.cursor()

    # ACTUALIZAR STOCK
    cursor.execute("""
        UPDATE producto
        SET stock = stock + %s
        WHERE idProducto = %s
    """, (cantidad, id))

    # REGISTRAR AJUSTE
    cursor.execute("""
        INSERT INTO ajuste_stock(idproducto, idempleado, cantidad, motivo)
        VALUES (%s, %s, %s, %s)
    """, (id, idempleado, cantidad, motivo))

    conexion.commit()
    conexion.close()

    flash("Ajuste de stock registrado correctamente.")
    return redirect(url_for('productos.lista_productos'))
