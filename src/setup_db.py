import sqlite3

# Connect to the database
conn = sqlite3.connect("database/my_db.db")
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
    title TEXT NOT NULL,
    description TEXT,
    deadline TEXT NOT NULL,
    tag TEXT UNIQUE,
    importance INTEGER CHECK(importance BETWEEN 1 AND 5) DEFAULT 3,
    completed BOOLEAN DEFAULT FALSE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS task_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER,
    task_id INTEGER,
    role TEXT CHECK(role IN ('supervisor', 'member')),
    FOREIGN KEY (person_id) REFERENCES people(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
)
""")

conn.commit()
conn.close()

print("Database and table created. ✅ ")
