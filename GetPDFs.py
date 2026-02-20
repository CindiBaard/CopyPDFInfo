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

all_pdfs = []

for root, dirs, files in os.walk("."):

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

Gemini said
It looks like your code is being a bit too thorough! The reason you are seeing 9917 PDFs is likely because of how the search logic is navigating your computer's folders.

The Culprit: os.walk(".")
In your code, you have this block:

Python
for root, dirs, files in os.walk("."):
    for file in files:
        if file.lower().endswith(".pdf"):
            all_pdfs.append(os.path.join(root, file))
The function os.walk(".") tells Python to start at the current directory (where your script is) and then "walk" down into every single subfolder it can find.

If you are running this locally (on your laptop) or in a large repository, it is likely digging into hidden folders you didn't intend to search, such as:

.venv or env: Virtual environments often contain thousands of documentation PDFs.

.git: Internal version control files.

node_modules: If you have any JavaScript projects nearby.

System Temp Folders: If your script is sitting in a broad user directory.

How to Fix It
You have two main options depending on where your actual PDFs are located.

Option 1: Limit to a Specific Folder (Recommended)
If your PDFs are only in a folder named "Quotes", change the walk to start there instead of the root ".":

Python
# Change "." to your specific folder name
for root, dirs, files in os.walk("./Quotes"): 
    for file in files:
        if file.lower().endswith(".pdf"):
            all_pdfs.append(os.path.join(root, file))
Option 2: Stay in the Current Folder Only (No Subfolders)
If you don't want the script to "walk" into subdirectories at all, use os.listdir() instead:

Python
all_pdfs = [f for f in os.listdir(".") if f.lower().endswith(".pdf")]
Option 3: Exclude Hidden/System Folders
If you must use os.walk but want to skip things like virtual environments, you can "prune" the search:

Python
for root, dirs, files in os.walk("."):
    # This line tells the code to skip these folders
    dirs[:] = [d for d in dirs if d not in ['.venv', '.git', '__pycache__', 'node_modules']]
    for file in files:
        if file.lower().endswith(".pdf"):
            all_pdfs.append(os.path.join(root, file))
⚠️ A Quick Warning
Trying to process 9,917 PDFs through PyPDF2 and then pushing them to Google Sheets in one go will almost certainly:

Crash your Streamlit app (due to memory limits).

Trigger Google Sheets API limits (you can't usually push that much data in one append_rows call without timing out).

Would you like me to help you modify the code to include a "limit" or a folder selection dropdown so you don't accidentally process thousands of files?

You said
can i exit out of streamlit to reload the code

Gemini said
Yes, you absolutely can! In fact, Streamlit is designed to handle code changes in a few different ways. Here is the best way to manage reloading depending on what you’ve changed:

1. The "Soft" Reload (Recommended)
If you have just edited the Python script (e.g., changed the folder path or fixed a typo) and the app is still running in your terminal:

Save your file in your code editor.

Look at the top-right corner of your Streamlit browser window. You will see a message: "Source file changed."

Click "Always rerun".

From now on, every time you press Ctrl+S (Save) in your editor, the app will automatically refresh with the new code.

2. The "Hard" Restart (If the app is stuck)
If the app is frozen because it's trying to process those 9,917 PDFs, you should kill the process and start over:

Go to your Terminal/Command Prompt where the code is running.

Press Ctrl + C to stop the Streamlit server.

Type streamlit run your_filename.py to start it fresh.

💡 Pro-Tip: Adding a "Stop" Safeguard
Since you accidentally hit 9,000+ files, you can add a "Safety Valve" to your code so it doesn't try to process everything at once while you are testing.

Replace your file detection logic with this "Limited" version:

Python
# --- DYNAMIC FILE SEARCH WITH LIMIT ---
all_pdfs = []
MAX_FILES = 10  # Change this to 100 or more once you're ready!

for root, dirs, files in os.walk("."):
    # Ignore hidden and environment folders
    dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['venv', 'env', 'node_modules']]
    
    for file in files:
        if file.lower().endswith(".pdf"):
            all_pdfs.append(os.path.join(root, file))
            if len(all_pdfs) >= MAX_FILES:
                break
    if len(all_pdfs) >= MAX_FILES:
        break
Summary of Actions
Action	Keyboard Shortcut	When to use
Stop App	Ctrl + C (Terminal)	If the app is frozen or you want to quit.
Rerun App	R (in Browser)	To manually refresh the UI.
Clear Cache	C (in Browser)	If data is "stuck" even after a code change.
Would you like me to rewrite the file-searching part of your code to only look in a specific "Quotes" folder so you don't have to worry about the 9,000+ files again?

You said
NameError: This app has encountered an error. The original error message is redacted to prevent data leaks. Full error details have been recorded in the logs (if you're on Streamlit Cloud, click on 'Manage app' in the lower right of your app).

Traceback:

File "/mount/src/copypdfinfo/GetPDFs.py", line 48, in <module>

st.sidebar.write(f"Total PDFs detected: **{len(all_pdfs)}**")

^^^^^^^^ import streamlit as st

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

Gemini said
The NameError is occurring because you are trying to add items to the list all_pdfs before actually creating (initializing) the list. In Python, you can't append to something that doesn't exist yet!

The Fix
You just need to add all_pdfs = [] right before your for loop starts.

Search for this section in your code and update it like this:

Python
# --- DYNAMIC FILE SEARCH ---
all_pdfs = []  # <--- ADD THIS LINE HERE

for root, dirs, files in os.walk("./Quotes"): 
    for file in files:
        if file.lower().endswith(".pdf"):
            all_pdfs.append(os.path.join(root, file))
Why this happened
In your original code, you had all_pdfs = [] at the top of the search block. When you edited the code to change the directory to ./Quotes, that line was accidentally deleted or commented out.

Wait! One more thing to check:
Since you are running this on Streamlit Cloud (based on your traceback path /mount/src/...), make sure a folder named Quotes actually exists in your GitHub repository.

If the PDFs are just sitting in the main folder of your GitHub, use os.walk(".").

If they are inside a folder named "Quotes", then os.walk("./Quotes") is correct.

Updated Snippet for Safety
If you want to avoid the "9,000 files" issue again while fixing the error, use this version:

Python
all_pdfs = []
# This checks if the folder exists first to prevent a crash
search_path = "./Quotes" if os.path.exists("./Quotes") else "."

for root, dirs, files in os.walk(search_path):
    # Ignore hidden folders like .git
    dirs[:] = [d for d in dirs if not d.startswith('.')]
    for file in files:
        if file.lower().endswith(".pdf"):
            all_pdfs.append(os.path.join(root, file))
Would you like me to provide the full, corrected script so you can copy-paste the whole thing?

You said
yes please

Gemini said
Here is the complete, corrected code. I have added the initialization for all_pdfs and included a safety check to ensure the folder exists so the app doesn't crash.

Python
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
        st.error(f"Authentication Error: Check your Streamlit Secrets. {e}")
        return None

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
        return [f"Error reading {os.path.basename(file_path)}: {str(e)}"] + [""] * (len(headers) - 1)

# --- MAIN APP ---
st.set_page_config(layout="wide", page_title="PDF Data Extractor")
st.title("📄 PDF to Structured Columns")

# --- DYNAMIC FILE SEARCH ---
all_pdfs = []  # <--- FIXED: Initialized the list to prevent NameError

# Check if "Quotes" folder exists, otherwise look in the current directory
search_dir = "./Quotes" if os.path.exists("./Quotes") else "."

for root, dirs, files in os.walk(search_dir):
    # Prune hidden folders (like .git or .venv) to avoid the 9,000+ file issue
    dirs[:] = [d for d in dirs if not d.startswith('.')]
    for file in files:
        if file.lower().endswith(".pdf"):
            all_pdfs.append(os.path.join(root, file))

# --- SIDEBAR STATUS ---
st.sidebar.write(f"### 📁 System Status")
st.sidebar.write(f"Searching in: `{search_dir}`")
st.sidebar.write(f"Total PDFs detected: **{len(all_pdfs)}**")

if all_pdfs:
    st.sidebar.write("Files ready for processing ✅")
else:
    st.sidebar.warning("No PDFs found in the target directory.")

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
    st.error("No PDFs found. Please ensure your PDFs are in the 'Quotes' folder or the root of your repository.")
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
                        if gc:
                            sh = gc.open_by_key("1BSA6lItqxS92NCAxrXoK6ey9AzNh1C3ExM98WTXqXo4")
                            worksheet = sh.get_worksheet(0)
                            worksheet.append_rows(st.session_state['extracted_data'])
                            st.success(f"✅ Successfully added {len(all_pdfs)} rows to your Spreadsheet!")
                except Exception as e:
                    st.error(f"Google Sheets Error: {e}")