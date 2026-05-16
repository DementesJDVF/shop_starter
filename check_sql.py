
import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

print("--- products_product IDs ---")
cursor.execute("SELECT id FROM products_product")
for row in cursor.fetchall():
    print(f"'{row[0]}'")

print("\n--- products_images FKs ---")
cursor.execute("SELECT id, products_product_id FROM products_images")
for row in cursor.fetchall():
    print(f"ID: {row[0]}, FK: '{row[1]}'")

conn.close()
