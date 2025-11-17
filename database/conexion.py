import pymysql

def get_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="root123",
        database="equipo7",
        cursorclass=pymysql.cursors.DictCursor
    )