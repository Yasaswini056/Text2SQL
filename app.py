import streamlit as st
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from huggingface_hub import login
import torch
import os
import sqlparse
from gsheet_utils import save_query_to_gsheet, save_feedback

# ===== Page Setup ===== #
st.set_page_config(page_title="Text2SQL - AI Query Generator", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
        ::placeholder {
        font-size: 15px !important;
        }
        textarea {
        resize: none !important;
        }
        @media (max-width: 768px) {
            .title-container h1 {
                font-size: 28px !important;
            }
            .title-container p {
                font-size: 14px !important;
            }
            ::placeholder {
            font-size: 14px !important;
            }
        }
    </style>
    <div class='title-container' style='text-align: center; margin-top: -60px; margin-bottom: 40px;'>
        <h1 style='color: #4CAF50; font-size: 40px; font-family:serif;'>🤖 Text2SQL - AI Query Generation System</h1>
        <p style='font-size: 18px; font-family:serif;color: gray;'>Convert natural language questions into SQL queries effortlessly!</p>
    </div>
""", unsafe_allow_html=True)

# ===== Session State ===== #
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ===== Load Model & Tokenizer ===== #
hf_token = st.secrets["hf_token"]["token"]
login(token=hf_token)

model_name = "Yasaswini056/CodeT5-Text2SQL"

tokenizer = AutoTokenizer.from_pretrained(model_name, token=hf_token)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name, token=hf_token)


with st.expander("🗣️ Feedback"):
    st.markdown(
        """
        <div style='margin-top: 5px;'>
            <h3 style='font-size:22px; color:#4CAF50; font-family:serif;'>Share Your Feedback</h3>
            <p style='font-size:16px; color:gray;'>We'd love to hear your suggestions or ideas to improve the system.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    feedback_text = st.text_area(
        label="✍️ Enter your feedback below:", 
        placeholder="Type your feedback here...", 
        key="general_feedback", 
        height=120
    )

    if st.button("✅ Submit Feedback", key="submit_general_feedback"):
        if feedback_text.strip():
            save_feedback(feedback_text.strip())  # Using 'General' as placeholder
            st.success("✅ Feedback submitted successfully!")
        else:
            st.warning("⚠️ Please enter some feedback before submitting.")


# ===== Layout Columns ===== #
left_col, right_col = st.columns([1.6, 2], gap="medium")

# ===== LEFT: Input Form ===== #
with left_col:
    st.subheader("📝 Enter Query Details")
    with st.form("query_form", clear_on_submit=True):
        table_schema_input = st.text_area("🗃️ Enter Table Schema * (comma-separated)", 
            placeholder="e.g. employees(id, name, salary), departments(dept_id, dept_name)", height=100)
        question = st.text_area("Enter your English question 👇")
        submitted = st.form_submit_button("🚀 Generate SQL")

    if submitted:
        question_stripped = question.strip()
        table_schema_stripped = table_schema_input.strip()
        
        if not question_stripped or not table_schema_stripped:
            st.warning("⚠️ Please enter both the table schema and the question.")
        else:
            input_text = f"tables: {table_schema_stripped}\nquestion: {question_stripped}"
            inputs = tokenizer(input_text, return_tensors="pt", truncation=True, padding=True).to(device)
            with torch.no_grad():
                outputs = model.generate(**inputs, max_new_tokens=128)
            generated_sql = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
            formatted_sql = sqlparse.format(generated_sql, reindent=True, keyword_case='upper')

            # Save query to Google Sheet
            save_query_to_gsheet(table_schema_stripped, question_stripped, formatted_sql)

            # Update Chat History
            st.session_state.chat_history.append({
                "question": question_stripped,
                "schema": table_schema_stripped,
                "sql": formatted_sql
            })

# ===== RIGHT: Chat History ===== #
with right_col:
    st.subheader("📜 Chat History")
    if not st.session_state.chat_history:
        st.markdown(
            """
            <div class='centered-placeholder'>
                <p style='color: #999999; font-style: italic; font-family:serif;font-size: 16px; text-align: center; margin-top:8rem;'>
                    No queries yet. Ask something to see SQL generated here.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        for chat in reversed(st.session_state.chat_history):
            with st.chat_message("user"):
                st.markdown(f"**You:** {chat['question']}")
                st.markdown(f"**Schema:** `{chat['schema']}`")
            with st.chat_message("assistant"):
                st.markdown("**SQL:**")
                st.code(chat["sql"], language="sql")



