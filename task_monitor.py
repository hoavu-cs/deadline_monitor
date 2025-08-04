import sqlite3
import requests

def extract_task_info(prompt):
    system_prompt = f"""
Extract the following fields from this task instruction:
- project_name (e.g., "Project X")
- due_date (format: YYYY-MM-DD)
- task_type (e.g., "report", "review", "meeting")
- description (the full sentence)

Return valid JSON with keys: project_name, due_date, task_type, description.
Task: "{prompt}"
"""
    r = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "deepseek-coder:instruct",
            "prompt": system_prompt,
            "stream": False
        }
    )
    return r.json()["response"]

def insert_into_db(data):
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT,
        project_name TEXT,
        due_date DATE,
        task_type TEXT,
        status TEXT DEFAULT 'pending'
    )""")
    cursor.execute(
        "INSERT INTO tasks (description, project_name, due_date, task_type) VALUES (?, ?, ?, ?)",
        (data["description"], data["project_name"], data["due_date"], data["task_type"])
    )
    conn.commit()
    conn.close()

# Full pipeline
if __name__ == "__main__":
    user_input = input("Enter a task: ")
    response = extract_task_info(user_input)

    # Safe parsing of JSON from LLM
    import json
    try:
        parsed = json.loads(response)
        insert_into_db(parsed)
        print("✅ Task inserted successfully.")
    except Exception as e:
        print("❌ Failed to parse or insert task:", e)
        print("LLM response was:", response)
