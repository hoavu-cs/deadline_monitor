import sqlite3
import re
import os
from dotenv import load_dotenv
from datetime import datetime
from openai import OpenAI

# -------------------------
# CONFIG
# -------------------------
DB_PATH = "database/my_db.db"

# Load variables for the DeepSeek API
load_dotenv()

# Create a client for the DeepSeek API
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),  # no hardcoded key
    base_url="https://api.deepseek.com"
)

def query_deepseek(prompt: str, model: str = "deepseek-chat") -> str:
    """
    Send a prompt to DeepSeek and return the response content.
    """
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a SQLite expert. Return only SQL when asked."},
            {"role": "user", "content": prompt},
        ],
        stream=False
    )
    return response.choices[0].message.content.strip()

# -------------------------
# DB Schema introspection
# -------------------------
def introspect_schema_text(db_path: str) -> str:
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        ddls = [row[1] for row in cur.fetchall() if row[1]]
        return "\n\n".join(ddls)
    finally:
        conn.close()

# -------------------------
# Generate SQL with Llama
# -------------------------
def generate_sql_with_llm(nl_query: str, schema_text: str) -> str:
    prompt = f"""
You are a SQLite expert. Using ONLY the tables and columns below, write ONE SQLite query that answers the question.

Special rule for creating tasks:
- If the query is INSERT INTO tasks, you MUST always include a 'tag' column in the column list.
- The tag must be lowercase, start with '#', have no spaces, and be based on the title with a random 4-digit number appended.
  Example: title 'World Bank report' -> tag '#worldbank4821'
- Place the generated tag in the VALUES clause when inserting the task.
- Default importance is 3, and completed is FALSE.
- If a person's email is not provided, output an error message: "❌ Error: Email is required for task assignment." and do not execute the query.

Special rule for adding people:
- If the query is INSERT INTO people, the VALUES must include a non-empty email address containing '@'.

Do not modify column/table names. Use SQLite date functions (e.g., DATE('now')) when needed.
Return ONLY the SQL. No markdown, no backticks, no commentary.

Schema:
{schema_text}

Question: {nl_query}
SQL:
"""
    raw = query_deepseek(prompt)
    sql = re.sub(r"^```(?:sql)?\s*|\s*```$", "", raw.strip(), flags=re.IGNORECASE)
    sql = sql.split(";")[0].strip()
    return sql


# -------------------------
# SQL execution
# -------------------------
def run_sql(sql: str, db_path: str = DB_PATH):
    """
    Execute any SQL statement (read or write).
    Returns (headers, rows/message).
    """
    conn = sqlite3.connect(db_path)  # normal read/write connection
    try:
        cur = conn.cursor()
        cur.execute(sql)

        if cur.description:  # SELECT or something that returns rows
            rows = cur.fetchall()
            headers = [d[0] for d in cur.description]
            return headers, rows
        else:
            conn.commit()
            return None, f"{cur.rowcount} row(s) affected"
    finally:
        conn.close()

# -------------------------
# Pretty-print results
# -------------------------
def print_table(headers, rows):
    if not headers:
        print("(query executed, no tabular output)")
        return
    if not rows:
        print("(no rows)")
        return
    widths = [max(len(str(h)), *(len(str(r[i])) for r in rows)) for i, h in enumerate(headers)]
    header_line = " | ".join(f"{h:<{widths[i]}}" for i, h in enumerate(headers))
    sep_line    = "-+-".join("-" * w for w in widths)
    print(header_line)
    print(sep_line)
    for r in rows:
        print(" | ".join(f"{str(v):<{widths[i]}}" for i, v in enumerate(r)))

# -------------------------
# Main loop
# -------------------------
def main():
    schema_text = introspect_schema_text(DB_PATH)
    print("Natural Language SQL Agent (type 'exit' to quit)")
    while True:
        nl_query = input("\n💬 Enter your query: ").strip()
        if not nl_query or nl_query.lower() in {"exit", "quit"}:
            print("👋 Goodbye.")
            break
        try:
            sql = generate_sql_with_llm(nl_query, schema_text)
            print(f"\nGenerated SQL:\n{sql}\n")
            
            headers, result = run_sql(sql, DB_PATH)  # <-- use the new read/write run_sql
            if headers:  # SELECT or something returning rows
                print_table(headers, result)
            else:  # INSERT/UPDATE/DELETE
                print(result)
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
