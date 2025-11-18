from flask import Flask
from routes.login import login_bp
from routes.clientes import clientes_bp
from routes.productos import productos_bp
from routes.empleados import empleados_bp
from routes.ventas import ventas_bp
from routes.reportes import reportes_bp

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Registro de Blueprints
app.register_blueprint(login_bp)
app.register_blueprint(clientes_bp)
app.register_blueprint(productos_bp)
app.register_blueprint(empleados_bp)
app.register_blueprint(ventas_bp)
app.register_blueprint(reportes_bp)

if __name__ == "__main__":
    app.run(port=3000, debug=True)