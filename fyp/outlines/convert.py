import os
from PyPDF2 import PdfReader

# Current directory (where PDFs and script are)
pdf_dir = os.path.dirname(os.path.abspath(__file__))

# Parent directory
parent_dir = os.path.dirname(pdf_dir)

# New folder for text files
txt_dir = os.path.join(parent_dir, os.path.basename(pdf_dir) + "_txt")
os.makedirs(txt_dir, exist_ok=True)

# Process all PDFs
for file_name in os.listdir(pdf_dir):
    if file_name.lower().endswith(".pdf"):
        pdf_path = os.path.join(pdf_dir, file_name)
        txt_file_name = file_name.replace(".pdf", ".txt")
        txt_path = os.path.join(txt_dir, txt_file_name)
        if os.path.exists(txt_path):
            print(f"Skipped (already exists): {txt_file_name}")
            continue
        reader = PdfReader(pdf_path)

        with open(txt_path, "w", encoding="utf-8") as txt_file:
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    txt_file.write(text + "\n")

        print(f"Converted: {file_name} → {txt_file_name}")

print("✅ All PDFs converted successfully.")
