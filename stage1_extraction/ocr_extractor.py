import os
import fitz
import base64
import json
import random
import requests
from PIL import Image
import io
from dotenv import load_dotenv

from gemini_shared import disable_gemini, gemini_disabled_reason

# Try loading from the root .env first
root_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
if os.path.exists(root_env):
    load_dotenv(root_env)
else:
    # Fallback to local .env
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
    # Generic load_dotenv searching current & parent directories
    load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")


def build_gemini_url(model_name: str) -> str:
    return (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model_name}:generateContent?key=" + (GEMINI_API_KEY or "")
    )


def extract_text_locally(pdf_path: str) -> dict:
    doc = fitz.open(pdf_path)
    result = {}
    for i, page in enumerate(doc):
        try:
            result[f"page_{i+1}"] = page.get_text().strip()
        except Exception:
            result[f"page_{i+1}"] = ""
    doc.close()
    return result


def pdf_page_to_base64(pdf_path: str, page_num: int, dpi: int = 150) -> str:
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)
    img_bytes = pix.tobytes("png")
    doc.close()

    # resize if too large
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    max_dim = 1600
    w, h = img.size
    if max(w, h) > max_dim:
        scale = max_dim / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        img_bytes = buf.getvalue()

    return base64.b64encode(img_bytes).decode("utf-8")


def extract_text_with_gemini(base64_image: str) -> str:
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            "You are an OCR engine. Extract all the text from this image exactly as written. "
                            "Preserve the structure — keep question numbers, answer text, and layout intact. "
                            "Do not summarize, explain, or add anything. Output only the extracted text."
                        )
                    },
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": base64_image
                        }
                    }
                ]
            }
        ]
    }

    response = requests.post(build_gemini_url(GEMINI_MODEL), json=payload, timeout=120)

    if response.status_code == 404:
        fallback_model = "gemini-2.5-flash"
        response = requests.post(build_gemini_url(fallback_model), json=payload, timeout=120)

        if response.status_code == 404:
            raise Exception(f"Gemini model not found: {GEMINI_MODEL} or {fallback_model}")

    if response.status_code in {401, 403, 429}:
        disable_gemini(f"HTTP {response.status_code}: {response.text[:200]}", permanent=True)
        raise RuntimeError(f"Gemini disabled after HTTP {response.status_code}")

    if response.status_code != 200:
        raise Exception(f"Gemini API error {response.status_code}: {response.text}")

    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()


def extract_handwritten_pdf(pdf_path: str) -> dict:
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        return extract_text_locally(pdf_path)

    disabled_reason = gemini_disabled_reason()
    if disabled_reason:
        return extract_text_locally(pdf_path)

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    doc = fitz.open(pdf_path)
    num_pages = len(doc)
    doc.close()

    result = {}

    for i in range(num_pages):
        try:
            b64 = pdf_page_to_base64(pdf_path, i)
            text = extract_text_with_gemini(b64)
            result[f"page_{i+1}"] = text
        except Exception as e:
            result[f"page_{i+1}"] = ""

    if not any(page.strip() for page in result.values()):
        return extract_text_locally(pdf_path)

    return result
