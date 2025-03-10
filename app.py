# Backend using Flask
from flask import Flask, request, jsonify
import google.generativeai as genai
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Get Gemini API key from .env file or environment variable
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    raise ValueError("GEMINI_API_KEY is not set in the environment")

genai.configure(api_key=api_key)

@app.route('/generate', methods=['POST'])
def generate_email():
    data = request.get_json()
    prompt = data.get('prompt', '')
    tone = data.get('tone', 'Formal')
    purpose = data.get('purpose', '')
    recipient = data.get('recipient', '')
    sender_name = data.get('sender_name', '')
    key_points = data.get('key_points', [])
    
    # Create a detailed prompt for better generation
    key_points_text = "\n".join([f"- {point}" for point in key_points]) if key_points else ""
    
    full_prompt = f"""
    Generate a professional {tone.lower()} email for {purpose}.
    
    Context: {prompt}
    
    Recipient: {recipient}
    Sender: {sender_name}
    
    Key points to include:
    {key_points_text}
    
    The email should have:
    1. A clear and appropriate subject line
    2. A greeting that matches the tone
    3. Well-structured body paragraphs
    4. A call-to-action if applicable
    5. An appropriate sign-off
    
    Format the email with subject line, greeting, body, and closing.
    """

    try:
        # Generate email content using Gemini API
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        response = model.generate_content(full_prompt)
        email_text = response.text
        
        return jsonify({
            "email": email_text,
            "success": True
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "success": False
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"})

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Email Generator API is running"})

if __name__ == '__main__':
    # Use the PORT environment variable provided by Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)