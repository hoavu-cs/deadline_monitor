import Levenshtein
import sqlite3
from typing import Union, List, Tuple

LEVENSHTEIN_THRESHOLD = 3

def search_name(name: str = "", email: str = "", db_path: str = "") -> Union[Tuple[int, str, str], List[Tuple[int, str, str]], None]:
    if not db_path:
        raise ValueError("Database path must be provided")
    if not name:
        raise ValueError("Name must be provided")

    name = name.strip().lower()
    email = email.strip().lower()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    if email:
        cursor.execute("SELECT id, name, email FROM people WHERE LOWER(email) = ?", (email,))
    else:
        cursor.execute("SELECT id, name, email FROM people")

    entries = cursor.fetchall()
    conn.close()

    if not entries:
        return []

    matches = []
    for db_id, db_name, db_email in entries:
        db_name_lower = db_name.strip().lower()
        if Levenshtein.distance(name, db_name_lower) <= LEVENSHTEIN_THRESHOLD:
            matches.append((db_id, db_name, db_email))

    return matches


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