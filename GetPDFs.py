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
        st.error(f"⚠️ Authentication Error: Check your Streamlit Secrets. {e}")
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
        # Get the filename to use as the "Item" identifier
        filename = os.path.basename(pdf_path)
        
        for h in headers:
            if h == "Item":
                row.append(filename)
                continue
            
            # This regex looks for the Header name, ignores middle text, 
            # and captures the LAST number/currency at the end of that specific line.
            # Example: "Hours (Repro) 1 1,027.35 1,027.35" -> Captures "1,027.35"
            pattern = re.escape(h) + r".*?([\d,]+\.\d{2})\s*$"
            match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
            
            if match:
                val = match.group(1).replace(",", "") # Remove commas for clean math in Sheets
                row.append(val)
            else:
                row.append("")
        return row
    except Exception as e:
        return [f"Error: {str(e)}"] + [""] * (len(headers) - 1)

# --- MAIN APP CONFIG ---
st.set_page_config(layout="wide", page_title="PDF Data Extractor")
st.title("📄 PDF to Structured Columns")

# --- DYNAMIC FILE SEARCH ---
all_pdfs = []
# Based on your structure: Files/Quotes
target_path = "./Files/Quotes"

# Use the specific folder if it exists, otherwise scan root
search_root = target_path if os.path.exists(target_path) else "."

for root, dirs, files in os.walk(search_root):
    # Prune hidden folders to avoid the "9,000 files" system junk
    dirs[:] = [d for d in dirs if not d.startswith('.')]
    for file in files:
        if file.lower().endswith(".pdf"):
            all_pdfs.append(os.path.join(root, file))

# --- SIDEBAR STATUS ---
st.sidebar.header("📁 System Status")
st.sidebar.write(f"Scanning: `{search_root}`")
st.sidebar.write(f"Total PDFs: **{len(all_pdfs)}**")

if all_pdfs:
    with st.sidebar.expander("Show found files"):
        for p in sorted(all_pdfs):
            st.write(os.path.basename(p))
else:
    st.sidebar.warning("No PDFs found in Files/Quotes.")

# --- COLUMN HEADERS ---
column_headers = [
    "Item", "Client", "Description", "Preprod Ref", "Total", "Vat (15%)", "Grand Total", "Hours (Repro)", 
    "Dubuit (Silkscreen positive)", "K9 (Silkscreen positive)", 
    "OMSOx1: 100 x 270 (Plate)", "OMSOx1: 135 x 270 (Plate)", 
    "PAD Print", "HKx1:100-120mm (155mm plate)", 
    "HKx1:130-150mm (183mm plate)", "HKx1:150-180mm (208mm plate)", 
    "Silkscreen", "Barcode", "PDF (Artwork)", 
    "DTP (Design and F/A)", "Pre-press for Tiff files", 
    "Epson proof / Chromalin", "Foil Block"
]

# --- PROCESSING ---
if not all_pdfs:
    st.info("Upload your PDFs to the 'Files/Quotes' folder in GitHub to begin.")
else:
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 Step 1: Preview Data"):
            with st.spinner(f"Extracting data from {len(all_pdfs)} files..."):
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
                        if gc:
                            # Use your specific Sheet ID
                            sh = gc.open_by_key("1BSA6lItqxS92NCAxrXoK6ey9AzNh1C3ExM98WTXqXo4")
                            worksheet = sh.get_worksheet(0)
                            
                            # Push data
                            worksheet.append_rows(st.session_state['extracted_data'])
                            st.success(f"✅ Successfully added {len(all_pdfs)} rows!")
                except Exception as e:
                    st.error(f"Google Sheets Error: {e}")

# --- RESET ---
if st.sidebar.button("Clear App Cache"):
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()