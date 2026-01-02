# app.py
import streamlit as st
import pandas as pd
from io import BytesIO
import pytesseract
from pdf2image import convert_from_bytes
import docx2txt
import pdfplumber
import openai
import re
import json

# ---------------- CONFIG -------------------
# Set your OpenAI API key
openai.api_key = "YOUR_OPENAI_API_KEY"

# ----------------- FUNCTIONS -------------------

def extract_text_from_pdf(file):
    """Extract text from PDF (normal or scanned)."""
    text = ""
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        if text.strip() == "":
            images = convert_from_bytes(file.read())
            for img in images:
                text += pytesseract.image_to_string(img) + "\n"
    except:
        images = convert_from_bytes(file.read())
        for img in images:
            text += pytesseract.image_to_string(img) + "\n"
    return text

def extract_text_from_docx(file):
    """Extract text from Word documents."""
    text = docx2txt.process(file)
    return text

def ai_parse_cv(text):
    """Use OpenAI GPT to extract structured CV info."""
    prompt = f"""
    You are an expert HR assistant. Extract the following information from the CV text below:
    - Full Name
    - Email
    - Phone
    - CNIC/ID
    - Education (degrees and universities)
    - Skills
    - Work Experience (company, role, years)
    - Projects
    - Certifications
    - Languages

    Provide output in **JSON format** with keys:
    Name, Email, Phone, CNIC, Education, Skills, Experience, Projects, Certifications, Languages

    CV Text:
    {text}
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        text_response = response['choices'][0]['message']['content']
        data = json.loads(text_response)
    except:
        data = {
            "Name": "", "Email": "", "Phone": "", "CNIC": "",
            "Education": "", "Skills": "", "Experience": "",
            "Projects": "", "Certifications": "", "Languages": ""
        }
    return data

# ----------------- STREAMLIT UI -------------------

st.set_page_config(page_title="Ultimate CV Parser", layout="wide")
st.title("📄 Ultimate Professional CV Parser")
st.write("Upload multiple CVs (PDF, DOCX, images). Extracted info will be ready for Excel download.")

uploaded_files = st.file_uploader(
    "Upload CVs",
    type=["pdf","docx","png","jpg","jpeg"],
    accept_multiple_files=True
)

if uploaded_files:
    st.info("Processing CVs... Please wait ⏳")
    data = []

    for file in uploaded_files:
        if file.type == "application/pdf":
            text = extract_text_from_pdf(file)
        elif file.type.endswith("wordprocessingml.document"):
            text = extract_text_from_docx(file)
        else:
            text = pytesseract.image_to_string(file)

        entry = ai_parse_cv(text)
        data.append(entry)

    df = pd.DataFrame(data)
    st.success("✅ Extraction Complete!")
    st.dataframe(df)

    # Download Excel
    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    st.download_button(
        label="📥 Download Excel",
        data=buffer,
        file_name="extracted_CVs.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
