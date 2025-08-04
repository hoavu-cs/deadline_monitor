import sqlite3

# Connect to the database
conn = sqlite3.connect("tasks.db")
cursor = conn.cursor()

# Create the table if it doesn't exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT,
    project_name TEXT,
    due_date DATE,
    task_type TEXT,
    status TEXT DEFAULT 'pending'
)
""")

conn.commit()
conn.close()

print("Database and table created.")
