import sqlite3
from collections import OrderedDict
from typing import Iterable

from typing import Optional, Union
import sqlite3
from collections import OrderedDict

# ===== Function Signatures =====

"""
def insert_person(name: str, email: str, conn: sqlite3.Connection) -> bool:

def insert_task(
    title: str,
    description: str,
    deadline: str,
    tag: str,
    supervisor_emails: list[str],
    member_emails: list[str],
    importance: int = 3,
    conn: sqlite3.Connection
) -> bool:

def insert_person_task_pair(
    email: str,
    task_tag: str,
    role: str,
    db_path: str,
    conn: sqlite3.Connection
) -> bool:

def remove_person_task_pair(email: str, task_tag: str, conn: sqlite3.Connection) -> bool:

def get_id_by_email(email: str, conn: sqlite3.Connection) -> Optional[int]:

def list_people(conn: sqlite3.Connection) -> list[tuple[int, str, str]]:

def list_people_with_tasks(conn: sqlite3.Connection) -> "OrderedDict[int, dict[str, Union[str, list[tuple[str, str, str]]]]]":
"""

# ===== Function Implementations =====

def insert_person(name: str, email: str, conn: sqlite3.Connection) -> bool:
    if not conn:
        raise ValueError("conn must be provided")

    name = (name or "").strip()
    email = (email or "").strip().lower()
    if not name or not email:
        print("❌ Missing name or email.")
        return False

    try:
        conn.execute("PRAGMA foreign_keys = ON")
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO people (name, email) VALUES (?, ?)",
            (name, email),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        print(f"❌ Email {email} already exists. Person not added.")
        return False
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False

def insert_task(
    title, 
    description, 
    deadline, 
    tag, 
    supervisor_emails, 
    member_emails, 
    importance, 
    conn: sqlite3.Connection
) -> bool:
    if not title or not description or not deadline:
        print("❌ Missing one or more task fields. Task not added.")
        return False

    if importance == 0:
        importance = 3

    cursor = conn.cursor()

    # Insert the task
    cursor.execute("INSERT INTO tasks (title, description, deadline, tag, importance) VALUES (?, ?, ?, ?, ?)", \
        (title, description, deadline, tag, importance))
    conn.commit()

    # Get task ID
    cursor.execute("SELECT id FROM tasks WHERE title = ?", (title,))
    result = cursor.fetchone()

    if not result:
        print("❌ Could not find task after insertion.")
        return 

    task_id = result[0]
    print(f"✅ Task added: Title: {title}, Description: {description}, Deadline: {deadline}, Tag: {tag}, Importance: {importance}")


    # Handle supervisor assignment
    for email in supervisor_emails:
        person_id = get_id_by_email(email=email, conn=conn)
        if person_id:
            insert_person_task_pair(email, task_tag=tag, role="supervisor", conn=conn)
        else:
            print(f"⚠️ No person found with email: {email}")

    # Handle member assignment
    for email in member_emails:
        person_id = get_id_by_email(email=email, conn=conn)
        if person_id:
            insert_person_task_pair(email, task_tag=tag, role="member", conn=conn)
        else:
            print(f"⚠️ No person found with email: {email}")

    conn.commit()
    return True

def insert_person_task_pair(email: str, task_tag: str, role: str, conn: sqlite3.Connection) -> bool:
    """
    Inserts a new person-task assignment. Returns True if inserted, False otherwise.
    """
    if not conn:
        raise ValueError("conn must be provided")

    role = role.strip().lower()
    if role not in {"member", "supervisor"}:
        raise ValueError("role must be 'member' or 'supervisor'")

    person_id = get_id_by_email(email=email, conn=conn)
    if not person_id:
        print(f"⚠️ No person found with email: {email}")
        return False

    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    cur.execute("SELECT id FROM tasks WHERE tag = ?", (task_tag,))
    row = cur.fetchone()
    if not row:
        print(f"⚠️ No task found with tag: {task_tag}")
        return False
    task_id = row[0]

    try:
        cur.execute(
            "INSERT INTO task_assignments (person_id, task_id, role) VALUES (?, ?, ?)",
            (person_id, task_id, role)
        )
    except sqlite3.IntegrityError as e:
        print(f"❌ Insert failed: {e}")
        return False

    conn.commit()
    return True

def remove_person_task_pair(email: str, task_tag: str, conn: sqlite3.Connection) -> bool:
    """
    Removes a person-task-role assignment.
    Returns True if a row was deleted, False otherwise.
    """
    if not conn:
        raise ValueError("conn must be provided")

    person_id = get_id_by_email(email=email, conn=conn)
    if not person_id:
        print(f"⚠️ No person found with email: {email}")
        return False

    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    cur.execute("SELECT id FROM tasks WHERE tag = ?", (task_tag,))
    row = cur.fetchone()
    if not row:
        print(f"⚠️ No task found with tag: {task_tag}")
        return False
    task_id = row[0]

    cur.execute(
        "DELETE FROM task_assignments WHERE person_id = ? AND task_id = ?",
        (person_id, task_id)
    )

    if cur.rowcount == 0:
        print("ℹ️ No matching assignment found to remove.")
        return False

    conn.commit()
    return True

def get_id_by_email(email, conn):
    """
    Returns the person_id (integer) corresponding to the given email.
    Returns None if the email is not found.
    """
    if not email:
        raise ValueError("Email must be provided")

    cursor = conn.cursor()
    cursor.execute("SELECT id FROM people WHERE email = ?", (email,))
    result = cursor.fetchone()
    conn.commit()

    return result[0] if result else None

def list_people(conn: sqlite3.Connection) -> list[tuple[int, str, str]]:
    """
    Returns a list of tuples (id, name, email) for all people in the database.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email FROM people")
    people = cursor.fetchall()
    conn.commit()
    return people

from collections import OrderedDict
import sqlite3

def list_tasks_with_people(conn):
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

def list_people_with_tasks(conn):
    """
    Returns a list of (person_name, person_email, tasks)
    where tasks is a list of (title, tag). People with no tasks are included.
    """
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

    return people_tasks