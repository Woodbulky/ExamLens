"""
Dashboard Router — Stats and recent activity for the dashboard home page.
"""

from fastapi import APIRouter, Depends, HTTPException
from middleware.auth import get_current_user
from db.supabase_client import get_supabase

router = APIRouter(tags=["Dashboard"])


@router.get("/dashboard/stats")
async def get_dashboard_stats(user: dict = Depends(get_current_user)):
    """Get summary stats for the dashboard."""
    try:
        supabase = get_supabase()
        user_id = user["id"]

        # Count uploaded papers
        uploads = (
            supabase.table("uploads")
            .select("id")
            .eq("user_id", user_id)
            .execute()
        )
        papers_count = len(uploads.data) if uploads.data else 0

        # Count completed analyses + gather EFS scores
        analyses = (
            supabase.table("analyses")
            .select("id, efs_score")
            .eq("user_id", user_id)
            .eq("status", "done")
            .execute()
        )
        analyses_count = len(analyses.data) if analyses.data else 0

        # Calculate average EFS score
        avg_efs = None
        if analyses.data:
            scores = [a["efs_score"] for a in analyses.data if a.get("efs_score") is not None]
            if scores:
                avg_efs = round(sum(scores) / len(scores), 2)

        # Count subjects
        subjects = (
            supabase.table("subjects")
            .select("id")
            .eq("user_id", user_id)
            .execute()
        )
        subjects_count = len(subjects.data) if subjects.data else 0

        return {
            "papers_uploaded": papers_count,
            "analyses_complete": analyses_count,
            "avg_efs_score": avg_efs,
            "subjects_count": subjects_count,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load stats: {str(e)}")


@router.get("/dashboard/recent")
async def get_recent_analyses(user: dict = Depends(get_current_user)):
    """Get the 5 most recent analyses for the dashboard."""
    try:
        supabase = get_supabase()

        # Get recent analyses
        analyses = (
            supabase.table("analyses")
            .select("id, subject_id, efs_score, efs_label, status, total_questions, created_at")
            .eq("user_id", user["id"])
            .order("created_at", desc=True)
            .limit(5)
            .execute()
        )

        results = []
        for a in (analyses.data or []):
            # Get subject name
            subject = (
                supabase.table("subjects")
                .select("name")
                .eq("id", a["subject_id"])
                .execute()
            )
            subject_name = subject.data[0]["name"] if subject.data else "Unknown"

            results.append({
                "analysis_id": a["id"],
                "subject_name": subject_name,
                "efs_score": a.get("efs_score"),
                "efs_label": a.get("efs_label"),
                "status": a.get("status"),
                "total_questions": a.get("total_questions"),
                "created_at": a.get("created_at"),
            })

        return {"recent": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load recent: {str(e)}")
