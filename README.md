📌 Proyecto SV-PIA

Bienvenido al repositorio del sistema SV-PIA.
Aquí encontrarás todo el código necesario para configurar, ejecutar y continuar el desarrollo del proyecto.

## 🚀 1. Clonar este repositorio

Para obtener una copia local del proyecto, ejecuta en tu terminal:

```
git clone https://github.com/yo-0ss/SV-PIA.git
```

## 🗄️ 2. Importar la Base de Datos

Abre MySQL Workbench

Crea una base de datos llamada: equipo7

Importa el archivo .sql

## 🔑 3. Configurar credenciales de MySQL

Edita el archivo donde se encuentra la conexión (conexion.py) y ajusta tus datos:

host="localhost"
user="TU_USUARIO"
password="TU_PASSWORD"
database="piabd"

## 📦 4. Instalar dependencias

Ejecuta:
```
pip install -r requirements.txt
```

## ▶️ 5. Ejecutar el proyecto

Dentro de la carpeta del proyecto:

```
python app.py
```

Si todo está correcto, la aplicación se abrirá en:

http://127.0.0.1:3000/
