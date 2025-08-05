import sqlite3
import requests
import re

# Function to extract person information from natural language text
def extract_person_info(natural_text):
    prompt = f"""
            You are a helpful assistant. Extract the following person information from the prompt:

            Prompt:
            "{natural_text}"

            Format:
            Name: ...
            Email: ...

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
    name, email = None, None
    for line in lines:
        if line.lower().startswith("name:"):
            name = line.split(":", 1)[1].strip()
        elif line.lower().startswith("email:"):
            email = line.split(":", 1)[1].strip()
    return name, email

# Insert person into SQLite database
def insert_person(name, email):
    conn = sqlite3.connect("people.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO people (name, email) VALUES (?, ?)", (name, email))
    conn.commit()
    conn.close()

# Main function to run the script
if __name__ == "__main__":
    user_input = input("Enter a person to add (e.g., 'Add John Doe with email john@example.com'): ")
    result = extract_person_info(user_input)
    print("\n💬 Extracted info:\n", result)

    name, email = parse_output(result)

    if not name or not email:
        print("❌ Error: Could not extract both name and email.")
    else:
        insert_person(name, email)
        print(f"✅ Successfully added {name} ({email}) to the database.")
