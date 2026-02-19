import os
import PyPDF2
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 1. Setup Google Sheets Authentication
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)

# 2. Open the Spreadsheet
spreadsheet_id = "1BSA6lItqxS92NCAxrXoK6ey9AzNh1C3ExM98WTXqXo4"
sheet = client.open_by_key(spreadsheet_id).sheet1

# 3. Path to your PDF folder
folder_path = './New folder(3)'
pdf_files = [f for f in os.listdir(folder_path) if f.endswith('.pdf')]

# 4. Extract and Upload
for pdf_file in pdf_files:
    file_path = os.path.join(folder_path, pdf_file)
    
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        full_text = ""
        
        # Extract text from all pages
        for page in reader.pages:
            full_text += page.extract_text() + "\n"
        
        # Append to the next available row in Google Sheets
        # We store the filename in Col A and the content in Col B
        sheet.append_row([pdf_file, full_text])
        print(f"Successfully uploaded: {pdf_file}")

print("Extraction complete!")