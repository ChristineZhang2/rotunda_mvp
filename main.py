from flask import Flask, request
import fitz  # PyMuPDF for reading PDFs
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load your OpenAI API key from .env
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPEN_API_KEY"))


# Helper: extract text from uploaded PDF
def extract_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    return "\n".join([page.get_text() for page in doc])


# Route: homepage with welcome message
@app.route('/')
def index():
    return '''
        <h2>✅ Rotunda AI is Live!</h2>
        <p>Go to <a href="/upload">/upload</a> to submit your documents.</p>
    '''


# Route: handle uploads and GPT
@app.route('/upload', methods=['GET', 'POST'])
def handle_upload():
    if request.method == 'GET':
        # Show upload form
        return '''
            <h2>Grant Draft Generator</h2>
            <form action="/upload" method="post" enctype="multipart/form-data">
                <label>District Document (PDF):</label><br>
                <input type="file" name="district_doc" required><br><br>

                <label>Grant Document (PDF):</label><br>
                <input type="file" name="grant_doc" required><br><br>

                <button type="submit">Generate Draft</button>
            </form>
        '''

    # POST request: generate GPT draft
    print("📥 Files uploaded!")

    try:
        # Get the uploaded files
        district_file = request.files['district_doc']
        grant_file = request.files['grant_doc']

        # Extract text from each PDF
        district_text = extract_text(district_file)[:2000]
        grant_text = extract_text(grant_file)[:2000]

        # Build the GPT prompt
        prompt = f"""
You are a grant-writing assistant. Write a short, first-draft grant application using the following information.

---

District Info:
{district_text}

Grant Info:
{grant_text}

---

Use this structure:
1. Project Title
2. Executive Summary (3–5 sentences)
3. Needs Statement
4. Goals & Objectives (3 bullet points)
5. Budget Overview
6. Sustainability Plan

Respond professionally and clearly. Keep the total response under 500 words.
"""

        # Call OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "system",
                "content": "You are a grant-writing assistant."
            }, {
                "role": "user",
                "content": prompt
            }])

        # Extract and format the result
        draft = response.choices[0].message.content
        formatted_draft = draft.replace("\n", "<br>")

        return f"<div style='font-family: Arial, sans-serif; padding: 2rem;'>{formatted_draft}</div>"

    except Exception as e:
        print("❌ Error:", e)
        return f"<p style='color:red;'>❌ Error: {str(e)}</p>", 500


# Replit requires this exact host/port setup
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
