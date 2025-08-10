import sqlite3
from collections import OrderedDict

def get_id_by_email(email, db_path=""):
    """
    Returns the person_id (integer) corresponding to the given email.
    Returns None if the email is not found.
    """
    if not email:
        raise ValueError("Email must be provided")

    if not db_path:
        raise ValueError("Database path must be provided")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM people WHERE email = ?", (email,))
    result = cursor.fetchone()
    conn.close()

    return result[0] if result else None

def list_people(db_path=""):
    """
    Returns a list of tuples (id, name, email) for all people in the database.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email FROM people")
    people = cursor.fetchall()
    conn.close()
    return people

from collections import OrderedDict
import sqlite3

def list_tasks_with_people(db_path):
    """
    Returns an OrderedDict sorted by importance (descending):
    {
        task_id: {
            "title": str,
            "description": str,
            "tag": str,
            "importance": int,
            "people": [ (role, "Name <email>"), ... ]
        },
        ...
    }
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    cur.execute("""
        SELECT
            t.id,
            t.title,
            t.description,
            t.tag,
            t.importance,
            p.name,
            p.email,
            a.role
        FROM task_assignments a
        JOIN tasks  t ON a.task_id = t.id
        JOIN people p ON a.person_id = p.id
        ORDER BY t.id, p.name
    """)

    tasks = {}
    for task_id, title, desc, tag, importance, name, email, role in cur.fetchall():
        if task_id not in tasks:
            tasks[task_id] = {
                "title": title,
                "description": desc,
                "tag": tag,
                "importance": importance,
                "people": []
            }
        # keep tuples; person string does NOT include role
        tasks[task_id]["people"].append((role, f"{name} <{email}>"))

    conn.close()

    # Sort people: supervisors first, then members (keep tuples)
    role_order = {"supervisor": 0, "member": 1}
    for task in tasks.values():
        task["people"] = sorted(
            task["people"],
            key=lambda x: role_order.get(x[0], 99)
        )

    # Sort tasks by importance (descending)
    sorted_tasks = OrderedDict(
        sorted(tasks.items(), key=lambda x: (-x[1]["importance"], x[0]))
    )
    return sorted_tasks

def list_people_with_tasks(db_path):
    """
    Returns a list of (person_name, person_email, tasks)
    where tasks is a list of (title, tag). People with no tasks are included.
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    cur.execute("""
        SELECT
            p.id,
            p.name,
            p.email,
            t.title,
            t.tag,
            a.role
        FROM people p
        LEFT JOIN task_assignments a ON a.person_id = p.id
        LEFT JOIN tasks t ON t.id = a.task_id
        ORDER BY p.name, COALESCE(t.title, '')
    """)

    people_tasks = OrderedDict()
    for person_id, name, email, title, tag, role in cur.fetchall():
        if person_id not in people_tasks:
            people_tasks[person_id] = {"name": name, "email": email, "tasks": []}
        if title is not None and tag is not None:
            people_tasks[person_id]["tasks"].append((title, tag, role))

    conn.close()

    return people_tasks