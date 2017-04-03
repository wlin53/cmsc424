import mysql.connector
conn = mysql.connector.connect(
        user='root', 
        password='password', 
        database='sys')

cursor = conn.cursor()

cursor.execute('SELECT foo FROM jack')

print([ x for x in cursor ])

conn.close()
