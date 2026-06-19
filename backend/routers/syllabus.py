"""
Syllabus Router — Manage syllabus chapters for subjects.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from pydantic import BaseModel
from middleware.auth import get_current_user
from db.supabase_client import get_supabase

router = APIRouter(tags=["Syllabus"])


# ============================================================
# POST /syllabus/extract — Extract chapters from syllabus PDF
# ============================================================
@router.post("/syllabus/extract")
async def extract_chapters_from_pdf(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """
    Upload a syllabus PDF and extract chapter/unit names using AI.
    Returns extracted chapters for user review — does NOT save to DB.
    """
    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted.",
        )

    # Read file bytes
    try:
        pdf_bytes = await file.read()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read uploaded file.",
        )

    if len(pdf_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    if len(pdf_bytes) > 20 * 1024 * 1024:  # 20MB limit
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size is 20MB.",
        )

    # Extract text from PDF
    try:
        from services.pdf_parser import extract_text_from_pdf
        raw_text = extract_text_from_pdf(pdf_bytes)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read PDF: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF parsing failed: {str(e)}",
        )

    # Extract chapters using AI
    try:
        from services.groq_service import extract_syllabus_chapters
        chapters = extract_syllabus_chapters(raw_text)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI extraction failed: {str(e)}",
        )

    return {"chapters": chapters}


class CreateChapterRequest(BaseModel):
    subject_id: str
    chapter_name: str


@router.post("/syllabus")
async def create_chapter(
    body: CreateChapterRequest,
    user: dict = Depends(get_current_user),
):
    """Add a syllabus chapter to a subject."""
    if not body.chapter_name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chapter name cannot be empty.",
        )

    try:
        supabase = get_supabase()

        # Verify subject ownership
        check = (
            supabase.table("subjects")
            .select("id")
            .eq("id", body.subject_id)
            .eq("user_id", user["id"])
            .execute()
        )
        if not check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found.",
            )

        # Check for existing chapter number to auto-increment
        existing = (
            supabase.table("syllabus_chapters")
            .select("chapter_order")
            .eq("subject_id", body.subject_id)
            .order("chapter_order", desc=True)
            .limit(1)
            .execute()
        )

        next_number = 1
        if existing.data:
            next_number = (existing.data[0]["chapter_order"] or 0) + 1

        result = (
            supabase.table("syllabus_chapters")
            .insert({
                "subject_id": body.subject_id,
                "chapter_order": next_number,
                "chapter_name": body.chapter_name.strip(),
            })
            .execute()
        )

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create chapter.",
            )

        return result.data[0]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create chapter: {str(e)}",
        )


@router.get("/syllabus/{subject_id}")
async def list_chapters(
    subject_id: str,
    user: dict = Depends(get_current_user),
):
    """List all syllabus chapters for a subject."""
    try:
        supabase = get_supabase()

        # Verify ownership
        check = (
            supabase.table("subjects")
            .select("id")
            .eq("id", subject_id)
            .eq("user_id", user["id"])
            .execute()
        )
        if not check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found.",
            )

        result = (
            supabase.table("syllabus_chapters")
            .select("id, chapter_order, chapter_name")
            .eq("subject_id", subject_id)
            .order("chapter_order")
            .execute()
        )

        return {"chapters": result.data or []}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list chapters: {str(e)}",
        )
