from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask import Flask, request, jsonify, render_template, redirect, url_for, make_response

import re
from PyPDF2 import PdfReader
import fitz
import spacy
import os
from flask import send_file, session 
import pdfkit

app = Flask(__name__)

# Load the en_core_web_lg model
nlp = spacy.load('en_core_web_lg')

@app.route('/', methods=['GET'])
def upload_file():
    value = request.args.get('value')
    # Process the received value as needed
    print('Received value:', value)

    return render_template('index.html')


@app.route('/extract_info', methods=['GET', 'POST'])
def extract_info():
    if request.method == 'POST':
        # Get the uploaded file from the request object
        file = request.files['file']

        # Save the file to a temporary location
        file.save('temp.pdf')

        # Extract information from the PDF
        info = extract_information('temp.pdf')

        # Delete the temporary file
        os.remove('temp.pdf')

        # Render the results template with the extracted information
        return render_template('result.html', data=info)
    else:
        return render_template('index.html')

@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    # Get the data from the form submission
    data = request.form

    # Render the result.html template with the data
    html = render_template('result_pdf.html', data=data)

    # Create a configuration object with the path to the wkhtmltopdf executable
    config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
    pdf = pdfkit.from_string(html, False, configuration=config)

    # Create a response with the PDF data
    response = make_response(pdf)

    # Set the content type to 'application/pdf'
    response.headers['Content-Type'] = 'application/pdf'

    # Set the content disposition to 'attachment' so it can be downloaded
    response.headers['Content-Disposition'] = 'attachment; filename=output.pdf'

    return response





def extract_information(pdf_path):
    print("Extracting information from: ", pdf_path)
    with open(pdf_path, 'rb') as f:
        pdf = PdfReader(f)
        num_pages = len(pdf.pages)
        text = ''
        for page in pdf.pages:
            text += page.extract_text()

        doc = fitz.open(pdf_path)
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

    return (info)

  

if __name__ == '__main__':
    app.run(debug=True)




