import streamlit as st
import pandas as pd
import sqlite3
from sql_agent import introspect_schema_text, generate_sql_with_llm, run_sql, DB_PATH

st.set_page_config(layout="wide")

# Helper to fetch any table
def get_table(table_name):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    if table_name == "task_assignments":
        cur.execute("""
            SELECT p.email, t.tag AS tag, a.role
            FROM task_assignments a
            JOIN people p ON a.person_id = p.id
            JOIN tasks t ON a.task_id = t.id
        """)
    else:
        cur.execute(f"SELECT * FROM {table_name}")

    data = cur.fetchall()
    headers = [desc[0] for desc in cur.description]
    conn.close()
    return pd.DataFrame(data, columns=headers)


# Load schema once
if "schema_text" not in st.session_state:
    st.session_state.schema_text = introspect_schema_text(DB_PATH)

st.title("Halcom Agent")

# Form allows Enter to submit
with st.form("query_form"):
    nl_query = st.text_area("💬 Enter your query:", height=100)  # ~5 lines tall
    submitted = st.form_submit_button("Run Query")  # Ctrl+Enter to submit


if submitted and nl_query:
    try:
        sql = generate_sql_with_llm(nl_query, st.session_state.schema_text)
        st.subheader("Generated SQL")
        st.code(sql, language="sql")

        headers, result = run_sql(sql, DB_PATH)

        if headers:  # SELECT
            df = pd.DataFrame(result, columns=headers)
            st.subheader("Query Results")
            st.dataframe(df, use_container_width=True)
        else:
            st.success(result)

    except Exception as e:
        st.error(f"❌ Error: {e}")

# Always show the three key tables at the bottom
st.markdown("---")
st.subheader("📋 Database Snapshot")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**People**")
    st.dataframe(get_table("people"), use_container_width=True)

with col2:
    st.markdown("**Tasks**")
    st.dataframe(get_table("tasks"), use_container_width=True)

with col3:
    st.markdown("**Task Assignments**")
    st.dataframe(get_table("task_assignments"), use_container_width=True)
