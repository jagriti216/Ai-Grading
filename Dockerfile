FROM python:3.13-slim

WORKDIR /app

# System deps needed by PyMuPDF / pdfplumber for PDF parsing
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml setup.py ./
COPY stage1_extraction ./stage1_extraction
COPY stage2_parser ./stage2_parser
COPY stage3_grading ./stage3_grading
COPY stage4_feedback ./stage4_feedback
COPY stage5_fastapi ./stage5_fastapi
COPY gemini_shared.py ./

RUN pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["uvicorn", "stage5_fastapi.main:app", "--host", "0.0.0.0", "--port", "8000"]
