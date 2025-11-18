from flask import Blueprint, render_template
from database.conexion import get_connection
from utils.seguridad import login_requerido, admin_requerido
import pymysql

reportes_bp = Blueprint('reportes', __name__, url_prefix="/reportes")

# --- PROCEDIMIENTO 2: REPORTE DE BAJO STOCK ---
@reportes_bp.route('/bajo_stock')
@login_requerido
@admin_requerido
def reporte_bajo_stock():
    conexion = get_connection()
    cursor = conexion.cursor()
    umbral = 10 
    
    cursor.callproc('sp_reporte_productos_bajo_stock', (umbral,))
    reporte = cursor.fetchall()
    conexion.close()
    
    return render_template("reporte_stock.html", reporte=reporte, umbral=umbral)

# --- VISTA 3: REPORTE DE VENTAS POR EMPLEADO ---
@reportes_bp.route('/ventas_empleado')
@login_requerido
@admin_requerido
def reporte_ventas_empleado():
    conexion = get_connection()
    cursor = conexion.cursor()
    
    # Aquí llamamos a la 3ra vista
    cursor.execute("SELECT * FROM vista_resumen_ventas_empleado")
    reporte = cursor.fetchall()
    conexion.close()
    
    return render_template("reporte_ventas_empleado.html", reporte=reporte)

# --- PROCEDIMIENTO 3: REPORTE DE BONIFICACIONES ---
@reportes_bp.route('/bonificaciones')
@login_requerido
@admin_requerido
def reporte_bonificaciones():
    conexion = get_connection()
    cursor = conexion.cursor()
    
    # Llamamos al SP con un 10% de bono (0.10)
    cursor.callproc('sp_reporte_bonificacion_empleados', (0.10,))
    reporte = cursor.fetchall()
    conexion.close()

    return render_template("reporte_bonos.html", reporte=reporte, bono="10%")