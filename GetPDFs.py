import streamlit as st
import os
import PyPDF2
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

# --- AUTHENTICATION ---
def get_gspread_client():
    creds_info = st.secrets["gcp_service_account"]
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_info, scopes=scope)
    return gspread.authorize(creds)

# --- THE MAPPING LOGIC ---
def parse_pdf_to_columns(file_path, headers):
    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        
        row = []
        for h in headers:
            import re
            pattern = re.escape(h) + r"[:\s]+([^\n]+)"
            match = re.search(pattern, text, re.IGNORECASE)
            row.append(match.group(1).strip() if match else "")
        return row
    except:
        return ["Error"] + [""] * (len(headers) - 1)

# --- MAIN APP ---
st.set_page_config(layout="wide")
st.title("📄 PDF to Structured Columns")

# --- SIDEBAR DIAGNOSTICS ---
st.sidebar.title("Debug Folder Explorer")
current_files = os.listdir(".")
st.sidebar.write("Root files/folders found:", current_files)

# Look specifically for a folder named Quotes (case-insensitive)
target_folder = None
for item in current_files:
    if item.lower() == "quotes" and os.path.isdir(item):
        target_folder = item

if target_folder:
    st.sidebar.success(f"Found folder: {target_folder}")
    all_pdfs = [os.path.join(target_folder, f) for f in os.listdir(target_folder) if f.lower().endswith(".pdf")]
    st.sidebar.write(f"PDFs found: {len(all_pdfs)}")
else:
    st.sidebar.error("Folder 'Quotes' not detected in root.")
    all_pdfs = []

# --- APP LOGIC ---
column_headers = [
    "Item", "Nett", "Gross", "Markup", "Hours (Repro)", 
    "Dubuit (Silkscreen positive)", "K9 (Silkscreen positive)", 
    "OMSOx1: 100 x 270 (Plate)", "OMSOx1: 135 x 270 (Plate)", 
    "PAD Print", "HKx1:100-120mm (155mm plate)", 
    "HKx1:130-150mm (183mm plate)", "HKx1:150-180mm (208mm plate)", 
    "Silkscreen", "Barcode", "PDF (Artwork)", 
    "DTP (Design and F/A)", "Pre-press for Tiff files", 
    "Epson proof / Chromalin", "Foil Block"
]

if not all_pdfs:
    st.warning("⚠️ No PDFs detected. Check the Sidebar for what the server sees.")
    st.info("If you just uploaded to GitHub, click 'Manage App' -> 'Reboot App' in the bottom right.")
else:
    if st.button("🔍 Step 1: Preview Data"):
        preview_data = [parse_pdf_to_columns(p, column_headers) for p in all_pdfs]
        st.session_state['extracted_data'] = preview_data
        df = pd.DataFrame(preview_data, columns=column_headers)
        st.dataframe(df)

    if 'extracted_data' in st.session_state:
        if st.button("📤 Step 2: Upload to Google Sheets"):
            gc = get_gspread_client()
            sh = gc.open_by_key("1BSA6lItqxS92NCAxrXoK6ey9AzNh1C3ExM98WTXqXo4")
            sh.sheet1.append_rows(st.session_state['extracted_data'])
            st.success("Uploaded!")