import streamlit as st
import os
import PyPDF2
import gspread
import re
import pandas as pd # Added for the preview table
from google.oauth2.service_account import Credentials

# --- AUTHENTICATION ---
def get_gspread_client():
    creds_info = st.secrets["gcp_service_account"]
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_info, scopes=scope)
    return gspread.authorize(creds)

# --- THE MAPPING LOGIC ---
def parse_pdf_to_columns(file_path, headers):
    text = ""
    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        
        row = []
        for h in headers:
            # Look for the heading and grab the next "word" or "number"
            # This pattern looks for the header, skips colon/spaces, and grabs everything until a newline
            pattern = re.escape(h) + r"[:\s]+([^\n]+)"
            match = re.search(pattern, text, re.IGNORECASE)
            row.append(match.group(1).strip() if match else "")
        return row
    except:
        return ["Error Reading File"] + [""] * (len(headers) - 1)

# --- MAIN APP ---
st.set_page_config(layout="wide")
st.title("📄 PDF to Structured Columns")

# Define your exact 20 headers
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

all_pdfs = [os.path.join(r, f) for r, d, fs in os.walk(".") if "Quotes" in r for f in fs if f.lower().endswith(".pdf")]

if not all_pdfs:
    st.info("Please ensure your PDFs are in a folder named 'Quotes' on GitHub.")
else:
    # --- PREVIEW SECTION ---
    if st.button("🔍 Step 1: Preview Data from PDFs"):
        preview_data = []
        for path in all_pdfs:
            preview_data.append(parse_pdf_to_columns(path, column_headers))
        
        # Store in session state so Step 2 can use it
        st.session_state['extracted_data'] = preview_data
        
        # Display as a Table
        df = pd.DataFrame(preview_data, columns=column_headers)
        st.write("### Data Preview (Check columns below)")
        st.dataframe(df)

    # --- UPLOAD SECTION ---
    if 'extracted_data' in st.session_state:
        st.divider()
        st.warning("Found the data above. Ready to send to Google Sheets?")
        if st.button("📤 Step 2: Confirm & Upload to Google Sheets"):
            try:
                gc = get_gspread_client()
                sh = gc.open_by_key("1BSA6lItqxS92NCAxrXoK6ey9AzNh1C3ExM98WTXqXo4")
                worksheet = sh.get_worksheet(0)
                
                worksheet.append_rows(st.session_state['extracted_data'])
                st.success(f"✅ Successfully uploaded {len(st.session_state['extracted_data'])} rows!")
                # Clear session state so they don't double-upload
                del st.session_state['extracted_data']
            except Exception as e:
                st.error(f"Error: {e}")