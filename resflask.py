import io
import os
import re
import spacy
import pdfplumber
from flask import Flask, render_template, request

# Load the French language model
nlp = spacy.load("fr_core_news_sm")

# Define regular expressions for matching phone numbers and email addresses
phone_regex = r"\b[0-9]{2}[-. ]?[0-9]{2}[-. ]?[0-9]{2}[-. ]?[0-9]{2}[-. ]?\b"
email_regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"

# Define function to extract text from PDF file
def extract_text_from_pdf(file_path):
    with pdfplumber.open(file_path) as pdf:
        pages = []
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n".join(pages)

# Define function to extract section text
def extract_section_text(doc, section_start_keywords, section_entity_labels):
    section_text = ""
    section_started = False
    section_ended = False
    for token in doc:
        if not section_started:
            if any(keyword in token.text.lower() for keyword in section_start_keywords):
                section_started = True
                section_text += token.text
        elif section_started and not section_ended:
            if any(ent.label_ in section_entity_labels for ent in doc.ents) or token.is_stop:
                section_text += token.text_with_ws
            else:
                section_ended = True
    return section_text.strip()

# Define function to extract all sections from resume
def extract_resume_sections(resume_text):
    doc = nlp(resume_text)

    # Extract person names
    person_names = [ent.text for ent in doc.ents if ent.label_ == "PER"]

    # Extract email addresses
    email_addresses = re.findall(email_regex, resume_text)

    # Extract phone numbers
    phone_numbers = re.findall(phone_regex, resume_text)

    # Extract experiences section
    experiences_start_keywords = ["expérience", "expériences", "professionnelles", "professionnelle"]
    experiences_entity_labels = ["ORG", "LOC"]
    experiences_text = extract_section_text(doc, experiences_start_keywords, experiences_entity_labels)

    # Extract education section
    education_start_keywords = ["formation", "formations", "diplômes", "diplôme", "études", "étude"]
    education_entity_labels = ["ORG", "LOC"]
    education_text = extract_section_text(doc, education_start_keywords, education_entity_labels)

    # Extract skills section
    skills_start_keywords = ["compétences", "connaissances", "techniques", "langues"]
    skills_entity_labels = ["SKILL", "LANGUAGE"]
    skills_text = extract_section_text(doc, skills_start_keywords, skills_entity_labels)

    # Return dictionary of extracted information
    resume_dict = {
        "person_names": person_names,
        "email_addresses": email_addresses,
        "phone_numbers": phone_numbers,
        "experiences_text": experiences_text,
        "education_text": education_text,
        "skills_text": skills_text,
    }
    return resume_dict

# Define Flask app
app = Flask(__name__)

# Define route for home page
@app.route("/")
def home():
    return render_template("index.html")

# Define route for file upload and display of results
@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["resume"]
    file_path = os.path.join("uploads", file.filename)
    file.save(file_path)
    resume_text = extract_text_from_pdf(file_path)
    resume_dict = extract_resume_sections(resume_text)
    return render_template("results.html", resume_dict=resume_dict)

# Run the app
if __name__ == "__main__":
    app.run(debug=True)