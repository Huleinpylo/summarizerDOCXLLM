# frontend/app.py

import streamlit as st
import requests
from streamlit_lottie import st_lottie
import json
import time

# Function to load Lottie animations
def load_lottieurl(url: str):
    import requests
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# Load animations
lottie_upload = load_lottieurl("https://assets8.lottiefiles.com/packages/lf20_jcikwtux.json")
lottie_processing = load_lottieurl("https://assets6.lottiefiles.com/packages/lf20_usmfx6bp.json")
lottie_success = load_lottieurl("https://assets2.lottiefiles.com/packages/lf20_j1adxtyb.json")
lottie_error = load_lottieurl("https://assets2.lottiefiles.com/packages/lf20_u7vgd4gx.json")  # Optional: Add an error animation

# Set page configuration
st.set_page_config(page_title="📄 Document Summarizer", page_icon="📄", layout="centered", initial_sidebar_state="auto")

# Header section
st.title("📄 **Document Summarizer** 📄")
st.markdown("""
    Welcome to the **Document Summarizer**! Upload your markdown files, choose your preferred summary format and model, provide necessary credentials, and download the summarized content effortlessly.
""")

# Display upload animation
if lottie_upload:
    st_lottie(lottie_upload, height=200, key="upload")

# File Upload and Format Selection
st.markdown("---")
st.header("🚀 Get Your Document Summarized")

# File uploader
uploaded_file = st.file_uploader("Upload your Markdown file 📄", type=["md"])

# Model selection
model = st.selectbox(
    "Choose the summarization model:",
    ("Ollama", "OpenAI")
)

# Model-specific credentials
if model == "Ollama":
    api_url = st.text_input("Ollama API URL:", value="http://ollama:11434")
    api_key = st.text_input("Ollama API Key:", type="password")
elif model == "OpenAI":
    api_key = st.text_input("OpenAI API Key:", type="password")

# Output format selection
output_format = st.selectbox(
    "Choose the summary format:",
    ("Markdown (.md)", "JSON (.json)")
)

# Submit Button and Processing
if st.button("✨ Summarize Document ✨") and uploaded_file is not None:
    with st.spinner("🔄 Initiating summarization job..."):
        # Prepare the request
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/markdown")}
        params = {
            "model": model.lower(),
            "format": "markdown" if output_format == "Markdown (.md)" else "json"
        }
        if model == "Ollama":
            params["api_url"] = api_url
            params["api_key"] = api_key
        elif model == "OpenAI":
            params["api_key"] = api_key

        try:
            # Replace with your FastAPI backend URL
            backend_url = "http://backend:8001/summarize"

            response = requests.post(backend_url, files=files, params=params)

            if response.status_code == 202:
                job_id = response.json().get("job_id")
                st.success("🎉 Summarization job initiated successfully!")

                # Start polling for job status
                global_progress_bar = st.progress(0)
                section_progress_bar = st.progress(0)
                chunk_progress_bar = st.progress(0)
                status_text = st.empty()

                while True:
                    status_response = requests.get(f"http://backend:8001/status/{job_id}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        global_progress = int(status_data.get("progress", 0))
                        section_progress = int(status_data.get("section_progress", 0))
                        chunk_current = status_data.get("chunk_current", 0)
                        chunk_total = status_data.get("chunk_total", 1)
                        chunk_progress = int((chunk_current / chunk_total) * 100) if chunk_total > 0 else 0
                        status_message = status_data.get("status_message", "")

                        global_progress_bar.progress(global_progress)
                        section_progress_bar.progress(section_progress)
                        chunk_progress_bar.progress(chunk_progress)
                        status_text.text(f"Status: {status_message}")

                        if status_data["status"] == "SUCCESS":
                            break
                        elif status_data["status"] == "FAILURE":
                            break
                    else:
                        status_text.text("❌ Failed to retrieve job status.")
                        break

                    time.sleep(2)  # Poll every 2 seconds

                # Retrieve the result
                if status_data["status"] == "SUCCESS":
                    result_response = requests.get(f"http://backend:8001/result/{job_id}")
                    if result_response.status_code == 200:
                        result_data = result_response.json()
                        summary_markdown = result_data.get("summary_markdown", "")
                        summaries_json = result_data.get("summaries_json", {})

                        st.success("🎉 Summary generated successfully!")
                        if lottie_success:
                            st_lottie(lottie_success, height=150, key="success")

                        if output_format == "Markdown (.md)":
                            st.download_button(
                                label="📥 Download Markdown Summary",
                                data=summary_markdown,
                                file_name=f"summary_{uploaded_file.name}",
                                mime="text/markdown"
                            )
                        else:
                            summary_str = json.dumps(summaries_json, indent=4, ensure_ascii=False)
                            st.download_button(
                                label="📥 Download JSON Summary",
                                data=summary_str,
                                file_name=f"summary_{uploaded_file.name.split('.')[0]}.json",
                                mime="application/json"
                            )
                    else:
                        st.error(f"❌ Error retrieving the summary: {result_response.json().get('detail', 'Unknown error')}")
                        if lottie_error:
                            st_lottie(lottie_error, height=150, key="error")
                elif status_data["status"] == "FAILURE":
                    st.error(f"❌ Summarization failed: {status_data.get('status_message', 'Unknown error')}")
                    if lottie_error:
                        st_lottie(lottie_error, height=150, key="error")
            else:
                st.error(f"❌ Error initiating summarization: {response.json().get('detail', 'Unknown error')}")
                if lottie_error:
                    st_lottie(lottie_error, height=150, key="error")
        except requests.exceptions.ConnectionError:
            st.error("❌ Could not connect to the backend. Please ensure the FastAPI server and Celery worker are running.")
            if lottie_error:
                st_lottie(lottie_error, height=150, key="error")
        except Exception as e:
            st.error(f"❌ An unexpected error occurred: {str(e)}")
            if lottie_error:
                st_lottie(lottie_error, height=150, key="error")

# Footer
st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    cute_image_url = "https://placekitten.com/400/300"
    st.image(cute_image_url, use_column_width=True, caption="🐾 Thank you for using Document Summarizer! 🐾")

# Additional Styling
st.markdown(
    """
    <style>
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        padding: 10px 24px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 12px;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    </style>
    """,
    unsafe_allow_html=True
)
