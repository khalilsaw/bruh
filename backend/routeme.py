from flask import Flask, request, render_template
from pymongo import MongoClient
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter
import fitz
import spacy
import re
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

app = Flask(__name__)

# Load the en_core_web_lg model
nlp = spacy.load('en_core_web_lg')

# Connect to MongoDB
client = MongoClient("mongodb+srv://safaehamri82:UevKunSxstC52C4i@cluster0.balntet.mongodb.net/?retryWrites=true&w=majority&wtimeoutMS=5000")
db = client['your_database_name']
collection = db['your_collection_name']

@app.route('/tablepage')
def table_page():
    # Retrieve the list of uploaded PDF names from the MongoDB collection
    pdf_docs = collection.find()
    return render_template('tablepage.html', pdf_docs=pdf_docs)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Check if a file was uploaded
        if 'file' not in request.files:
            return 'No file uploaded'

        file = request.files['file']

        # Check if the file has a name
        if file.filename == '':
            return 'Empty file name'

        # Save the uploaded file to a BytesIO object
        file_stream = BytesIO()
        file.save(file_stream)
        file_stream.seek(0)

        # Extract information from the uploaded PDF
        info = extract_information(file_stream)

        # Generate a new PDF with the extracted information
        new_pdf_stream = generate_pdf(info)

        # Store the new PDF in MongoDB
        pdf_id = store_pdf(info, new_pdf_stream)

        # Render the result template and pass the extracted information and new PDF URL/id
        return render_template('result.html', info=info, pdf_id=pdf_id)

    return render_template('index.html')

def extract_information(pdf_stream):
    print("Extracting information from the uploaded PDF")
    with PdfReader(pdf_stream) as pdf:
        text = ''
        for page in pdf.pages:
            text += page.extract_text()

        doc = fitz.open(stream=pdf_stream)
        images = []
        for i in range(doc.page_count):
            img_list = doc.get_page_images(i)
            for img in img_list:
                images.append(img)

    doc = nlp(text)
    name = ''
    for ent in doc.ents:
        if ent.label_ == 'PERSON':
            name = ent.text
            break

    phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    phone_numbers = re.findall(phone_pattern, text)
    phone_number = phone_numbers[0] if phone_numbers else ''

    email_pattern = r'\S+@\S+'
    email_addresses = re.findall(email_pattern, text)
    email_address = email_addresses[0] if email_addresses else ''

    education_pattern = r'(?:Education|Qualifications|Academic|University|Bachelor|Diploma)(.*?)(?:Experience|Skills|Abilities|Employment|\n\n)'
    education = re.search(education_pattern, text, re.DOTALL)
    education = education.group(1).strip() if education else ''

    skills_pattern = r'(?:Skills|Abilities)(.*?)(?:Experience|Education|email|Certifications|\n\n)'
    skills = re.search(skills_pattern, text, re.DOTALL)
    skills = skills.group(1).strip() if skills else ''

    experience_pattern = r'(?:Experience|Employment)(.*?)(?:Education|Skills|Certifications|Languages|Language|\n\n)'
    experience = re.search(experience_pattern, text, re.DOTALL)
    experience = experience.group(1).strip() if experience else ''

    language_pattern = r'(?:Language|Languages|language skills|Language Skills)(.*?)(?:Experience|Education|Skills|Abilities|Employment|\Z)'
    language = re.search(language_pattern, text, re.DOTALL)
    language = language.group(1).strip() if language else ''

    certification_pattern = r'(?:Certifications|Certification|JavaScript)(.*?)(?:Experience|Education|Skills|Language|\n\n)'
    certification = re.search(certification_pattern, text, re.DOTALL)
    certification = certification.group(1).strip() if certification else ''

    info = {
        'name': name,
        'phone_number': phone_number,
        'email_address': email_address,
        'education': education,
        'skills': skills,
        'experience': experience,
        'language': language,
        'certification': certification,
        'images': images
    }

    return info

def generate_pdf(info):
    print("Generating new PDF with extracted information")
    output_stream = BytesIO()
    # Create a new PDF using ReportLab
    c = canvas.Canvas(output_stream, pagesize=letter)

    # Set font and font size
    c.setFont("Helvetica", 12)

    # Add content to the PDF
    content = [
        f"Name: {info['name']}",
        f"Phone Number: {info['phone_number']}",
        f"Email Address: {info['email_address']}",
        f"Education: {info['education']}",
        f"Skills: {info['skills']}",
        f"Experience: {info['experience']}",
        f"Language: {info['language']}",
        f"Certification: {info['certification']}",
    ]
    y = 700
    for line in content:
        c.drawString(50, y, line)
        y -= 20

    c.save()
    output_stream.seek(0)
    return output_stream

def store_pdf(info, pdf_stream):
    print("Storing the new PDF in MongoDB")
    # Split the PDF into smaller chunks if necessary
    chunk_size = 1024 * 1024  # 1MB
    pdf_chunks = []
    while True:
        chunk = pdf_stream.read(chunk_size)
        if not chunk:
            break
        pdf_chunks.append(chunk)

    # Store the PDF and info in MongoDB
    pdf_doc = {
        'info': info,
        'chunks': pdf_chunks,
        'num_chunks': len(pdf_chunks)
    }
    pdf_id = collection.insert_one(pdf_doc).inserted_id
    return str(pdf_id)

if __name__ == '_main_':
    app.run(debug=True)

# Close the MongoDB client when the application is terminated
client.close()