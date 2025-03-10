# Backend using Flask
from flask import Flask, request, jsonify
import google.generativeai as genai
from flask_cors import CORS
import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re

# Load environment variables
load_dotenv()
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))

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

@app.route('/send-email', methods=['POST'])
def send_email():
    data = request.get_json()
    email_content = data.get('email_content', '')
    recipient_email = data.get('recipient_email', '')
    sender_name = data.get('sender_name', 'Email Generator User')
    
    # Get user's email credentials from request
    sender_email = data.get('sender_email', '')
    sender_password = data.get('sender_password', '')
    email_host = data.get('email_host', EMAIL_HOST)
    email_port = int(data.get('email_port', EMAIL_PORT))
    
    # Validate email addresses
    if not re.match(r"[^@]+@[^@]+\.[^@]+", recipient_email):
        return jsonify({
            "success": False,
            "error": "Invalid recipient email address format"
        }), 400
        
    if not re.match(r"[^@]+@[^@]+\.[^@]+", sender_email):
        return jsonify({
            "success": False,
            "error": "Invalid sender email address format"
        }), 400
    
    # Check required credentials
    if not sender_email or not sender_password:
        return jsonify({
            "success": False,
            "error": "Sender email and password are required."
        }), 400
    
    # Extract subject from the email content
    subject_match = re.search(r"Subject:(.*?)(?:\n|<br>)", email_content, re.IGNORECASE)
    subject = subject_match.group(1).strip() if subject_match else "Generated Email"
    
    # Clean up HTML from email content if present for plain text version
    email_text = re.sub(r'<.*?>', '', email_content)
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{sender_name} <{sender_email}>"
        msg['To'] = recipient_email
        msg['Subject'] = subject
        
        # Create both plain text and HTML versions
        text_part = MIMEText(email_text, 'plain')
        html_part = MIMEText(email_content, 'html')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP(email_host, email_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        return jsonify({
            "success": True,
            "message": f"Email sent successfully to {recipient_email}"
        })
    except smtplib.SMTPAuthenticationError:
        return jsonify({
            "success": False,
            "error": "Authentication failed. Please check your email and password. For Gmail, use an App Password instead of your regular password."
        }), 401
    except smtplib.SMTPException as e:
        return jsonify({
            "success": False,
            "error": f"SMTP Error: {str(e)}"
        }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to send email: {str(e)}"
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
