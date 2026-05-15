
import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(products_product)")
columns = cursor.fetchall()
for col in columns:
    print(col[1])
conn.close()
