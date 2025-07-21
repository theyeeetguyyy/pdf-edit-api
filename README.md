# PDF AI Processor

A Flask-based web application that uses the Google Gemini API to rewrite the first two pages of a PDF and then reassembles the document. It features a simple web interface and can handle both text-based and scanned (image-based) PDFs.

---

## Features

- **Web UI**: A clean, simple web interface to upload a PDF file.
- **AI-Powered Rewriting**: Leverages the Gemini API to intelligently rewrite text and structure it with HTML.
- **HTML to PDF Conversion**: Uses Playwright to accurately convert the rewritten HTML content back into a high-quality PDF.
- **Text & Scanned PDF Support**: Handles both text-based PDFs and scanned (image-based) PDFs using OCR (Tesseract).
- **Secure Configuration**: Uses an `.env` file for API keys and local system paths.
- **Robust Processing**: Manages temporary files securely and cleans up after each request.

---

## 1. System Requirements

This project requires the following applications to be installed on your system.

| Dependency | Purpose | Installation Link |
| :--- | :--- | :--- |
| **Poppler** | PDF Text Extraction/Utils | [github.com/oschwartz10612/poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases/) |
| **Tesseract-OCR**| OCR for Scanned PDFs | [github.com/tesseract-ocr/tesseract](https://github.com/tesseract-ocr/tesseract) |

**Important**: After installing Tesseract, you must add its installation directory (e.g., `C:\Program Files\Tesseract-OCR`) to your system's `PATH` environment variable for the application to find it.

---

## 2. Setup & Installation

**Step 1: Clone the repository**
```bash
git clone <your-repo-url>
cd <your-repo-folder>
```

**Step 2: Create a Virtual Environment**
It is highly recommended to use a virtual environment to manage dependencies.
```bash
# Create the environment
python -m venv venv

# Activate the environment
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

**Step 3: Install Python & Playwright Dependencies**
Install all required Python packages and the necessary browser binaries for Playwright.
```bash
# Install Python packages
pip install -r requirements.txt

# Install Playwright browsers
playwright install
```

**Step 4: Create and Configure the `.env` file**
Create a new file named `.env` in the root directory. Add the following environment variables, replacing the placeholder values with your actual paths and API key.

```plaintext
# .env file

# Secret key for Google Gemini API
GEMINI_API_KEY="your_actual_gemini_api_key_here"

# Full path to your Poppler 'bin' directory.
# Make sure to use forward slashes or double backslashes on Windows.
POPPLER_PATH="C:/path/to/your/poppler-24.08.0/Library/bin"
```

---

## 3. Running the Application

With your environment configured, start the Flask development server:
```bash
python api.py
```
The application will be available at **http://127.0.0.1:5000**. Open this URL in your web browser, upload a PDF, and the processed file will be returned as a download.

---

## For Production Use

The default Flask server is for development only. For a production deployment, use a production-grade WSGI server such as **Gunicorn** (for Linux/macOS) or **Waitress** (for Windows). 