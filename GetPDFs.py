import streamlit as st
import os
import PyPDF2
import gspread
from google.oauth2 import service_account

# --- STEP 1: AUTHENTICATION ---
def get_gspread_client():
    # Access the dictionary under the [gcp_service_account] header
    creds_info = st.secrets["gcp_service_account"]
    
    # Scope for Google Sheets and Drive
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # Create credentials object
    creds = service_account.Credentials.from_service_account_info(creds_info, scopes=scope)
    return gspread.authorize(creds)

# --- STEP 2: PDF EXTRACTION ---
def extract_text_from_pdf(file_path):
    text = ""
    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                content = page.extract_text()
                if content:
                    text += content + "\n"
    except Exception as e:
        return f"Error reading {file_path}: {e}"
    return text

# --- STEP 3: MAIN APP ---
st.title("📄 PDF to Google Sheets Porter")

if st.button("Start Extraction"):
    try:
        # Initialize Google Sheet
        gc = get_gspread_client()
        sheet_id = "1BSA6lItqxS92NCAxrXoK6ey9AzNh1C3ExM98WTXqXo4"
        sh = gc.open_by_key(sheet_id)
        worksheet = sh.get_worksheet(0) # Targets the first tab

        folder_name = "New folder(3)"
        
        if not os.path.exists(folder_name):
            st.error(f"Folder '{folder_name}' not found. Please ensure it is in the root directory.")
        else:
            pdf_files = [f for f in os.listdir(folder_name) if f.endswith('.pdf')]
            
            if not pdf_files:
                st.warning("No PDF files found in the folder.")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, filename in enumerate(pdf_files):
                    status_text.text(f"Processing: {filename}")
                    path = os.path.join(folder_name, filename)
                    
                    # Extract text
                    content = extract_text_from_pdf(path)
                    
                    # Append to Sheet (Filename in Col A, Content in Col B)
                    worksheet.append_row([filename, content])
                    
                    # Update progress
                    progress_bar.progress((i + 1) / len(pdf_files))
                
                st.success(f"Done! Processed {len(pdf_files)} files.")
                
    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.info("Check if you shared the sheet with the client_email in your secrets.")
Critical Final Checklist: