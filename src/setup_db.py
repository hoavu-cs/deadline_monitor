import sqlite3

# Connect to the database
conn = sqlite3.connect("people.db")
cursor = conn.cursor()

# Create the table if it doesn't exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS people (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    description TEXT,
    deadline TEXT)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS task_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER,
    task_id INTEGER,
    role TEXT CHECK(role IN ('supervisor', 'member')),
    FOREIGN KEY (person_id) REFERENCES people(id),
    FOREIGN KEY (task_id) REFERENCES tasks(id)
)
""")

conn.commit()
conn.close()

print("Database and table created. ✅ ")
