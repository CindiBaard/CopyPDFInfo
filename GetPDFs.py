import streamlit as st
import os
import PyPDF2
import gspread
import re
from google.oauth2.service_account import Credentials

# --- AUTHENTICATION (Same as before) ---
def get_gspread_client():
    creds_info = st.secrets["gcp_service_account"]
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_info, scopes=scope)
    return gspread.authorize(creds)

# --- THE MAPPING LOGIC ---
def parse_pdf_to_columns(file_path):
    text = ""
    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        
        # Helper to find value after a heading
        def get_val(heading):
            # This regex looks for the heading and grabs the text until the next newline or major space
            pattern = re.escape(heading) + r"[:\s]+([^\n]+)"
            match = re.search(pattern, text, re.IGNORECASE)
            return match.group(1).strip() if match else ""

        # Constructing the row exactly as your headings are ordered
        row = [
            get_val("Item"),
            get_val("Nett"),
            get_val("Gross"),
            get_val("Markup"),
            get_val("Hours (Repro)"),
            get_val("Dubuit"),
            get_val("K9"),
            get_val("OMSOx1: 100 x 270"),
            get_val("OMSOx1: 135 x 270"),
            get_val("PAD Print"),
            get_val("HKx1:100-120mm"),
            get_val("HKx1:130-150mm"),
            get_val("HKx1:150-180mm"),
            get_val("Silkscreen"),
            get_val("Barcode"),
            get_val("PDF (Artwork)"),
            get_val("DTP"),
            get_val("Pre-press"),
            get_val("Epson proof"),
            get_val("Foil Block")
        ]
        return row
    except Exception as e:
        # Returns a list of errors if the PDF fails to read
        return ["Error"] + [""] * 19

# --- MAIN APP ---
st.title("📄 PDF to Structured Columns")

all_pdfs = [os.path.join(r, f) for r, d, fs in os.walk(".") if "Quotes" in r for f in fs if f.lower().endswith(".pdf")]

if st.button("🚀 Run Extraction"):
    if not all_pdfs:
        st.error("No PDFs found in the 'Quotes' folder.")
    else:
        gc = get_gspread_client()
        sh = gc.open_by_key("1BSA6lItqxS92NCAxrXoK6ey9AzNh1C3ExM98WTXqXo4")
        worksheet = sh.get_worksheet(0)

        data_rows = []
        progress = st.progress(0)
        
        for i, path in enumerate(all_pdfs):
            st.write(f"Processing {os.path.basename(path)}...")
            data_rows.append(parse_pdf_to_columns(path))
            progress.progress((i + 1) / len(all_pdfs))
        
        # This sends all data at once. Each item in the list becomes a column.
        worksheet.append_rows(data_rows)
        st.success("✅ Spreadsheet Updated with 20 Columns!")