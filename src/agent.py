import sqlite3
import requests
import re
import random
from db_queries import *

OLLAMA_MODEL = "llama3"
OLLAMA_URL = "http://localhost:11434/api/generate"

# ===== Function Signatures =====

def query_ollama(prompt: str) -> str:
    """Send prompt to Ollama API and return the generated response."""

def classify_command(user_input: str) -> str:
    """Classify a user command into one of the predefined intents."""

def extract_person_fields(text: str) -> tuple[str | None, str | None]:
    """Extract 'Name' and 'Email' from text."""

def extract_task_fields(text: str) -> tuple[
    str | None, str | None, str | None, list[str], list[str], int
]:
    """Extract task fields including title, description, deadline, emails, and importance."""

def extract_person_task_fields(text: str) -> tuple[str | None, str | None, str | None]:
    """Extract email, task tag, and role (supervisor/member) from text."""

def extract_person_task_fields_for_deletions(text: str) -> tuple[str | None, str | None]:
    """Extract email and task tag for deletion commands."""

def generate_tag_with_llama(title: str) -> str:
    """Generate a lowercase, unique task tag from a title."""

# ===== Function Implementations =====

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
            Classify the following command into one of: 'add_person', 'add_task', 'display_tasks', \
                                                        'display_people', 'add_person_to_task', \
                                                        'remove_person_from_task', or 'other'.
            Command: "{user_input}"
            

            Constraints:
            - Answer with one word only.
            - The response must be in one of the listed intents.
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
            Importance: <importance level from 1 to 5>

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
        elif line.strip().lower().startswith("importance:"):
            importance = line.split(":", 1)[1].strip()
            if importance.isdigit() and 1 <= int(importance) <= 5:
                importance = int(importance)
            else:
                importance = 3

    print(f"{output}")
    return title, desc, deadline, supervisor_emails, member_emails, importance

def extract_person_task_fields(text):
    prompt = f"""
            Extract the following fields from the text below.

            Return output **only** in the following format:
            Email: <email address>
            Task Tag: <task tag>
            Role: <role>

            Constraints:
            - Role must be exactly one of: "supervisor" or "member".
            - If role is unclear or missing, choose the most likely one but still output only "supervisor" or "member".
            - Do not output anything except the three lines above.
            - Do not modify or remove the '#' symbol from the Task Tag.

            Text:
            {text}
            """

    output = query_ollama(prompt)
    email = task_tag = role = None

    for line in output.splitlines():
        if line.lower().startswith("email:"):
            email = line.split(":", 1)[1].strip()
        elif line.lower().startswith("task tag:"):
            task_tag = line.split(":", 1)[1].strip()
        elif line.lower().startswith("role:"):
            role = line.split(":", 1)[1].strip()
        
    return email, task_tag, role

def extract_person_task_fields_for_deletions(text):
    prompt = f"""
            Extract the following fields from the text below.

            Return output **only** in the following format:
            Email: <email address>
            Task Tag: <task tag>

            Constraints:
            - Do not modify or remove the '#' symbol from the Task Tag.

            Text:
            {text}
            """

    output = query_ollama(prompt)
    email = task_tag = None

    for line in output.splitlines():
        if line.lower().startswith("email:"):
            email = line.split(":", 1)[1].strip()
        elif line.lower().startswith("task tag:"):
            task_tag = line.split(":", 1)[1].strip()

    return email, task_tag

def generate_tag_with_llama(title: str):
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
            conn = sqlite3.connect("database/my_db.db")
            result = insert_person(name, email, conn)
            if result:
                print(f"✅ Person added: {name} ({email})")
            else:
                print(f"❌ Failed to add person: {name} ({email})")
            conn.close()

        elif intent == "add_task":
            title, desc, deadline, supervisor_emails, member_emails, importance = extract_task_fields(user_input)
            tag = generate_tag_with_llama(title)
            conn = sqlite3.connect("database/my_db.db")
            result = insert_task(title, desc, deadline, tag, supervisor_emails, member_emails, importance, conn)
            if result:
                print(f"✅ Task added: {title} (Tag: {tag})")
            else:
                print(f"❌ Failed to add task: {title} (Tag: {tag})")
            conn.close()

        elif intent == "add_person_to_task":
            email, task_tag, role = extract_person_task_fields(user_input)
            conn = sqlite3.connect("database/my_db.db")
            result = insert_person_task_pair(email, task_tag, role, conn=conn)
            if result:
                print(f"✅ Added {role} with email {email} to task with tag {task_tag}")
            else:
                print(f"❌ Failed to add {role} with email {email} to task with tag {task_tag}")
            conn.close()

        elif intent == "remove_person_from_task":
            email, task_tag = extract_person_task_fields_for_deletions(user_input)
            conn = sqlite3.connect("database/my_db.db")
            result = remove_person_task_pair(email, task_tag, conn=conn)
            if result:
                print(f"✅ Removed email {email} from task with tag {task_tag}")
            else:
                print(f"❌ Failed to remove email {email} from task with tag {task_tag}")
            conn.close()

        elif intent == "display_tasks":
            print("📋 Current task assignments:")
            conn = sqlite3.connect("database/my_db.db")
            assignments = list_tasks_with_people(conn=conn)
            for a in assignments.values():
                print(f"** Title: {a['title']}, Description: {a['description']}, Tag: {a['tag']}, Importance: {a['importance']}")
                for role, person in a["people"]:
                    print(f"  - {person} ({role})")
            conn.close()

        elif intent == "display_people":
            print("👥 Current people in the database:")
            conn = sqlite3.connect("database/my_db.db")
            people_tasks = list_people_with_tasks(conn=conn)
            for person_id, info in people_tasks.items():
                print(f"** {info['name']} <{info['email']}> has tasks:")
                for title, tag, role in info["tasks"]:
                    print(f"  - {title} (Tag: {tag}, Role: {role})")
            conn.close()

        else:
            print("🤖 I’m not sure what you’re asking. Please clarify.")

