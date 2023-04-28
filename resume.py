import spacy
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter 
from pdfminer.converter import TextConverter 
from pdfminer.layout import LAParams 
from pdfminer.pdfpage import PDFPage
import re
import json

# Load language model
nlp = spacy.load("fr_core_news_sm")

# Define regular expressions for matching phone numbers and emails
phone_regex = r"\b[0-9]{2}[-. ]?[0-9]{2}[-. ]?[0-9]{2}[-. ]?[0-9]{2}[-. ]?\b"
email_regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"

# Define function to extract section text
def extract_section_text(doc, section_start_keywords, section_entity_labels):
    section_text = ""
    section_started = False
    section_ended = False
    for token in doc:
        if not section_started:
            if any(keyword in token.text.lower() for keyword in section_start_keywords):
                section_started = True
                section_text += token.text_with_ws
                continue
        if section_started and not section_ended:
            if any(ent.label_ in section_entity_labels for ent in token.ents):
                section_ended = True
                break
            section_text += token.text_with_ws
    return section_text.strip()

# Extract text from PDF file
with open("/workspace/bruh/Black White Minimalist CV Resume.pdf", "rb") as f, open("output.txt", "w", encoding="utf-8") as outfile:
    rsrcmgr = PDFResourceManager()
    laparams = LAParams()
    converter = TextConverter(rsrcmgr, outfile, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, converter)

    for page in PDFPage.get_pages(f, caching=True, check_extractable=True): 
        interpreter.process_page(page)
        
    text = converter.close()

print("Extracted text:", text)

if text:
    doc = nlp(text)

    # Extract person names
    person_names = [ent.text for ent in doc.ents if ent.label_ == "PER"]

    # Extract email addresses
    email_addresses = re.findall(email_regex, text)

    # Extract phone numbers
    phone_numbers = re.findall(phone_regex, text)

    # Extract experiences section
    experiences_start_keywords = ["expérience", "expériences professionnelles"]
    experiences_entity_labels = ["ORG", "LOC", "PER"]
    experiences_text = extract_section_text(doc, experiences_start_keywords, experiences_entity_labels)

    # Extract education section
    education_start_keywords = ["formation", "formations"]
    education_entity_labels = ["ORG", "LOC", "PER"]
    education_text = extract_section_text(doc, education_start_keywords, education_entity_labels)

    # Extract skills section
    skills_start_keywords = ["compétences"]
    skills_entity_labels = ["SKILL"]
    skills_text = extract_section_text(doc, skills_start_keywords, skills_entity_labels)

    # Create a dictionary with the extracted information
    resume_dict = {
        'person_names': person_names,
        'email_addresses': email_addresses,
        'phone_numbers': phone_numbers,
        'experiences_text': experiences_text,
        'education_text': education_text,
        'skills_text': skills_text
    }
       # Print extracted information in JSON format
    print(json.dumps(resume_dict, ensure_ascii=False))

else:
    print("Error: Failed to extract text from PDF file.")
   
