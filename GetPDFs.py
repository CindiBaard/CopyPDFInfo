import streamlit as st
import os
import PyPDF2
import gspread
import pandas as pd
import re
from google.oauth2.service_account import Credentials

# --- AUTHENTICATION ---
def get_gspread_client():
    try:
        creds_info = st.secrets["gcp_service_account"]
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"⚠️ Authentication Error: {e}")
        return None

# --- THE MAPPING LOGIC ---
def parse_pdf_to_columns(pdf_path, headers):
    try:
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        
        row = []
        filename = os.path.basename(pdf_path)
        
        for h in headers:
            if h == "Item":
                row.append(filename)
                continue
            
            # Regex captures the last price/number on the line for that header
            pattern = re.escape(h) + r".*?([\d,]+\.\d{2})\s*$"
            match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
            
            if match:
                val = match.group(1).replace(",", "") 
                row.append(val)
            else:
                row.append("")
        return row
    except Exception as e:
        return [f"Error: {str(e)}"] + [""] * (len(headers) - 1)

# --- MAIN APP ---
st.set_page_config(layout="wide", page_title="PDF Data Extractor")
st.title("📄 PDF to Structured Columns")

# --- DYNAMIC FILE SEARCH ---
all_pdfs = []
target_path = "./Files/Quotes"
search_root = target_path if os.path.exists(target_path) else "."

for root, dirs, files in os.walk(search_root):
    dirs[:] = [d for d in dirs if not d.startswith('.')]
    for file in files:
        if file.lower().endswith(".pdf"):
            all_pdfs.append(os.path.join(root, file))

# --- SIDEBAR STATUS ---
st.sidebar.header("📁 System Status")
st.sidebar.write(f"Total PDFs: **{len(all_pdfs)}**")

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
    st.info("No PDFs found in Files/Quotes.")
else:
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 Step 1: Preview Data"):
            with st.spinner("Processing..."):
                preview_data = [parse_pdf_to_columns(p, column_headers) for p in all_pdfs]
                st.session_state['extracted_data'] = preview_data
                df = pd.DataFrame(preview_data, columns=column_headers)
                st.write("### Preview of Extracted Data")
                st.dataframe(df)

    with col2:
        if 'extracted_data' in st.session_state:
            if st.button("📤 Step 2: Push New Data Only"):
                try:
                    with st.spinner("Checking for duplicates in Google Sheets..."):
                        gc = get_gspread_client()
                        if gc:
                            sh = gc.open_by_key("1BSA6lItqxS92NCAxrXoK6ey9AzNh1C3ExM98WTXqXo4")
                            worksheet = sh.get_worksheet(0)
                            
                            # 1. Get all existing "Item" names (Column A)
                            existing_items = worksheet.col_values(1) 
                            
                            # 2. Filter out data that already exists
                            to_upload = []
                            skipped_count = 0
                            for row in st.session_state['extracted_data']:
                                if row[0] not in existing_items:
                                    to_upload.append(row)
                                else:
                                    skipped_count += 1
                            
                            # 3. Upload only unique rows
                            if to_upload:
                                worksheet.append_rows(to_upload)
                                st.success(f"✅ Added {len(to_upload)} new rows!")
                            
                            if skipped_count > 0:
                                st.info(f"ℹ️ Skipped {skipped_count} files that were already in the sheet.")
                            elif not to_upload:
                                st.warning("No new data to upload.")
                                
                except Exception as e:
                    st.error(f"Google Sheets Error: {e}")

# --- RESET ---
if st.sidebar.button("Clear Cache"):
    st.session_state.clear()
    st.rerun()