import os
import docx
import PyPDF2

def read_document(file_path):
    """
    Reads the text content from a file.
    Supports .txt, .docx, and .pdf files.
    Returns the text content as a string, or an error message if something goes wrong.
    """
    if not os.path.exists(file_path):
        return f"Error: File not found at '{file_path}'"

    _, extension = os.path.splitext(file_path)
    extension = extension.lower()

    try:
        if extension == '.txt':
            return _read_txt(file_path)
        elif extension == '.docx':
            return _read_docx(file_path)
        elif extension == '.pdf':
            return _read_pdf(file_path)
        else:
            return f"Error: Unsupported file type '{extension}'. I can only read .txt, .docx, and .pdf files."
    except Exception as e:
        return f"Error: Could not read file '{os.path.basename(file_path)}'. Reason: {e}"

def _read_txt(file_path):
    """Reads a plain text file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def _read_docx(file_path):
    """Reads a .docx file."""
    doc = docx.Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

def _read_pdf(file_path):
    """Reads a .pdf file."""
    text = ""
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text
