# deepseek_prompt.py

import requests

import requests

def generate_task(task_string):
    prompt = f"""
        You are a helpful assistant. Extract the following structured task information from the prompt below:

        Fields:
        - Description
        - People
        - Supervisor
        - Deadline
        
        Prompt:
        "{task_string}"
        Format the output like:
        Description: ...
        People: ...
        Supervisor: ...
        Deadline: ...
        """

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",  # Updated from deepseek-coder
            "prompt": prompt,
            "stream": False
        }
    )

    if response.status_code != 200:
        raise RuntimeError(f"Error from Ollama: {response.text}")

    return response.json()["response"]


if __name__ == "__main__":
    user_input = input("Enter a prompt: ")
    output = generate_task(user_input)
    print("\n💬 Agent says:\n", output)
