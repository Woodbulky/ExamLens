"""
Syllabus Router — Manage syllabus chapters for subjects.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from middleware.auth import get_current_user
from db.supabase_client import get_supabase

router = APIRouter(tags=["Syllabus"])


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
