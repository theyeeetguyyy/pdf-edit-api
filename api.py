import os
import tempfile
from flask import Flask, request, send_file, render_template_string, after_this_request
from mainn import process_pdf

app = Flask(__name__)

# --- TEMPLATES ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF Processor</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background-color: #f8f9fa; }
        .container { background: #fff; padding: 2.5rem; border-radius: 12px; box-shadow: 0 8px 30px rgba(0,0,0,0.1); text-align: center; width: 90%; max-width: 450px; }
        h1 { color: #343a40; margin-bottom: 2rem; }
        input[type=file] { border: 1px solid #ced4da; padding: 10px; border-radius: 5px; width: 100%; box-sizing: border-box; margin-bottom: 1.5rem; }
        button { background-color: #007bff; color: white; border: none; padding: 1rem 2rem; border-radius: 5px; font-size: 1rem; cursor: pointer; transition: background-color 0.2s; width: 100%; }
        button:hover { background-color: #0056b3; }
        .message { margin-top: 1.5rem; font-size: 0.95rem; }
        .message.error { color: #dc3545; }
    </style>
</head>
<body>
    <div class="container">
        <h1>PDF Processor</h1>
        <p>Upload a PDF to rewrite the first few pages with AI.</p>
        <form method="post" action="/process" enctype="multipart/form-data">
            <input type="file" name="pdf_file" accept="application/pdf" required>
            <button type="submit">Upload & Process</button>
        </form>
        {% if message %}
            <div class="message {{ 'error' if is_error else '' }}">{{ message }}</div>
        {% endif %}
    </div>
</body>
</html>
"""

# --- ROUTES ---
@app.route('/', methods=['GET'])
def index():
    """Renders the main upload page."""
    return render_template_string(HTML_TEMPLATE)

@app.route('/process', methods=['POST'])
def process_endpoint():
    """Handles the PDF file upload, processing, and response."""
    pdf_file = request.files.get('pdf_file')

    if not pdf_file or not pdf_file.filename.lower().endswith('.pdf'):
        return render_template_string(HTML_TEMPLATE, message="Please upload a valid PDF file.", is_error=True), 400

    # Securely create temporary files for input and output
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_in:
            pdf_file.save(temp_in)
            temp_in_path = temp_in.name
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_out:
            temp_out_path = temp_out.name
    except Exception as e:
        print(f"Error creating temporary files: {e}")
        return render_template_string(HTML_TEMPLATE, message="Server error creating temporary files.", is_error=True), 500

    # Process the PDF and handle the response
    try:
        success = process_pdf(temp_in_path, temp_out_path)
        
        if success and os.path.exists(temp_out_path) and os.path.getsize(temp_out_path) > 0:
            @after_this_request
            def cleanup(response):
                """Safely delete temporary files after the request is sent."""
                try:
                    os.remove(temp_in_path)
                    os.remove(temp_out_path)
                except Exception as error:
                    print(f"Error during file cleanup: {error}")
                return response
            
            return send_file(temp_out_path, as_attachment=True, download_name=f"processed_{pdf_file.filename}", mimetype='application/pdf')
        else:
            # If processing fails, clean up immediately
            os.remove(temp_in_path)
            if os.path.exists(temp_out_path): os.remove(temp_out_path)
            return render_template_string(HTML_TEMPLATE, message="Processing failed. Please check server logs.", is_error=True), 500
    except Exception as e:
        print(f"An unexpected error occurred during processing: {e}")
        # Clean up any files that might have been created
        if os.path.exists(temp_in_path): os.remove(temp_in_path)
        if os.path.exists(temp_out_path): os.remove(temp_out_path)
        return render_template_string(HTML_TEMPLATE, message="An internal server error occurred.", is_error=True), 500

if __name__ == '__main__':
    # For development only. Use a production WSGI server like Gunicorn or Waitress for deployment.
    app.run(debug=True, host='0.0.0.0', port=5000)
