"""
Chat Router — AI Chat Assistant for ExamLens ("Ask ExamLens")

Provides a conversational AI interface that answers questions
about exam analyses using the user's actual data as context.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from middleware.auth import get_current_user
from db.supabase_client import get_supabase
from services.groq_service import _chat_completion

router = APIRouter(tags=["Chat"])


class ChatRequest(BaseModel):
    message: str
    analysis_id: Optional[str] = None


@router.post("/chat")
async def chat(
    body: ChatRequest,
    user: dict = Depends(get_current_user),
):
    """
    AI Chat Assistant endpoint.
    Accepts a user message and optional analysis_id for context.
    Returns an AI-generated response using the user's exam data.
    """
    if not body.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty.",
        )

    supabase = get_supabase()
    context = ""

    try:
        if body.analysis_id:
            # === Fetch specific analysis context ===
            context = _build_analysis_context(supabase, user["id"], body.analysis_id)
        else:
            # === Fetch general overview context ===
            context = _build_general_context(supabase, user["id"])
    except Exception as e:
        print(f"[Chat] Context fetch warning: {e}")
        context = "No analysis data available yet."

    # Build system prompt
    system_prompt = (
        "You are ExamLens AI Assistant — a helpful, friendly academic assistant "
        "built into the ExamLens exam analysis platform. You help students understand "
        "their exam analysis results and prepare for upcoming exams.\n\n"
        "RESPONSE FORMAT RULES (VERY IMPORTANT):\n"
        "- NEVER use markdown syntax. No *, **, #, ##, ```, or any markdown.\n"
        "- Use plain dashes (-) for bullet points.\n"
        "- Use numbered lists (1. 2. 3.) for ordered items like questions.\n"
        "- Use CAPS or a colon for emphasis instead of bold. Example: 'IMPORTANT:' or 'Answer:'\n"
        "- For questions, use this exact format:\n"
        "  Q1. [question text]\n"
        "      Chapter: [name] | Difficulty: [Easy/Medium/Hard] | Marks: [number]\n"
        "  Q2. [question text]\n"
        "      Chapter: [name] | Difficulty: [Easy/Medium/Hard] | Marks: [number]\n"
        "- Separate sections with a blank line.\n"
        "- Keep responses clean, readable, and under 300 words unless asked for detail.\n\n"
        "CONTENT GUIDELINES:\n"
        "- Be concise and specific. Use numbers and data from the context.\n"
        "- If asked to generate questions, create realistic university-level questions.\n"
        "- If asked about predictions, base your answer on the historical data provided.\n"
        "- If you don't have enough data to answer, say so honestly.\n"
        "- Never make up statistics — only use data from the context below.\n\n"
        f"USER'S DATA CONTEXT:\n{context}"
    )

    try:
        reply = _chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": body.message},
            ],
            temperature=0.4,
            max_tokens=1500,
        )
        return {"reply": reply.strip()}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI response failed: {str(e)}",
        )


def _build_analysis_context(supabase, user_id: str, analysis_id: str) -> str:
    """Build rich context from a specific analysis."""

    # Get analysis record
    analysis = (
        supabase.table("analyses")
        .select("*")
        .eq("id", analysis_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not analysis.data:
        return "Analysis not found."

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
        .eq("analysis_id", analysis_id)
        .execute()
    )

    # Get questions
    questions = (
        supabase.table("questions")
        .select("question_number, question_text, assigned_chapter, difficulty, confidence, year")
        .eq("analysis_id", analysis_id)
        .order("question_number")
        .execute()
    )

    # Get syllabus chapters
    chapters_result = (
        supabase.table("syllabus_chapters")
        .select("chapter_name")
        .eq("subject_id", a["subject_id"])
        .order("chapter_order")
        .execute()
    )
    all_chapters = [ch["chapter_name"] for ch in (chapters_result.data or [])]

    # Get years
    years = sorted(set(q["year"] for q in (questions.data or []) if q.get("year")))

    # Tested/never-tested
    tested = set(cs["chapter_name"] for cs in (stats.data or []) if cs.get("questions_asked", 0) > 0)
    never_tested = [ch for ch in all_chapters if ch not in tested]

    # Difficulty distribution
    diff_dist = {"Easy": 0, "Medium": 0, "Hard": 0}
    for q in (questions.data or []):
        d = q.get("difficulty", "Medium")
        if d in diff_dist:
            diff_dist[d] += 1

    # Build chapter stats string
    chapter_lines = []
    for cs in (stats.data or []):
        status_label = "Fair"
        if cs["questions_asked"] == 0:
            status_label = "Never tested"
        elif cs.get("bias_score", 1) > 1.5:
            status_label = "Over-tested"
        elif cs.get("bias_score", 1) < 0.5 and cs["questions_asked"] > 0:
            status_label = "Under-tested"
        chapter_lines.append(
            f"  - {cs['chapter_name']}: {cs['questions_asked']} questions "
            f"(expected {cs.get('expected_questions', '?')}), status: {status_label}"
        )

    # Build question samples (first 15 for context)
    question_lines = []
    for q in (questions.data or [])[:15]:
        text_preview = (q.get("question_text") or "")[:100]
        question_lines.append(
            f"  Q{q['question_number']} [{q.get('difficulty', '?')}] "
            f"({q.get('assigned_chapter', '?')}): {text_preview}"
        )

    context = (
        f"CURRENT ANALYSIS: {subject_name}\n"
        f"Years analyzed: {', '.join(str(y) for y in years)}\n"
        f"Total questions: {a.get('total_questions', len(questions.data or []))}\n"
        f"EFS Score: {a.get('efs_score', 'N/A')}/10 ({a.get('efs_label', 'N/A')})\n"
        f"  - Topic Bias Index (TBI): {a.get('tbi_score', 'N/A')}/10\n"
        f"  - Syllabus Coverage (SCS): {a.get('scs_score', 'N/A')}/10\n"
        f"  - Recurrence Penalty (RP): {a.get('rp_score', 'N/A')}/10\n\n"
        f"AI Summary: {a.get('ai_summary', 'N/A')}\n\n"
        f"Syllabus chapters ({len(all_chapters)}): {', '.join(all_chapters)}\n\n"
        f"Chapter stats:\n" + "\n".join(chapter_lines) + "\n\n"
        f"Never tested chapters: {', '.join(never_tested) if never_tested else 'None'}\n\n"
        f"Difficulty distribution: Easy={diff_dist['Easy']}, Medium={diff_dist['Medium']}, Hard={diff_dist['Hard']}\n\n"
        f"Sample questions:\n" + "\n".join(question_lines)
    )

    return context


def _build_general_context(supabase, user_id: str) -> str:
    """Build overview context from all user's subjects."""

    # Get all subjects
    subjects = (
        supabase.table("subjects")
        .select("id, name")
        .eq("user_id", user_id)
        .execute()
    )

    if not subjects.data:
        return "No subjects or analyses yet. The user hasn't uploaded any exam papers."

    # Get recent analyses
    analyses = (
        supabase.table("analyses")
        .select("id, subject_id, efs_score, efs_label, total_questions, status, created_at")
        .eq("user_id", user_id)
        .eq("status", "done")
        .order("created_at", desc=True)
        .limit(10)
        .execute()
    )

    subject_map = {s["id"]: s["name"] for s in subjects.data}

    lines = [f"USER HAS {len(subjects.data)} SUBJECT(S):\n"]
    for s in subjects.data:
        lines.append(f"  - {s['name']}")

    if analyses.data:
        lines.append(f"\nRECENT ANALYSES ({len(analyses.data)}):")
        for a in analyses.data:
            name = subject_map.get(a["subject_id"], "Unknown")
            lines.append(
                f"  - {name}: EFS {a.get('efs_score', '?')}/10 "
                f"({a.get('efs_label', '?')}), "
                f"{a.get('total_questions', '?')} questions"
            )
    else:
        lines.append("\nNo completed analyses yet.")

    return "\n".join(lines)
