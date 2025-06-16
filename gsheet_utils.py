import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import json
import streamlit as st

# 🔐 Setup GSheet access
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gsheets"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# 📄 Open the spreadsheet and worksheets
spreadsheet = client.open("Text2SQL_Logs")
query_ws = spreadsheet.get_worksheet(0)   # Sheet1
feedback_ws = spreadsheet.get_worksheet(1) # Sheet2

# ✏️ Function to save query logs
def save_query_to_gsheet(schema, question, generated_sql):
    try:
        query_ws.append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), schema, question, generated_sql])
    except Exception as e:
        st.error(f"Error logging query: {e}")

def save_feedback(user_feedback):
    try:
        feedback_ws.append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  user_feedback])
    except Exception as e:
        st.error(f"Error logging feedback: {e}")
