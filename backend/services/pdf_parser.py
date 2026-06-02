"""
PDF Parser — Extracts raw text from PDF exam papers.

Uses PyMuPDF (fitz) for text extraction. Falls back to pdfplumber
if PyMuPDF returns empty text (e.g., scanned PDFs).
"""

import fitz  # PyMuPDF
import pdfplumber
import io
import re
import pytesseract
from PIL import Image

# Configure Tesseract OCR path (Windows)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract all text from a PDF file.
    Supports both digital and scanned/image-based PDFs.

    Args:
        pdf_bytes: Raw PDF file bytes

    Returns:
        Extracted text as a single string with page separators
    """
    # Try PyMuPDF first (fast, good for digital PDFs)
    text = _extract_with_pymupdf(pdf_bytes)

    # Fallback to pdfplumber if PyMuPDF got nothing useful
    if len(text.strip()) < 50:
        text = _extract_with_pdfplumber(pdf_bytes)

    # If still no text, try OCR on scanned pages
    if len(text.strip()) < 20:
        text = _extract_with_ocr(pdf_bytes)

    if len(text.strip()) < 10:
        raise ValueError(
            "Could not extract text from PDF. "
            "The file may be corrupted or completely blank."
        )

    return text.strip()


def _extract_with_pymupdf(pdf_bytes: bytes) -> str:
    """Extract text using PyMuPDF."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        page_text = page.get_text("text")
        if page_text.strip():
            pages.append(page_text)
    doc.close()
    return "\n\n".join(pages)


def _extract_with_pdfplumber(pdf_bytes: bytes) -> str:
    """Extract text using pdfplumber (better for tables/complex layouts)."""
    pages = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text and page_text.strip():
                pages.append(page_text)
    return "\n\n".join(pages)


def _extract_with_ocr(pdf_bytes: bytes) -> str:
    """
    Last-resort text extraction for scanned/image-based PDFs.
    Tries multiple strategies before giving up.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)

        # Strategy 1: Try extracting text with "dict" mode (sometimes gets more)
        try:
            blocks = page.get_text("dict")["blocks"]
            block_texts = []
            for b in blocks:
                if b.get("type") == 0:  # text block
                    for line in b.get("lines", []):
                        for span in line.get("spans", []):
                            t = span.get("text", "").strip()
                            if t:
                                block_texts.append(t)
            if block_texts:
                pages.append(" ".join(block_texts))
                continue
        except Exception:
            pass

        # Strategy 2: Try pytesseract OCR
        try:
            pix = page.get_pixmap(dpi=200)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            page_text = pytesseract.image_to_string(img)
            if page_text and page_text.strip():
                pages.append(page_text.strip())
                continue
        except Exception as e:
            print(f"[PDF Parser] OCR not available: {e}")

        # Strategy 3: Try raw text extraction
        try:
            raw = page.get_text("rawdict")
            raw_texts = []
            for b in raw.get("blocks", []):
                if b.get("type") == 0:
                    for line in b.get("lines", []):
                        for span in line.get("spans", []):
                            t = span.get("text", "").strip()
                            if t:
                                raw_texts.append(t)
            if raw_texts:
                pages.append(" ".join(raw_texts))
        except Exception:
            pass

    doc.close()
    return "\n\n".join(pages)


def extract_questions(raw_text: str) -> list[dict]:
    """
    Split raw exam text into individual questions.

    Handles common patterns:
    - Q1, Q2, Q.1, Q.2
    - 1., 2., 3.
    - 1), 2), 3)
    - Question 1, Question 2

    Returns:
        List of dicts: [{"number": 1, "text": "..."}, ...]
    """
    # Multiple patterns ordered by specificity
    patterns = [
        # Q1, Q.1, Q 1, Question 1 (most reliable)
        r'(?:^|\n)\s*Q(?:uestion)?\s*[.\s]*(\d+)',
        # (1), (2) — parenthesized numbers at line start
        r'(?:^|\n)\s*\((\d+)\)',
    ]

    # Try each pattern
    for pattern in patterns:
        matches = list(re.finditer(pattern, raw_text, re.IGNORECASE | re.MULTILINE))
        if len(matches) >= 3:  # Need at least 3 questions to be confident
            return _build_questions_from_matches(matches, raw_text)

    # Last resort: Try "number." or "number)" but ONLY at start of line
    # and only for reasonable question numbers (1-50)
    pattern = r'(?:^|\n)\s*(\d{1,2})\s*[.)]\s+[A-Z]'
    matches = list(re.finditer(pattern, raw_text, re.MULTILINE))
    # Filter to only sequential-ish numbers
    if len(matches) >= 3:
        nums = [int(m.group(1)) for m in matches]
        # Check if numbers are roughly sequential (not random page/marks numbers)
        if nums[0] <= 5 and max(nums) <= 50:
            return _build_questions_from_matches(matches, raw_text)

    # Fallback: split by paragraphs
    return _extract_questions_by_paragraphs(raw_text)


def _build_questions_from_matches(matches, raw_text):
    """Build question list from regex matches."""
    questions = []
    for i, match in enumerate(matches):
        # Get question number from first capturing group
        q_num = int(match.group(1))

        # Get question text (from this match to next match, or end)
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw_text)
        q_text = raw_text[start:end].strip()

        # Clean up the text
        q_text = re.sub(r'\s+', ' ', q_text)

        if len(q_text) > 15:  # Skip very short fragments
            questions.append({
                "number": q_num,
                "text": q_text[:2000],
            })

    return questions


def _extract_questions_by_paragraphs(raw_text: str) -> list[dict]:
    """
    Fallback: Split text by paragraphs when structured question numbering
    isn't found. Groups text into substantial chunks.
    """
    # Split by double newlines or substantial gaps
    paragraphs = re.split(r'\n\s*\n', raw_text)

    questions = []
    q_num = 1

    for para in paragraphs:
        para = para.strip()
        para = re.sub(r'\s+', ' ', para)

        # Skip headers, page numbers, and very short text
        if len(para) < 50:
            continue
        # Skip common header patterns
        if re.match(r'^(page|university|exam|semester|time|marks|instructions|roll|reg|date|subject|max|note|section)', para, re.I):
            continue

        questions.append({
            "number": q_num,
            "text": para[:2000],
        })
        q_num += 1

    # If we got too many "questions" (>50), something is wrong — merge them
    if len(questions) > 50:
        merged = []
        for i in range(0, len(questions), 3):
            chunk = questions[i:i+3]
            merged_text = " ".join(q["text"] for q in chunk)
            merged.append({
                "number": len(merged) + 1,
                "text": merged_text[:2000],
            })
        return merged

    return questions

