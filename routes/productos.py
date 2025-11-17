from flask import Blueprint, render_template, request, redirect, url_for, flash
from database.conexion import get_connection
from utils.seguridad import login_requerido, admin_requerido

productos_bp = Blueprint('productos', __name__, url_prefix="/productos")

# ---- LISTAR PRODUCTOS ----
@productos_bp.route('/')
@login_requerido
def lista_productos():
    conexion = get_connection()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM producto")
    productos = cursor.fetchall()
    conexion.close()

    return render_template("productos.html", productos=productos)

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
    cursor.execute("SELECT * FROM producto WHERE idProducto = %s", (id,))
    producto = cursor.fetchone()
    conexion.close()

    if not producto:
        flash("Producto no encontrado.")
        return redirect(url_for('productos.lista_productos'))

    return render_template("edit-producto.html", producto=producto)

# ---- ACTUALIZAR PRODUCTO ----
@productos_bp.route('/actualizar/<int:id>', methods=['POST'])
@login_requerido
@admin_requerido
def actualizar_producto(id):
    nombre = request.form['nombre']
    categoria = request.form['categoria']
    precio = float(request.form['precio'])
    stock = int(request.form['stock'])
    activo = int(request.form['activo'])  # 0 o 1

    if precio < 0 or stock < 0:
        flash("El precio y el stock deben ser mayores o iguales a 0.")
        return redirect(url_for('productos.editar_producto', id=id))

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""
        UPDATE producto
        SET nombre=%s, categoria=%s, precio=%s, stock=%s, activo=%s
        WHERE idProducto=%s
    """, (nombre, categoria, precio, stock, activo, id))

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

    cursor.execute("DELETE FROM producto WHERE idProducto=%s", (id,))
    conexion.commit()
    conexion.close()

    flash("Producto eliminado.")
    return redirect(url_for('productos.lista_productos'))
