import logging
import streamlit as st
import requests
import uuid
from PIL import Image
import base64

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Set the page configuration (must be first command)
st.set_page_config(
    page_title="📄 Document Chapter Summarizer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Function to add background image or enhance UI
def add_bg_from_url():
    """
    Adds a background image to the Streamlit app.
    """
    st.markdown(
         f"""
         <style>
         .stApp {{
             background-image: url("https://images.unsplash.com/photo-1581090464230-3a94a406c829?ixlib=rb-4.0.3&auto=format&fit=crop&w=1950&q=80");
             background-attachment: fixed;
             background-size: cover;
         }}
         </style>
         """,
         unsafe_allow_html=True
     )

# Call the function to set background
add_bg_from_url()

# Header with logo and title
col1, col2 = st.columns([1, 3])
with col1:
    # Add a logo image
    st.image("https://streamlit.io/images/brand/streamlit-logo-secondary-colormark-darktext.png", width=100)
with col2:
    st.title("📄 Document Chapter Summarizer")

# Instructions
st.markdown("""
### Upload a Word document, and the application will summarize each chapter for you.
""")

# Initialize session state for session_id and summaries
if 'session_id' not in st.session_state:
    st.session_state['session_id'] = None
if 'summaries' not in st.session_state:
    st.session_state['summaries'] = {}

def upload_and_summarize(uploaded_file):
    """
    Uploads the file to the backend API and retrieves summaries.

    Args:
        uploaded_file (UploadedFile): The uploaded Word document.

    Returns:
        dict: Summaries of each chapter.
    """
    api_url = "http://localhost:8001/summarize"
    
    # Log the MIME type for debugging purposes
    logger.debug(f"Uploaded file MIME type: {uploaded_file.type}")
    
    # Ensure the file has the correct MIME type
    if uploaded_file.type != "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        logger.error(f"Uploaded file is not a valid .docx file. MIME type: {uploaded_file.type}")
        st.error("Only .docx files are supported.")
        return {}, None
    
    # Continue with summarization
    files = {'file': (uploaded_file.name, uploaded_file.read(), uploaded_file.type)}
    params = {'session_id': str(uuid.uuid4())}
    
    try:
        logger.info("Sending file to API for summarization...")
        response = requests.post(api_url, files=files, params=params)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Summarization successful for session_id: {data.get('session_id')}")
        return data.get("summaries", {}), data.get("session_id")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error while uploading file: {str(e)}")
        st.error("Failed to upload or summarize the file. Please try again.")
        return {}, None

# File uploader widget with better UI
with st.container():
    uploaded_file = st.file_uploader("📂 **Upload a Word Document**", type=["docx"], accept_multiple_files=False)

    if uploaded_file is not None:
        st.success(f"**Filename:** {uploaded_file.name}")
        logger.debug(f"File uploaded: {uploaded_file.name}")
        
        # Button to initiate summarization with enhanced styling
        summarize_button = st.button("🔍 **Summarize**", key='summarize_button')
        
        if summarize_button:
            with st.spinner('🔍 Summarizing chapters...'):
                summaries, session_id = upload_and_summarize(uploaded_file)
                if summaries and session_id:
                    st.session_state['summaries'] = summaries
                    st.session_state['session_id'] = session_id
                    st.success("✅ Summarization complete!")
                    logger.info(f"Summaries stored in session state for session_id: {session_id}")
                else:
                    st.error("❌ Failed to retrieve summaries.")
                    logger.error("Summarization process failed.")
        
        # Display summaries if available
        if st.session_state['summaries']:
            st.markdown("### 📑 **Chapter Summaries**")
            for chapter, summary in st.session_state['summaries'].items():
                with st.expander(f"📖 {chapter}"):
                    st.write(summary)
                    logger.debug(f"Displaying summary for chapter: {chapter}")

# Sidebar for session management
with st.sidebar:
    st.header("🔄 **Session Management**")
    
    def start_new_session():
        """
        Resets the session state to start a new chat.
        """
        logger.info("Starting a new session")
        st.session_state['session_id'] = None
        st.session_state['summaries'] = {}
        st.experimental_rerun()
    
    if st.button("🚀 **Start New Chat**"):
        start_new_session()
    
    st.markdown("""
    ---
    **Developed with ❤️ using Streamlit and FastAPI.**
    """)

# Footer
st.markdown("""
---
© 2024 Document Summarizer. All rights reserved.
""")
