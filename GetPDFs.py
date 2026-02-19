import streamlit as st
import os
import PyPDF2
import gspread
from google.oauth2.service_account import Credentials

# --- 1. AUTHENTICATION HELPER ---
def get_gspread_client():
    creds_info = st.secrets["gcp_service_account"]
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
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

# DEBUG: Let's see what folders exist on the server
st.sidebar.write("### Folders found in your repo:")
found_folders = [d for d in os.listdir('.') if os.path.isdir(d) and not d.startswith('.')]
st.sidebar.write(found_folders)

# User Input for Folder Path - Defaulting to 'Quotes'
folder_path = st.text_input("Folder Path (Case Sensitive)", value="Quotes")

if st.button("🚀 Start Extraction"):
    try:
        # Authenticate
        gc = get_gspread_client()
        sheet_id = "1BSA6lItqxS92NCAxrXoK6ey9AzNh1C3ExM98WTXqXo4"
        sh = gc.open_by_key(sheet_id)
        worksheet = sh.get_worksheet(0)

        # Check Folder
        if not os.path.exists(folder_path):
            st.error(f"Directory '{folder_path}' not found.")
            st.info(f"Available folders are: {found_folders}")
        else:
            files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
            
            if not files:
                st.warning(f"No PDF files found in '{folder_path}'.")
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
                
                status.text("Uploading to Google Sheets...")
                worksheet.append_rows(rows_to_add)
                st.success(f"✅ Successfully processed {len(files)} files!")
                
    except Exception as e:
        st.error(f"Critical Error: {e}")