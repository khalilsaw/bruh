import os
import fitz
import spacy
import pdfkit
from flask import Flask, render_template, request, send_file

app = Flask(__name__)

nlp = spacy.load("en_core_web_lg")


def extract_information(filename):
    pdf = fitz.open(filename)
    text = ""
    for page in pdf:
        text += page.getText()
    information = {}
    for entity in nlp(text).ents:
        if entity.label_ in ["PERSON", "TITLE", "EMAIL", "PHONE", "ORGANIZATION", "EDUCATION", "SKILLS", "EXPERIENCE", "LANGUAGES", "CERTIFICATIONS"]:
            information[entity.label_] = entity.text
    return information


@app.route("/")
def upload_file():
    return render_template("index.html")


@app.route("/extract_info", methods=["POST"])
def extract_info():
    file = request.files["file"]
    filename = os.path.join("upload", file.filename)
    file.save(filename)

    information = extract_information(filename)

    pdf = pdfkit.from_string(
        render_template("result.html", data=information),
        False,
        configuration={
            "wkhtmltopdf": "/usr/local/bin/wkhtmltopdf",
            "page-size": "A4",
            "margin-top": "0.5in",
            "margin-bottom": "0.5in",
            "margin-left": "0.5in",
            "margin-right": "0.5in",
        },
    )

    response = send_file(
        pdf,
        attachment_filename=file.filename,
        as_attachment=True,
        mimetype="application/pdf",
    )

    os.remove(filename)
    return response


if __name__ == "__main__":
    app.run(debug=True)
