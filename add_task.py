import sqlite3
import requests
import re

# Function to extract person information from natural language text
def extract_person_info(natural_text):
    prompt = f"""
            You are a helpful assistant. Extract the following task information from the prompt:

            Prompt:
            "{natural_text}"

            Format:
            Task: ...
            Description: ...

            Only return the structured fields.
            """

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
    )

    if response.status_code != 200:
        raise RuntimeError(f"Error from Ollama: {response.text}")

    return response.json()["response"]

# Parse output using regex or line splitting
def parse_output(output):
    lines = output.strip().splitlines()
    title, description = None, None
    for line in lines:
        if line.lower().startswith("title:"):
            title = line.split(":", 1)[1].strip()
        elif line.lower().startswith("description:"):
            description = line.split(":", 1)[1].strip()
    return title, description

# Insert task into SQLite database
def insert_task(title, description):
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (title, description) VALUES (?, ?)", (title, description))
    conn.commit()
    conn.close()

# Main function to run the script
if __name__ == "__main__":
    user_input = input("Enter a task to add (e.g., 'Add task to review code with description of the task'): ")
    result = extract_person_info(user_input)
    print("\n💬 Extracted info:\n", result)
    task, description = parse_output(result)
    
    if task and description:
        insert_task(task, description)
        print(f"Task '{task}' added successfully! ✅")
    else:
        print("❌ Error: Could not extract both task and description.")