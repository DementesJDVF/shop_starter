from django.db import connection

query_drop_table = "DROP TABLE IF EXISTS audit_log;"
query_delete_migrations = "DELETE FROM django_migrations WHERE app = 'audit';"

with connection.cursor() as cursor:
    try:
        cursor.execute(query_drop_table)
        print("Dropped table audit_log if it existed.")
    except Exception as e:
        print(f"Error dropping table: {e}")
        
    try:
        cursor.execute(query_delete_migrations)
        print("Deleted audit migrations from django_migrations.")
    except Exception as e:
        print(f"Error dropping migrations: {e}")
