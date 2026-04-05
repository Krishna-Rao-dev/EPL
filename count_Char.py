import pdfplumber

def count_characters_pdf(file_path):
    text = ""

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""

    return len(text)

print(count_characters_pdf("07_Registered_Address_INC22.pdf"))