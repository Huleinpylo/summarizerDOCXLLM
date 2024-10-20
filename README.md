
# 📄 Document Chapter Summarizer

Welcome to the **Document Chapter Summarizer** project! This application allows users to upload Word documents (.docx) and receive chapter-wise summaries using AI-powered summarization tools like _LangChain_ and _Ollama LLM_. Built with FastAPI for the backend and Streamlit for the frontend, the app is designed for ease of use and seamless interaction.

## 📦 Project Structure

This project contains the following key components:

*   **frontend/** - Contains the Streamlit app for the user interface.
*   **backend/** - FastAPI server that handles file uploads and communicates with the summarizer.
*   **summarizer.py** - Core summarization logic, handling document reading, chapter splitting, and summarization.
*   **app.py** - FastAPI routes for handling file uploads and returning summaries.

## 🚀 Getting Started

Follow the steps below to set up and run the project on your local machine:

### 1\. Clone the repository

```
git clone https://github.com/Huleinpylo/summarizerDOCXLLM.git
```

### 2\. Set up a Python virtual environment

```
python -m venv .venv
source .venv/bin/activate   # On Windows, use .venv\Scripts\activate
```

### 3\. Install the required dependencies

```
pip install -r requirements.txt
```

### 4\. Run the backend server (FastAPI)

Navigate to the `backend/` directory and run the following command:

```
uvicorn app:app --host 0.0.0.0 --port 8001 --reload
```

### 5\. Run the frontend (Streamlit)

In a separate terminal, run the following command to start the Streamlit app:

```
streamlit run frontend/streamlit_app.py
```

## 🔧 Usage

Once the backend and frontend are running, you can access the Streamlit app at `http://localhost:8501`.

To use the app:

*   Upload a Word document (.docx).
*   Click the **Summarize** button.
*   View the chapter-wise summaries in the app.

**Note:** Ensure that the Word document has structured chapters with titles (e.g., `Heading 1` or `Title` styles) for accurate summarization.

## 🔗 API Endpoints

The FastAPI backend provides the following endpoint:

*   `POST /summarize` - Uploads a Word document and returns chapter-wise summaries.

### Sample API Request

```
curl -X POST "http://localhost:8001/summarize" \
  -F "file=@/path/to/your/document.docx" \
  -F "session_id=your-session-id"
```

## 🛠️ Technologies Used

*   **Python** - Core programming language.
*   **FastAPI** - Backend framework for building the API.
*   **Streamlit** - Frontend framework for creating the web interface.
*   **LangChain** - Used for AI-driven summarization.
*   **Ollama LLM** - The language model for generating summaries.
*   **python-docx** - Library for parsing and reading Word documents.

## 💡 Key Features

*   Upload a Word document (.docx) and get AI-generated summaries of each chapter.
*   Simple and intuitive UI with real-time feedback on file uploads and summarization status.
*   Handles large documents with structured chapter headings for efficient summarization.
*   Supports session management to allow users to start a new session or continue an existing one.

## ⚠️ Error Handling

The app provides the following error handling mechanisms:

*   **Invalid File Type:** The app only accepts .docx files. If an unsupported file type is uploaded, an error message is displayed.
*   **Summarization Errors:** If the backend fails to summarize a document, an error message is shown on the frontend.

## 🔒 Security Considerations

For production, consider the following security enhancements:

*   Limit CORS to specific trusted origins.
*   Implement authentication and authorization mechanisms to secure API endpoints.
*   Use HTTPS for secure communication between the frontend and backend.

## 📄 License

This project is licensed under the **MIT License**. See the `LICENSE` file for more details.

## 🤝 Contributing

Contributions are welcome! To contribute:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature`).
3.  Commit your changes (`git commit -m 'Add your feature'`).
4.  Push to the branch (`git push origin feature/your-feature`).
5.  Create a Pull Request.

## 🧑‍💻 Authors

Developed by **Xcom** and **OCYAN** and the team.
