import streamlit as st
import requests
import os
import re

# Get API URL from environment variable or use default
API_URL = os.environ.get("API_URL", "https://email-generator-api.onrender.com")

# Page configuration
st.set_page_config(
    page_title="AI Email Generator",
    page_icon="✉️",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        height: 3rem;
        font-size: 1rem;
    }
    .email-container {
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 20px;
        background-color: #black;
    }
    h1 {
        color: #1E3A8A;
    }
    hr {
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# App title and description
st.title("✉️ AI Personalized Email Generator")
st.markdown("Generate professional, personalized emails tailored to your specific needs.")

# Check backend health
@st.cache_data(ttl=60)
def check_backend_health():
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

if not check_backend_health():
    st.warning("⚠️ Backend API service is currently unavailable. Please try again later.")

# Create two columns for input and output
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Email Details")
    
    # Basic info
    purpose = st.text_input("Purpose of Email", placeholder="Job application, meeting request, follow-up, etc.")
    
    recipient = st.text_input("Recipient (optional)", placeholder="e.g., HR Manager, John Smith")
    sender_name = st.text_input("Your Name (optional)", placeholder="Your full name")
    
    tone = st.selectbox(
        "Email Tone",
        ["Formal", "Friendly", "Persuasive", "Apologetic", "Thankful", "Urgent", "Professional"]
    )
    
    # Context information
    st.subheader("Context & Content")
    prompt = st.text_area(
        "Email Context",
        placeholder="Describe the situation, background information, or any context needed for the email.",
        height=150
    )
    
    # Key points
    st.subheader("Key Points (optional)")
    st.markdown("Add important points to include in your email:")
    
    # Initialize session state for key points
    if 'key_points' not in st.session_state:
        st.session_state.key_points = [""]
    
    # Display input fields for key points
    for i, point in enumerate(st.session_state.key_points):
        col_point, col_delete = st.columns([5, 1])
        with col_point:
            st.session_state.key_points[i] = st.text_input(
                f"Point {i+1}",
                value=point,
                key=f"point_{i}",
                label_visibility="collapsed"
            )
        with col_delete:
            if st.button("🗑️", key=f"delete_{i}") and len(st.session_state.key_points) > 1:
                st.session_state.key_points.pop(i)
                st.rerun()
    
    if st.button("➕ Add Point"):
        st.session_state.key_points.append("")
        st.rerun()

    # Generate button
    generate_button = st.button("🚀 Generate Email", use_container_width=True)

with col2:
    st.subheader("Generated Email")
    email_container = st.empty()
    
    if 'generated_email' in st.session_state:
        email_container.markdown(f"""
        <div class="email-container">
        {st.session_state.generated_email}
        </div>
        """, unsafe_allow_html=True)
    
    # Action buttons for generated email
    if 'generated_email' in st.session_state and st.session_state.generated_email:
        col_copy, col_save = st.columns(2)
        
        with col_copy:
            st.button("📋 Copy to Clipboard", key="copy_button")
        
        with col_save:
            st.download_button(
                label="💾 Download as Text",
                data=st.session_state.generated_email,
                file_name="generated_email.txt",
                mime="text/plain",
                key="download_button"
            )
        
        # Feedback buttons
        st.markdown("### Feedback")
        feedback_cols = st.columns(3)
        with feedback_cols[0]:
            st.button("👍 Helpful")
        with feedback_cols[1]:
            st.button("👎 Not Helpful")
        with feedback_cols[2]:
            st.button("🔄 Regenerate")

# Generate email when button is clicked
if generate_button:
    # Validate inputs
    if not purpose.strip() or not prompt.strip():
        st.error("Please fill in the purpose and context of the email.")
    else:
        # Filter out empty key points
        key_points = [point for point in st.session_state.key_points if point.strip()]
        
        # Show loading spinner
        with st.spinner("Generating your email..."):
            try:
                response = requests.post(
                    f"{API_URL}/generate",
                    json={
                        "prompt": prompt,
                        "tone": tone,
                        "purpose": purpose,
                        "recipient": recipient,
                        "sender_name": sender_name,
                        "key_points": key_points
                    },
                    timeout=30
                )
                
                if response.status_code == 200 and response.json().get("success", False):
                    email_text = response.json().get("email", "")
                    
                    # Process the raw email text to make it more presentable
                    # Enhance the formatting (bold subject, spacing, etc.)
                    email_text = re.sub(r"Subject: (.*)", r"<strong>Subject:</strong> \1", email_text)
                    email_text = email_text.replace("\n", "<br>")
                    
                    # Store the generated email
                    st.session_state.generated_email = email_text
                    
                    # Display the email
                    email_container.markdown(f"""
                    <div class="email-container">
                    {email_text}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.success("Email generated successfully!")
                else:
                    st.error(f"Failed to generate email: {response.json().get('error', 'Unknown error')}")
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to the backend API. Please check your internet connection.")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

# Information about the service
with st.expander("ℹ️ About this Email Generator"):
    st.markdown("""
    This AI-Powered Email Generator uses Google's Gemini AI to create personalized, professional emails based on your input.
    
    **Features:**
    - Multiple tone options for different situations
    - Key points integration
    - Context-aware generation
    - Professional formatting
    
    **All services used are free:**
    - Backend: Flask (Python) on Render
    - Frontend: Streamlit on Streamlit Cloud
    - AI: Google Gemini API (free tier)
    """)