import sqlite3
import requests
import re
import random
from my_package.db_queries import get_id_by_email

OLLAMA_MODEL = "llama3"
OLLAMA_URL = "http://localhost:11434/api/generate"

def query_ollama(prompt: str):
    response = requests.post(
        OLLAMA_URL,
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
    )
    if response.status_code != 200:
        raise RuntimeError(f"Ollama error: {response.text}")
    return response.json()["response"]

def classify_command(user_input: str):
    prompt = f"""
            Classify the following command into one of: 'add_person', 'add_task', or 'other'.
            Command: "{user_input}"
            Answer with one word only.
            """
    return query_ollama(prompt).strip("'\"").lower()

def extract_person_fields(text):
    prompt = f"""
            Extract the following fields from the text below.

            Return output **only** in the following format:
            Name: <full name>
            Email: <email address>

            Do not include explanations, comments, or extra lines.

            Text:
            {text}
            """

    output = query_ollama(prompt)
    name, email = None, None
    for line in output.splitlines():
        if line.lower().startswith("name:"):
            name = line.split(":", 1)[1].strip()
        elif line.lower().startswith("email:"):
            email = line.split(":", 1)[1].strip()
    return name, email

def extract_task_fields(text):
    prompt = f"""
            You are an assistant that extracts structured task information from the following input.

            Return ONLY the fields in this exact format:
            Title: <short task title>
            Description: <brief description of the task>
            Deadline: <deadline in YYYY-MM-DD format>
            Supervisor Emails: <comma-separated list of supervisor emails>
            Member Emails: <comma-separated list of task member emails>

            Do not include any explanation or extra lines.

            Text:
            {text}
            """

    output = query_ollama(prompt)
    
    title = desc = deadline = None
    supervisor_emails = []
    member_emails = []

    for line in output.splitlines():
        if line.lower().startswith("title:"):
            title = line.split(":", 1)[1].strip()
        elif line.lower().startswith("description:"):
            desc = line.split(":", 1)[1].strip()
        elif line.lower().startswith("deadline:"):
            deadline = line.split(":", 1)[1].strip()
        elif line.strip().lower().startswith("supervisor emails:"):
            supervisor_emails = [s.strip() for s in line.split(":", 1)[1].split(",") if s.strip()]
        elif line.strip().lower().startswith("member emails:"):
            member_emails = [m.strip() for m in line.split(":", 1)[1].split(",") if m.strip()]

    print(f"{output}")
    return title, desc, deadline, supervisor_emails, member_emails

def insert_person(name, email):
    if not name or not email:
        print("❌ Missing name or email. Person not added.")
        return
    try:
        conn = sqlite3.connect("people.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO people (name, email) VALUES (?, ?)", (name, email))
        conn.commit()
        print(f"✅ Person added: {name} ({email})")
    except sqlite3.IntegrityError:
        print(f"❌ Email {email} already exists. Person not added.")
    finally:
        conn.close()

def assign_person_to_task(conn, person_id, task_id, role):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO task_assignments (person_id, task_id, role) VALUES (?, ?, ?)",
        (person_id, task_id, role)
    )
    print(f"✅ Assigned person {person_id} to task {task_id} as {role}")

def generate_tag_with_llama(title: str) -> str:
    prompt = f"""
    Generate a lowercase tag based on the task title.
    - Use short keywords from the title (lowercase, no punctuation)
    - Add 2 random digits at the end to ensure uniqueness
    - Do not include quotes, punctuation, or explanations

    Title: {title}
    Tag:
    """
    tag_base = query_ollama(prompt).strip().replace(" ", "_")
    random_digits = f"{random.randint(0, 99):02d}"
    return f"#{tag_base}{random_digits}"

def insert_task(title, description, deadline, supervisor_emails, member_emails):
    if not title or not description or not deadline:
        print("❌ Missing one or more task fields. Task not added.")
        return

    conn = sqlite3.connect("people.db")
    cursor = conn.cursor()
    generated_tag = generate_tag_with_llama(title)

    # Insert the task
    cursor.execute("INSERT INTO tasks (title, description, deadline, tag) VALUES (?, ?, ?, ?)", (title, description, deadline, generated_tag))
    conn.commit()

    # Get task ID
    cursor.execute("SELECT id FROM tasks WHERE title = ?", (title,))
    result = cursor.fetchone()

    if not result:
        print("❌ Could not find task after insertion.")
        conn.close()
        return 

    task_id = result[0]
    print(f"✅ Task added: Title: {title}, Description: {description}, Deadline: {deadline}, Tag: {generated_tag}")

    # Handle supervisor assignment
    for email in supervisor_emails:
        person_id = get_id_by_email(email=email, db_path="people.db")
        if person_id:
            assign_person_to_task(conn, person_id, task_id, "supervisor")
        else:
            print(f"⚠️ No person found with email: {email}")

    # Handle member assignment
    for email in member_emails:
        person_id = get_id_by_email(email=email, db_path="people.db")
        if person_id:
            assign_person_to_task(conn, person_id, task_id, "member")
        else:
            print(f"⚠️ No person found with email: {email}")

    conn.commit()
    conn.close()

# ---- MAIN LOOP ----
if __name__ == "__main__":
    print("🧠 Agent is ready. Type 'exit' or 'quit' to stop.\n")
    
    while True:
        user_input = input("💬 Enter a command for the agent: ").strip()
        if user_input.lower() in {"exit", "quit", "bye"}:
            print("👋 Exiting. Goodbye!")
            break

        intent = classify_command(user_input)
        print(f"🤖 Classified intent: {intent}")

        if intent == "add_person":
            name, email = extract_person_fields(user_input)
            insert_person(name, email)

        elif intent == "add_task":
            title, desc, deadline, supervisor_emails, member_emails = extract_task_fields(user_input)
            insert_task(title, desc, deadline, supervisor_emails, member_emails)

        else:
            print("🤖 I’m not sure what you’re asking. Please clarify.")

