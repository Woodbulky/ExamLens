"""
Subjects Router — CRUD for exam subjects and syllabus chapters.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from middleware.auth import get_current_user
from db.supabase_client import get_supabase

router = APIRouter(prefix="/subjects", tags=["Subjects"])


class CreateSubjectRequest(BaseModel):
    name: str


class SubjectResponse(BaseModel):
    subject_id: str
    name: str


@router.post("", response_model=SubjectResponse)
async def create_subject(
    body: CreateSubjectRequest,
    user: dict = Depends(get_current_user),
):
    """Create a new subject for the authenticated user."""
    if not body.name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subject name cannot be empty.",
        )

    try:
        supabase = get_supabase()
        result = (
            supabase.table("subjects")
            .insert({"user_id": user["id"], "name": body.name.strip()})
            .execute()
        )

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create subject.",
            )

        subject = result.data[0]
        return SubjectResponse(subject_id=subject["id"], name=subject["name"])

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create subject: {str(e)}",
        )


@router.get("")
async def list_subjects(user: dict = Depends(get_current_user)):
    """List all subjects for the authenticated user with latest analysis info."""
    try:
        supabase = get_supabase()

        # Get subjects for this user
        result = (
            supabase.table("subjects")
            .select("id, name, created_at")
            .eq("user_id", user["id"])
            .order("created_at", desc=True)
            .execute()
        )

        subjects = []
        for s in result.data or []:
            # Count uploads for this subject
            uploads_result = (
                supabase.table("uploads")
                .select("id", count="exact")
                .eq("subject_id", s["id"])
                .execute()
            )
            papers_count = uploads_result.count if uploads_result.count else 0

            # Get latest analysis
            analysis_result = (
                supabase.table("analyses")
                .select("id, efs_score, efs_label, created_at")
                .eq("subject_id", s["id"])
                .eq("status", "done")
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )

            latest = analysis_result.data[0] if analysis_result.data else None

            subjects.append({
                "subject_id": s["id"],
                "name": s["name"],
                "papers_count": papers_count,
                "latest_efs": latest["efs_score"] if latest else None,
                "latest_label": latest["efs_label"] if latest else None,
                "latest_analysis_id": latest["id"] if latest else None,
                "last_analyzed": latest["created_at"] if latest else None,
            })

        return {"subjects": subjects}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list subjects: {str(e)}",
        )


@router.delete("/{subject_id}")
async def delete_subject(
    subject_id: str,
    user: dict = Depends(get_current_user),
):
    """Delete a subject and all associated data."""
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

        # Delete (cascades to uploads, analyses, etc.)
        supabase.table("subjects").delete().eq("id", subject_id).execute()

        return {"deleted": True}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete subject: {str(e)}",
        )
