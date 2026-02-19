import streamlit as st
import os
import PyPDF2
import gspread
from google.oauth2.service_account import Credentials

# --- 1. AUTHENTICATION HELPER ---
def get_gspread_client():
    # Looks for [gcp_service_account] section in secrets.toml
    creds_info = st.secrets["gcp_service_account"]
    
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # Create credentials from the secrets dictionary
    creds = Credentials.from_service_account_info(creds_info, scopes=scope)
    return gspread.authorize(creds)

# --- 2. TEXT EXTRACTION HELPER ---
def extract_text(file_path):
    text = ""
    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                content = page.extract_text()
                if content:
                    text += content + "\n"
        return text.strip()
    except Exception as e:
        return f"Error: {str(e)}"

# --- 3. STREAMLIT INTERFACE ---
st.set_page_config(page_title="PDF to Sheets", page_icon="📄")
st.title("📄 PDF to Google Sheets Porter")

# User Input for Folder Path
folder_path = st.text_input("Folder Path", value="New folder(3)")

if st.button("🚀 Start Extraction"):
    try:
        # Authenticate
        gc = get_gspread_client()
        sheet_id = "1BSA6lItqxS92NCAxrXoK6ey9AzNh1C3ExM98WTXqXo4"
        sh = gc.open_by_key(sheet_id)
        worksheet = sh.get_worksheet(0)

        # Check Folder
        if not os.path.exists(folder_path):
            st.error(f"Directory '{folder_path}' not found. Ensure it is in the same folder as this script.")
        else:
            files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
            
            if not files:
                st.warning("No PDF files found.")
            else:
                progress_bar = st.progress(0)
                status = st.empty()
                
                rows_to_add = []
                for i, filename in enumerate(files):
                    status.text(f"Reading: {filename}")
                    full_path = os.path.join(folder_path, filename)
                    
                    content = extract_text(full_path)
                    rows_to_add.append([filename, content])
                    
                    progress_bar.progress((i + 1) / len(files))
                
                # Bulk update to Sheets is faster than append_row in a loop
                status.text("Uploading to Google Sheets...")
                worksheet.append_rows(rows_to_add)
                
                st.success(f"✅ Successfully processed {len(files)} files!")
                
    except Exception as e:
        st.error(f"Critical Error: {e}")
        st.info("💡 Tip: Make sure you shared the Google Sheet with your service account email as an 'Editor'.")