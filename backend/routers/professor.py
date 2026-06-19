"""
Professor Router — Dashboard, AI suggestions, and comparison endpoints
for professors/admins.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from middleware.auth import get_current_user
from db.supabase_client import get_supabase

router = APIRouter(prefix="/professor", tags=["Professor"])


def _require_professor(user: dict):
    """Helper to verify user has professor role."""
    supabase = get_supabase()
    profile = (
        supabase.table("profiles")
        .select("role")
        .eq("id", user["id"])
        .execute()
    )
    role = profile.data[0].get("role", "student") if profile.data else "student"
    if role != "professor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Professor access required.",
        )


@router.get("/dashboard")
async def professor_dashboard(user: dict = Depends(get_current_user)):
    """Get professor dashboard stats and exam list."""
    _require_professor(user)

    supabase = get_supabase()
    user_id = user["id"]

    # Get all completed analyses
    analyses = (
        supabase.table("analyses")
        .select("id, subject_id, efs_score, efs_label, tbi_score, scs_score, rp_score, total_questions, created_at")
        .eq("user_id", user_id)
        .eq("status", "done")
        .order("created_at", desc=True)
        .execute()
    )

    if not analyses.data:
        return {
            "stats": {
                "total_exams": 0,
                "avg_efs": None,
                "best_efs": None,
                "worst_efs": None,
                "total_questions": 0,
            },
            "exams": [],
        }

    # Get subject names
    subject_ids = list(set(a["subject_id"] for a in analyses.data))
    subjects = (
        supabase.table("subjects")
        .select("id, name")
        .in_("id", subject_ids)
        .execute()
    )
    subject_map = {s["id"]: s["name"] for s in (subjects.data or [])}

    # Calculate stats
    efs_scores = [a["efs_score"] for a in analyses.data if a.get("efs_score") is not None]
    total_questions = sum(a.get("total_questions", 0) for a in analyses.data)

    stats = {
        "total_exams": len(analyses.data),
        "avg_efs": round(sum(efs_scores) / len(efs_scores), 2) if efs_scores else None,
        "best_efs": round(max(efs_scores), 2) if efs_scores else None,
        "worst_efs": round(min(efs_scores), 2) if efs_scores else None,
        "total_questions": total_questions,
    }

    # Build exam list
    exams = []
    for a in analyses.data:
        exams.append({
            "analysis_id": a["id"],
            "subject_name": subject_map.get(a["subject_id"], "Unknown"),
            "efs_score": a.get("efs_score"),
            "efs_label": a.get("efs_label"),
            "tbi_score": a.get("tbi_score"),
            "scs_score": a.get("scs_score"),
            "rp_score": a.get("rp_score"),
            "total_questions": a.get("total_questions"),
            "created_at": a.get("created_at"),
        })

    return {"stats": stats, "exams": exams}


class ImproveRequest(BaseModel):
    analysis_id: str


@router.post("/improve")
async def get_improvement_suggestions(
    body: ImproveRequest,
    user: dict = Depends(get_current_user),
):
    """Get AI suggestions to improve exam fairness for a specific analysis."""
    _require_professor(user)

    from services.groq_service import _chat_completion_cerebras

    supabase = get_supabase()

    # Get analysis
    analysis = (
        supabase.table("analyses")
        .select("*")
        .eq("id", body.analysis_id)
        .eq("user_id", user["id"])
        .execute()
    )
    if not analysis.data:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    a = analysis.data[0]

    # Get subject name
    subject = (
        supabase.table("subjects")
        .select("name")
        .eq("id", a["subject_id"])
        .execute()
    )
    subject_name = subject.data[0]["name"] if subject.data else "Unknown"

    # Get chapter stats
    stats = (
        supabase.table("chapter_stats")
        .select("chapter_name, questions_asked, expected_questions, bias_score")
        .eq("analysis_id", body.analysis_id)
        .execute()
    )

    # Build context
    chapter_lines = []
    over_tested = []
    under_tested = []
    never_tested = []

    for cs in (stats.data or []):
        asked = cs.get("questions_asked", 0)
        expected = cs.get("expected_questions", 0)
        bias = cs.get("bias_score", 1)
        chapter_lines.append(
            f"  - {cs['chapter_name']}: {asked} asked / {expected} expected (bias: {bias:.2f})"
        )
        if asked == 0:
            never_tested.append(cs["chapter_name"])
        elif bias > 1.5:
            over_tested.append(cs["chapter_name"])
        elif bias < 0.5 and asked > 0:
            under_tested.append(cs["chapter_name"])

    try:
        system_prompt = (
            "You are an exam quality consultant for university professors. "
            "Analyze the exam fairness data and provide specific, actionable "
            "suggestions to improve the balance and fairness of the exam. "
            "Be constructive, professional, and specific."
        )

        user_prompt = (
            f"Analyze this exam and suggest improvements:\n\n"
            f"Subject: {subject_name}\n"
            f"EFS Score: {a.get('efs_score', 'N/A')}/10 ({a.get('efs_label', 'N/A')})\n"
            f"  - Topic Bias Index (TBI): {a.get('tbi_score', 'N/A')}/10\n"
            f"  - Syllabus Coverage (SCS): {a.get('scs_score', 'N/A')}/10\n"
            f"  - Recurrence Penalty (RP): {a.get('rp_score', 'N/A')}/10\n\n"
            f"Chapter breakdown:\n" + "\n".join(chapter_lines) + "\n\n"
            f"Over-tested chapters: {', '.join(over_tested) if over_tested else 'None'}\n"
            f"Under-tested chapters: {', '.join(under_tested) if under_tested else 'None'}\n"
            f"Never tested chapters: {', '.join(never_tested) if never_tested else 'None'}\n\n"
            "Provide 4-6 specific, actionable suggestions to improve the exam's fairness. "
            "Format each suggestion as a clear recommendation with reasoning. "
            "Focus on: chapter coverage balance, question distribution, and topics to add or reduce."
        )

        reply = _chat_completion_cerebras(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
            max_tokens=1500,
        )

        return {
            "analysis_id": body.analysis_id,
            "subject_name": subject_name,
            "efs_score": a.get("efs_score"),
            "efs_label": a.get("efs_label"),
            "suggestions": reply.strip(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate suggestions: {str(e)}",
        )


@router.get("/compare/{analysis_id}")
async def compare_with_average(
    analysis_id: str,
    user: dict = Depends(get_current_user),
):
    """Compare one exam's EFS components against the professor's average."""
    _require_professor(user)

    supabase = get_supabase()

    # Get the specific analysis
    analysis = (
        supabase.table("analyses")
        .select("id, subject_id, efs_score, efs_label, tbi_score, scs_score, rp_score")
        .eq("id", analysis_id)
        .eq("user_id", user["id"])
        .execute()
    )
    if not analysis.data:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    current = analysis.data[0]

    # Get subject name
    subject = (
        supabase.table("subjects")
        .select("name")
        .eq("id", current["subject_id"])
        .execute()
    )
    subject_name = subject.data[0]["name"] if subject.data else "Unknown"

    # Get ALL of this professor's analyses for averaging
    all_analyses = (
        supabase.table("analyses")
        .select("efs_score, tbi_score, scs_score, rp_score")
        .eq("user_id", user["id"])
        .eq("status", "done")
        .execute()
    )

    if not all_analyses.data or len(all_analyses.data) < 2:
        return {
            "current": {
                "subject_name": subject_name,
                "efs_score": current.get("efs_score"),
                "efs_label": current.get("efs_label"),
                "tbi_score": current.get("tbi_score"),
                "scs_score": current.get("scs_score"),
                "rp_score": current.get("rp_score"),
            },
            "average": None,
            "message": "Need at least 2 analyzed exams to compare against average.",
        }

    # Calculate averages
    def safe_avg(key):
        values = [a[key] for a in all_analyses.data if a.get(key) is not None]
        return round(sum(values) / len(values), 2) if values else None

    return {
        "current": {
            "subject_name": subject_name,
            "efs_score": current.get("efs_score"),
            "efs_label": current.get("efs_label"),
            "tbi_score": current.get("tbi_score"),
            "scs_score": current.get("scs_score"),
            "rp_score": current.get("rp_score"),
        },
        "average": {
            "efs_score": safe_avg("efs_score"),
            "tbi_score": safe_avg("tbi_score"),
            "scs_score": safe_avg("scs_score"),
            "rp_score": safe_avg("rp_score"),
            "exam_count": len(all_analyses.data),
        },
        "message": None,
    }
