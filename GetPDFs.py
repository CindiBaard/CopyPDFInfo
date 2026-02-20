import streamlit as st
import os
import PyPDF2
import gspread
import pandas as pd
import re
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
            # This regex looks for the heading and grabs the text following it
            pattern = re.escape(h) + r"[:\s]+([^\n]+)"
            match = re.search(pattern, text, re.IGNORECASE)
            row.append(match.group(1).strip() if match else "")
        return row
    except Exception as e:
        return [f"Error: {str(e)}"] + [""] * (len(headers) - 1)

# --- MAIN APP ---
st.set_page_config(layout="wide", page_title="PDF Data Extractor")
st.title("📄 PDF to Structured Columns")

# --- DYNAMIC FILE SEARCH ---
# This looks in the Root AND the Quotes folder automatically
# Change "." to your specific folder name
for root, dirs, files in os.walk("./Quotes"): 
    for file in files:
        if file.lower().endswith(".pdf"):
            all_pdfs.append(os.path.join(root, file))

st.sidebar.write(f"### 📁 System Status")
st.sidebar.write(f"Total PDFs detected: **{len(all_pdfs)}**")
if all_pdfs:
    st.sidebar.write("Files ready for processing ✅")

# --- COLUMN HEADERS ---
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

# --- STEPS ---
if not all_pdfs:
    st.error("No PDFs found. Please upload files to your GitHub repository.")
else:
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 Step 1: Preview Data"):
            with st.spinner("Reading PDFs..."):
                preview_data = [parse_pdf_to_columns(p, column_headers) for p in all_pdfs]
                st.session_state['extracted_data'] = preview_data
                df = pd.DataFrame(preview_data, columns=column_headers)
                st.write("### Preview of Extracted Data")
                st.dataframe(df)

    with col2:
        if 'extracted_data' in st.session_state:
            if st.button("📤 Step 2: Push to Google Sheets"):
                try:
                    with st.spinner("Connecting to Google Sheets..."):
                        gc = get_gspread_client()
                        sh = gc.open_by_key("1BSA6lItqxS92NCAxrXoK6ey9AzNh1C3ExM98WTXqXo4")
                        worksheet = sh.get_worksheet(0)
                        worksheet.append_rows(st.session_state['extracted_data'])
                        st.success(f"✅ Successfully added {len(all_pdfs)} rows to your Spreadsheet!")
                except Exception as e:
                    st.error(f"Google Sheets Error: {e}")