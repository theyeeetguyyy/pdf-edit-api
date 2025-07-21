# PDF AI Processor

A Flask-based web application that processes PDF files. It uses the Google Gemini API to rewrite the first two pages of a PDF and then reassembles the document. This project is designed to be run locally and is configured via an `.env` file.

---

## Features

- **Web UI**: A clean, simple web interface to upload a PDF file.
- **AI-Powered Rewriting**: Leverages the Gemini API to intelligently rewrite text.
- **Text & Scanned PDF Support**: Handles both text-based and scanned (image-based) PDFs using OCR (Tesseract).
- **Secure Configuration**: Uses an `.env` file for API keys and local system paths, keeping them out of version control.
- **Robust Processing**: Manages temporary files securely and cleans up after each request.

---

## 1. System Requirements

This project requires the following applications to be installed on your system. **They cannot be installed via `pip`**.

| Dependency        | Purpose                    | Installation Link                                                              |
| ----------------- | -------------------------- | ------------------------------------------------------------------------------ |
| **LibreOffice**   | HTML to PDF Conversion     | [libreoffice.org/download](https://www.libreoffice.org/download/download/)     |
| **Poppler**       | PDF Text Extraction/Utils  | [github.com/oschwartz10612/poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases/) |
| **Tesseract-OCR** | OCR for Scanned PDFs       | [github.com/tesseract-ocr/tesseract](https://github.com/tesseract-ocr/tesseract) |

After installing Tesseract, ensure its installation directory is added to your system's `PATH` environment variable.

---

## 2. Setup & Installation

**Step 1: Clone the repository**
```bash
git clone <your-repo-url>
cd <your-repo-folder>/api
```

**Step 2: Install Python Dependencies**
Ensure you have Python 3.8+ installed. It is recommended to use a virtual environment.
```bash
pip install -r requirements.txt
```

**Step 3: Create and Configure `.env` file**
Create a new file named `.env` in the `api` directory by copying the example:
```bash
# In Windows command prompt
copy .env.example .env

# In PowerShell
cp .env.example .env
```
Now, open the `.env` file and fill in your specific values:

```plaintext
# .env
# Secret key for Gemini API
GEMINI_API_KEY="your_actual_gemini_api_key_here"

# Full path to your LibreOffice executable
SOFFICE_PATH="C:\Program Files\LibreOffice\program\soffice.exe"

# Full path to your Poppler 'bin' directory
POPPLER_PATH="C:\path\to\your\poppler-24.08.0\Library\bin"
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