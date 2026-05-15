
import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

print("Updating products_images to remove dashes from FKs...")

# Find all images where the product ID has dashes
cursor.execute("SELECT id, products_product_id FROM products_images WHERE products_product_id LIKE '%-%'")
rows = cursor.fetchall()

for row in rows:
    img_id = row[0]
    old_fk = row[1]
    new_fk = old_fk.replace('-', '')
    print(f"Updating image {img_id}: {old_fk} -> {new_fk}")
    cursor.execute("UPDATE products_images SET products_product_id = ? WHERE id = ?", (new_fk, img_id))

conn.commit()
conn.close()
print("Done.")
