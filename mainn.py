import os
import shutil
import subprocess
import tempfile
import time
from dotenv import load_dotenv
import google.generativeai as genai
import pytesseract
from pdf2image import convert_from_path
from pypdf import PdfReader, PdfWriter
from pypdf.errors import PdfReadError

# Load environment variables from .env file
load_dotenv()

# --- CONFIGURATION ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SOFFICE_PATH = os.getenv("SOFFICE_PATH")
POPPLER_PATH = os.getenv("POPPLER_PATH")
MODEL_NAME = 'gemini-1.5-flash-latest'
PAGES_TO_PROCESS = 2

# Validate that all required environment variables are set
if not all([GEMINI_API_KEY, SOFFICE_PATH, POPPLER_PATH]):
    raise RuntimeError("One or more required environment variables (GEMINI_API_KEY, SOFFICE_PATH, POPPLER_PATH) are not set. Please create a .env file and set them.")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(MODEL_NAME)

REWRITE_PROMPT = """Rewrite the following text, intelligently structuring it with HTML to improve readability.
Format the output as clean HTML body content, ready to be inserted into a <body> tag.
- Analyze the text to identify titles, subtitles, and key points.
- Use heading tags (e.g., <h1>, <h2>, <h3>) for titles and section headers.
- Use the <strong> tag to bold important keywords, phrases, or labels.
- Use <p> tags for paragraphs. Create lists (<ul> or <ol>) if the content is suitable for it.
- Use <br> for line breaks only when absolutely necessary within a paragraph.
- VERY IMPORTANT: Do NOT include <html>, <head>, or <body> tags in your response.

Here is the text:
"""

# --- HELPER FUNCTIONS ---

def get_poppler_env():
    """Returns an environment dictionary with Poppler's bin directory added to the PATH."""
    env = os.environ.copy()
    if POPPLER_PATH and POPPLER_PATH not in env.get('PATH', ''):
        env['PATH'] = f"{POPPLER_PATH};{env.get('PATH', '')}"
    return env

def get_pdf_page_count(pdf_path):
    """Returns the number of pages in a PDF file."""
    try:
        with open(pdf_path, 'rb') as f:
            reader = PdfReader(f)
            return len(reader.pages)
    except PdfReadError:
        print(f"pypdf could not read {os.path.basename(pdf_path)}. It may be corrupted.")
        return 0
    except Exception as e:
        print(f"Could not get page count for {os.path.basename(pdf_path)}: {e}")
        return 0

def check_if_scanned(pdf_path):
    """
    Checks if a PDF is likely scanned by attempting to extract text from the first page.
    If very little text is found, it's assumed to be scanned.
    """
    pdftotext_cmd = os.path.join(POPPLER_PATH, "pdftotext.exe")
    command = [pdftotext_cmd, "-f", "1", "-l", "1", pdf_path, "-"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', check=False, env=get_poppler_env())
        first_page_text = result.stdout.strip()
        return result.returncode != 0 or len(first_page_text.split()) < 20
    except FileNotFoundError:
        print(f"Scan Check Error: '{pdftotext_cmd}' not found. Check POPPLER_PATH.")
        return False
    except Exception as e:
        print(f"Scan Check Error: {e}")
        return False # Assume text-based on error

def run_ocr_on_pdf(pdf_path, num_pages=2):
    """Performs OCR on the first few pages of a scanned PDF."""
    try:
        images = convert_from_path(pdf_path, poppler_path=POPPLER_PATH, last_page=num_pages)
        return "".join(pytesseract.image_to_string(image, timeout=60) + "\n\n" for image in images)
    except Exception as e:
        print(f"OCR Error: {e}. Check Tesseract installation and PATH.")
        return None

def extract_text_from_pdf(pdf_path, num_pages=2):
    """Extracts text from the first few pages of a text-based PDF."""
    pdftotext_cmd = os.path.join(POPPLER_PATH, "pdftotext.exe")
    command = [pdftotext_cmd, "-l", str(num_pages), pdf_path, "-"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', check=True, env=get_poppler_env())
        return result.stdout
    except FileNotFoundError:
        print(f"Text Extraction Error: '{pdftotext_cmd}' not found. Check POPPLER_PATH.")
        return None
    except subprocess.CalledProcessError as e:
        print(f"Text Extraction Error: pdftotext failed for {os.path.basename(pdf_path)}: {e.stderr}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during text extraction: {e}")
        return None

def rewrite_text_with_ai(text):
    """Sends text to the Gemini API for rewriting."""
    if not text or not text.strip():
        return ""
    try:
        response = model.generate_content(REWRITE_PROMPT + text)
        return response.text
    except Exception as e:
        print(f"AI Error: {e}")
        return None

def convert_html_to_pdf(html_path):
    """Uses LibreOffice to convert an HTML file to a PDF."""
    if not os.path.exists(SOFFICE_PATH):
        print(f"LibreOffice executable not found at '{SOFFICE_PATH}'. Check .env file.")
        return None
    try:
        command = f'"{os.path.normpath(SOFFICE_PATH)}" --headless --convert-to pdf --outdir "{os.path.dirname(html_path)}" "{html_path}"'
        print(f"Running command: {command}")
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("LibreOffice STDOUT:", result.stdout)
        print("LibreOffice STDERR:", result.stderr)
        
        expected_pdf = os.path.splitext(html_path)[0] + ".pdf"
        if os.path.exists(expected_pdf):
            return expected_pdf
        print("Expected PDF not found after conversion:", expected_pdf)
        return None
    except subprocess.CalledProcessError as e:
        print(f"LibreOffice conversion failed with return code {e.returncode}:")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return None
    except Exception as e:
        print(f"An unexpected error occurred during HTML to PDF conversion: {e}")
        return None

def split_pdf(original_pdf_path, start_page, output_pdf_path):
    """Extracts pages from a PDF and saves them to a new file."""
    try:
        reader = PdfReader(original_pdf_path)
        writer = PdfWriter()
        for page in reader.pages[start_page - 1:]:
            writer.add_page(page)
        with open(output_pdf_path, "wb") as f:
            writer.write(f)
        return True
    except Exception as e:
        print(f"Error splitting PDF: {e}")
        return False

def merge_pdfs(pdf_paths, final_output_path):
    """Merges a list of PDF files into a single output file."""
    pdfunite_cmd = os.path.join(POPPLER_PATH, "pdfunite.exe")
    command = [pdfunite_cmd] + pdf_paths + [final_output_path]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True, env=get_poppler_env())
        return True
    except FileNotFoundError:
        print(f"Merge Error: '{pdfunite_cmd}' not found. Check POPPLER_PATH.")
        return False
    except subprocess.CalledProcessError as e:
        print(f"PDF Merge Error: pdfunite failed with stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during merge: {e}")
        return False

# --- MAIN PROCESSING FUNCTION ---

def process_pdf(input_pdf_path, output_pdf_path):
    """
    Processes a single PDF file by rewriting the first few pages with an AI model,
    and then re-combining it with the rest of the original document.
    """
    temp_files = []
    try:
        print(f"\n--- Starting processing for: {os.path.basename(input_pdf_path)} ---")
        page_count = get_pdf_page_count(input_pdf_path)
        if page_count == 0:
            return False

        # 1. Extract text from the first few pages (via OCR or direct extraction)
        print(f"Step 1: Extracting text from first {PAGES_TO_PROCESS} pages...")
        full_text = run_ocr_on_pdf(input_pdf_path, num_pages=PAGES_TO_PROCESS) if check_if_scanned(input_pdf_path) else extract_text_from_pdf(input_pdf_path, num_pages=PAGES_TO_PROCESS)
        if not full_text:
            print("Extraction failed. Aborting.")
            return False

        # 2. Rewrite text with AI and create an intermediate HTML file
        print("Step 2: Rewriting text with AI...")
        rewritten_html_body = rewrite_text_with_ai(full_text)
        if not rewritten_html_body:
            print("AI rewrite failed. Aborting.")
            return False

        html_content = f"""
        <!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Processed PDF</title>
        <style>body{{font-family:sans-serif;line-height:1.6}}h1,h2,h3{{font-weight:600}}</style></head>
        <body>{rewritten_html_body}</body></html>
        """
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as temp_html:
            temp_html.write(html_content)
            temp_files.append(temp_html.name)

        # 3. Convert the generated HTML to a PDF
        print("Step 3: Converting rewritten HTML to PDF...")
        rewritten_pdf_path = convert_html_to_pdf(temp_html.name)
        if not rewritten_pdf_path:
            return False
        temp_files.append(rewritten_pdf_path)

        # 4. Combine the new front page(s) with the rest of the original PDF
        pdfs_to_merge = [rewritten_pdf_path]
        if page_count > PAGES_TO_PROCESS:
            print(f"Step 4: Appending original pages from page {PAGES_TO_PROCESS + 1}...")
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_remaining_pdf:
                if split_pdf(input_pdf_path, start_page=PAGES_TO_PROCESS + 1, output_pdf_path=temp_remaining_pdf.name):
                    pdfs_to_merge.append(temp_remaining_pdf.name)
                    temp_files.append(temp_remaining_pdf.name)

        # 5. Merge all parts into the final output file
        print("Step 5: Merging PDF parts into final output...")
        merge_success = merge_pdfs(pdfs_to_merge, output_pdf_path) if len(pdfs_to_merge) > 1 else (shutil.copyfile(pdfs_to_merge[0], output_pdf_path) and True)
        
        return merge_success

    except Exception as e:
        print(f"An unexpected error occurred in process_pdf: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 6. Clean up all temporary files
        print("Step 6: Cleaning up temporary files...")
        for f in temp_files:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except Exception as e:
                print(f"Failed to delete temp file {f}: {e}")
        print("--- Processing finished ---")