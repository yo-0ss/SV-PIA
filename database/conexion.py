import pymysql

def get_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="root123",
        database="piabd",
        cursorclass=pymysql.cursors.DictCursor
    )