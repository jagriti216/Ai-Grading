import pdfplumber
import os


def extract_typed_pdf(pdf_path: str) -> dict:
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    result = {}

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            result[f"page_{i+1}"] = text.strip() if text else ""

    return result


def is_typed_pdf(pdf_path: str) -> bool:
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if len(pdf.pages) == 0:
                return False
            # check first 2 pages in case page 1 is a blank cover
            for page in pdf.pages[:2]:
                text = page.extract_text()
                if text and len(text.strip()) > 20:
                    return True
        return False
    except Exception:
        return False
