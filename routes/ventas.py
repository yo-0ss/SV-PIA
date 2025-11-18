from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database.conexion import get_connection
from utils.seguridad import login_requerido
import pymysql

ventas_bp = Blueprint('ventas', __name__, url_prefix="/ventas")

# --- LISTA DE VENTAS (Req V4) ---
@ventas_bp.route('/', methods=['GET'])
@login_requerido
def lista_ventas():

    buscar = request.args.get('buscar', '').strip()
    fecha = request.args.get('fecha', '').strip()
    empleado = request.args.get('empleado', '').strip()

    conexion = get_connection()
    cursor = conexion.cursor()

    sql = """
        SELECT v.idventa, v.fecha, c.nombre AS cliente, e.nombre AS empleado, 
               v.total, v.estado
        FROM venta v
        JOIN cliente c ON v.idcliente = c.idcliente
        JOIN empleado e ON v.idempleado = e.idempleado
        WHERE 1=1
    """
    valores = []

    if buscar:
        sql += " AND c.nombre LIKE %s"
        valores.append(f"%{buscar}%")

    if fecha:
        sql += " AND DATE(v.fecha) = %s"
        valores.append(fecha)

    if empleado:
        sql += " AND e.nombre LIKE %s"
        valores.append(f"%{empleado}%")

    sql += " ORDER BY v.fecha DESC"

    cursor.execute(sql, valores)
    ventas = cursor.fetchall()
    conexion.close()

    return render_template("ventas.html",
                           ventas=ventas,
                           buscar=buscar,
                           fecha=fecha,
                           empleado=empleado)


# --- FORMULARIO PARA NUEVA VENTA (Req V1) ---
@ventas_bp.route('/nuevo')
@login_requerido
def nueva_venta_form():
    conexion = get_connection()
    cursor = conexion.cursor()
    # Obtenemos clientes para el dropdown
    cursor.execute("SELECT idcliente, nombre FROM cliente WHERE estado = 'Activo'")
    clientes = cursor.fetchall()
    conexion.close()
    
    return render_template("nueva-venta.html", clientes=clientes)

# --- CREAR LA VENTA (Req V1) ---
@ventas_bp.route('/crear', methods=['POST'])
@login_requerido
def crear_venta():
    id_cliente = request.form['idcliente']
    id_empleado = session['idEmpleado'] # Obtenemos el empleado de la sesión

    conexion = get_connection()
    cursor = conexion.cursor()
    
    # Creamos la venta "cabecera" con estado 'nuevo' y total 0
    cursor.execute("""
        INSERT INTO venta (idcliente, idempleado, estado, total)
        VALUES (%s, %s, 'nuevo', 0.00)
    """, (id_cliente, id_empleado))
    
    # Obtenemos el ID de la venta que acabamos de crear
    id_nueva_venta = cursor.lastrowid
    
    conexion.commit()
    conexion.close()
    
    flash("Venta creada. Ahora puede agregar productos.")
    # Redirigimos al detalle de la venta para empezar a agregar productos
    return redirect(url_for('ventas.detalle_venta', id=id_nueva_venta))


# --- DETALLE DE VENTA (Req V2, V5) ---
@ventas_bp.route('/detalle/<int:id>')
@login_requerido
def detalle_venta(id):
    conexion = get_connection()
    cursor = conexion.cursor()
    
    # Usamos la VISTA para obtener toda la info de la venta
    cursor.execute("SELECT * FROM vista_reporte_ventas_detallado WHERE idventa = %s", (id,))
    # Usamos fetchall() porque pueden ser varios productos
    detalles = cursor.fetchall()
    
    # Usamos la VISTA para obtener productos disponibles
    cursor.execute("SELECT * FROM vista_productos_activos")
    productos_disponibles = cursor.fetchall()
    
    conexion.close()
    
    if not detalles:
        flash("Venta no encontrada.")
        return redirect(url_for('ventas.lista_ventas'))
        
    # Pasamos la lista de detalles y la venta (el primer registro)
    return render_template("venta-detalle.html", 
                           detalles=detalles, 
                           venta=detalles[0], 
                           productos=productos_disponibles)

# --- AGREGAR PRODUCTO A VENTA (Req V2) ---
@ventas_bp.route('/detalle/<int:id>/agregar_producto', methods=['POST'])
@login_requerido
def agregar_producto_venta(id):
    id_producto = request.form['idproducto']
    cantidad = int(request.form['cantidad'])
    
    if cantidad <= 0:
        flash("La cantidad debe ser mayor a 0.")
        return redirect(url_for('ventas.detalle_venta', id=id))
        
    conexion = get_connection()
    cursor = conexion.cursor()
    
    try:
        # Obtenemos el precio unitario del producto
        cursor.execute("SELECT precio FROM producto WHERE idproducto = %s", (id_producto,))
        producto = cursor.fetchone()
        
        if not producto:
            flash("Producto no encontrado.")
            return redirect(url_for('ventas.detalle_venta', id=id))

        precio_unitario = producto['precio']
        
        # Insertamos en detalle_venta
        # ¡LOS TRIGGERS SE ENCARGARÁN DE TODO!
        # 1. trg_before_insert... validará el stock y calculará el subtotal
        # 2. trg_after_insert... restará el stock y actualizará el total de la venta
        cursor.execute("""
            INSERT INTO detalle_venta (idventa, idproducto, cantidad, preciounitario)
            VALUES (%s, %s, %s, %s)
        """, (id, id_producto, cantidad, precio_unitario))
        
        conexion.commit()
        flash("Producto agregado correctamente.")
        
    except pymysql.Error as e:
        # Capturamos el error del trigger (ej. stock insuficiente)
        conexion.rollback()
        flash(f"Error al agregar producto: {e}")
        
    finally:
        conexion.close()
        
    return redirect(url_for('ventas.detalle_venta', id=id))

# --- ELIMINAR PRODUCTO DE VENTA ---
@ventas_bp.route('/detalle/eliminar_producto/<int:id_detalle>')
@login_requerido
def eliminar_producto_venta(id_detalle):
    conexion = get_connection()
    cursor = conexion.cursor()
    
    # Obtenemos el idventa ANTES de borrar para saber a dónde redirigir
    cursor.execute("SELECT idventa FROM detalle_venta WHERE iddetalle = %s", (id_detalle,))
    detalle = cursor.fetchone()
    
    if not detalle:
        flash("Detalle no encontrado.")
        conexion.close()
        return redirect(url_for('ventas.lista_ventas'))

    id_venta = detalle['idventa']
    
    # ¡EL TRIGGER 'trg_after_delete_detalle_venta' SE ENCARGARÁ DE TODO!
    # 1. Devolverá el stock
    # 2. Recalculará el total de la venta
    cursor.execute("DELETE FROM detalle_venta WHERE iddetalle = %s", (id_detalle,))
    conexion.commit()
    conexion.close()
    
    flash("Producto eliminado de la venta.")
    return redirect(url_for('ventas.detalle_venta', id=id_venta))

# --- ACTUALIZAR ESTADO DE VENTA (Req V1) ---
@ventas_bp.route('/detalle/<int:id>/actualizar_estado', methods=['POST'])
@login_requerido
def actualizar_estado_venta(id):
    nuevo_estado = request.form['estado']
    
    conexion = get_connection()
    cursor = conexion.cursor()
    
    cursor.execute("UPDATE venta SET estado = %s WHERE idventa = %s", (nuevo_estado, id))
    conexion.commit()
    conexion.close()
    
    flash("Estado de la venta actualizado.")
    return redirect(url_for('ventas.detalle_venta', id=id))

# --- CANCELAR VENTA (Req V6) ---
@ventas_bp.route('/<int:id>/cancelar')
@login_requerido
def cancelar_venta(id):
    conexion = get_connection()
    cursor = conexion.cursor()
    
    # Para cancelar, borramos todos sus detalles
    # El trigger 'trg_after_delete_detalle_venta' devolverá el stock
    cursor.execute("DELETE FROM detalle_venta WHERE idventa = %s", (id,))
    
    # Luego, actualizamos la cabecera
    cursor.execute("UPDATE venta SET estado = 'Cancelado', total = 0.00 WHERE idventa = %s", (id,))
    
    conexion.commit()
    conexion.close()
    
    flash("Venta cancelada. El stock ha sido devuelto.")
    return redirect(url_for('ventas.lista_ventas'))