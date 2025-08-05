import sqlite3
import requests
import re

OLLAMA_MODEL = "llama3"
OLLAMA_URL = "http://localhost:11434/api/generate"

def query_ollama(prompt: str) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
    )
    if response.status_code != 200:
        raise RuntimeError(f"Ollama error: {response.text}")
    return response.json()["response"]

def classify_command(user_input: str) -> str:
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
            You are an assistant that extracts structured task information.

            Given the input text, return ONLY the following fields in this exact format:

            Title: <short task title>
            Description: <brief description of the task>
            Deadline: <deadline in YYYY-MM-DD format>

            Do not include any explanation, extra lines, or labels.

            Text:
            {text}
            """

    output = query_ollama(prompt)
    title, desc, deadline = None, None, None
    for line in output.splitlines():
        if line.lower().startswith("title:"):
            title = line.split(":", 1)[1].strip()
        elif line.lower().startswith("description:"):
            desc = line.split(":", 1)[1].strip()
        elif line.lower().startswith("deadline:"):
            deadline = line.split(":", 1)[1].strip()
    return title, desc, deadline

def insert_person(name, email):
    if not name or not email:
        print("❌ Missing name or email. Person not added.")
        return
    conn = sqlite3.connect("people.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO people (name, email) VALUES (?, ?)", (name, email))
    conn.commit()
    conn.close()
    print(f"✅ Person added: {name} ({email})")

def insert_task(title, description, deadline):
    if not title or not description or not deadline:
        print("❌ Missing one or more task fields. Task not added.")
        return
    conn = sqlite3.connect("people.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (title, description, deadline) VALUES (?, ?, ?)",
                   (title, description, deadline))
    conn.commit()
    conn.close()
    print(f"✅ Task added: Title: {title}, Description: {description}, Deadline: {deadline}")

# ---- MAIN LOOP ----
if __name__ == "__main__":
    user_input = input("💬 Enter a command for the agent: ").strip()
    intent = classify_command(user_input)
    print(f"🤖 Classified intent: {intent}")

    if intent == "add_person":
        name, email = extract_person_fields(user_input)
        insert_person(name, email)

    elif intent == "add_task":
        title, desc, deadline = extract_task_fields(user_input)
        insert_task(title, desc, deadline)

    else:
        print("🤖 I’m not sure what you’re asking. Please clarify.")
