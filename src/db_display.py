import sqlite3
from collections import OrderedDict

# Connect to the database
conn = sqlite3.connect("people.db")
cursor = conn.cursor()

# Fetch all user-defined tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
tables = [row[0] for row in cursor.fetchall()]

print("📦 Tables and entries in the database:\n")

for table in tables:
    print(f"🔹 Table: {table}")

    # Fetch column names
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [col[1] for col in cursor.fetchall()]
    print("Columns:", ", ".join(columns))

    # Fetch rows
    cursor.execute(f"SELECT * FROM {table}")
    rows = cursor.fetchall()

    if rows:
        for row in rows:
            print("  ", row)
    else:
        print("  (No entries)")

    print("-" * 40)

conn.close()
