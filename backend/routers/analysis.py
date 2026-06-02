"""
Analysis Router — Orchestrates the full exam analysis pipeline.

Pipeline steps:
  1. Fetch uploaded PDFs from Supabase Storage
  2. Extract text from each PDF
  3. Extract individual questions
  4. Classify questions using Groq AI
  5. Calculate EFS Score
  6. Generate AI summary
  7. Save everything to DB
"""

import traceback
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from middleware.auth import get_current_user
from db.supabase_client import get_supabase
from services.pdf_parser import extract_text_from_pdf, extract_questions
from services.groq_service import classify_questions, generate_summary
from services.efs_calculator import calculate_efs

router = APIRouter(tags=["Analysis"])


class AnalyzeRequest(BaseModel):
    upload_ids: list[str]
    subject_id: str


@router.post("/analyze")
async def trigger_analysis(
    body: AnalyzeRequest,
    user: dict = Depends(get_current_user),
):
    """
    Trigger the full analysis pipeline for a set of uploaded PDFs.

    Steps: PDF download → text extraction → question splitting →
           AI classification → EFS calculation → summary generation → save
    """
    supabase = get_supabase()

    # === Validate subject ownership ===
    subject_check = (
        supabase.table("subjects")
        .select("id, name")
        .eq("id", body.subject_id)
        .eq("user_id", user["id"])
        .execute()
    )
    if not subject_check.data:
        raise HTTPException(status_code=404, detail="Subject not found.")

    subject_name = subject_check.data[0]["name"]

    # === Create analysis record with status "processing" ===
    analysis_insert = (
        supabase.table("analyses")
        .insert({
            "subject_id": body.subject_id,
            "user_id": user["id"],
            "status": "processing",
        })
        .execute()
    )
    if not analysis_insert.data:
        raise HTTPException(status_code=500, detail="Failed to create analysis record.")

    analysis_id = analysis_insert.data[0]["id"]

    # Update uploads status to "processing"
    for uid in body.upload_ids:
        supabase.table("uploads").update({"status": "processing"}).eq("id", uid).execute()

    try:
        # === Step 1 & 2: Download PDFs and extract text ===
        all_questions = []
        years = []

        for upload_id in body.upload_ids:
            # Get upload record
            upload_rec = (
                supabase.table("uploads")
                .select("file_path, year, filename")
                .eq("id", upload_id)
                .execute()
            )
            if not upload_rec.data:
                continue

            upload = upload_rec.data[0]
            year = upload.get("year", 0)
            if year not in years:
                years.append(year)

            # Download PDF from storage
            file_bytes = supabase.storage.from_("exam-papers").download(upload["file_path"])

            # Extract text from PDF
            raw_text = extract_text_from_pdf(file_bytes)

            # Extract individual questions
            questions = extract_questions(raw_text)

            # Tag each question with its year
            for q in questions:
                q["year"] = year

            all_questions.extend(questions)

        if not all_questions:
            raise ValueError("No questions could be extracted from the uploaded PDFs.")

        # === Step 3: Get syllabus chapters ===
        chapters_result = (
            supabase.table("syllabus_chapters")
            .select("chapter_name")
            .eq("subject_id", body.subject_id)
            .order("chapter_order")
            .execute()
        )
        chapters = [ch["chapter_name"] for ch in (chapters_result.data or [])]

        if not chapters:
            raise ValueError("No syllabus chapters found for this subject. Add chapters first.")

        # === Step 4: Classify questions with AI ===
        # Update status
        supabase.table("analyses").update({
            "status": "processing",
        }).eq("id", analysis_id).execute()

        classifications = classify_questions(all_questions, chapters)

        # Merge classification data with question data
        for i, cls in enumerate(classifications):
            if i < len(all_questions):
                cls["question_text"] = all_questions[i]["text"]
                cls["year"] = all_questions[i].get("year", 0)

        # === Step 5: Calculate EFS Score ===
        efs_result = calculate_efs(classifications, chapters, years)

        # === Step 6: Generate AI Summary ===
        # Build top chapters list for the summary prompt
        top_chapters = [
            {"name": cs["chapter_name"], "count": cs["questions_asked"]}
            for cs in efs_result["chapter_stats"]
            if cs["questions_asked"] > 0
        ][:5]

        ai_summary = generate_summary(
            subject_name=subject_name,
            years=sorted(years),
            efs_score=efs_result["efs_score"],
            efs_label=efs_result["efs_label"],
            tbi_score=efs_result["tbi_score"],
            scs_score=efs_result["scs_score"],
            rp_score=efs_result["rp_score"],
            top_chapters=top_chapters,
            never_tested=efs_result["never_tested"],
            total_questions=efs_result["total_questions"],
            total_chapters=efs_result["total_chapters"],
            chapters_appeared=efs_result["chapters_appeared"],
        )

        # === Step 7: Save everything to DB ===

        # Update analysis record with results
        supabase.table("analyses").update({
            "status": "done",
            "efs_score": efs_result["efs_score"],
            "tbi_score": efs_result["tbi_score"],
            "scs_score": efs_result["scs_score"],
            "rp_score": efs_result["rp_score"],
            "efs_label": efs_result["efs_label"],
            "ai_summary": ai_summary,
            "total_questions": efs_result["total_questions"],
        }).eq("id", analysis_id).execute()

        # Save chapter stats
        for cs in efs_result["chapter_stats"]:
            supabase.table("chapter_stats").insert({
                "analysis_id": analysis_id,
                "chapter_name": cs["chapter_name"],
                "questions_asked": cs["questions_asked"],
                "expected_questions": cs["expected_questions"],
                "bias_score": cs["bias_score"],
            }).execute()

        # Save individual question classifications
        VALID_DIFFICULTY = {"Easy", "Medium", "Hard"}
        VALID_CONFIDENCE = {"High", "Medium", "Low"}

        for cls in classifications:
            difficulty = cls.get("difficulty", "Medium")
            confidence = cls.get("confidence", "Medium")
            # Sanitize AI output to match DB constraints
            if difficulty not in VALID_DIFFICULTY:
                difficulty = "Medium"
            if confidence not in VALID_CONFIDENCE:
                confidence = "Medium"

            supabase.table("questions").insert({
                "analysis_id": analysis_id,
                "question_number": cls.get("question_number", 0),
                "question_text": cls.get("question_text", "")[:2000],
                "assigned_chapter": cls.get("assigned_chapter", ""),
                "difficulty": difficulty,
                "confidence": confidence,
                "year": cls.get("year", 0),
            }).execute()

        # Update upload statuses to "done"
        for uid in body.upload_ids:
            supabase.table("uploads").update({"status": "done"}).eq("id", uid).execute()

        return {
            "analysis_id": analysis_id,
            "status": "done",
            "efs_score": efs_result["efs_score"],
            "efs_label": efs_result["efs_label"],
        }

    except Exception as e:
        # Pipeline failed — mark analysis as failed
        supabase.table("analyses").update({
            "status": "failed",
            "ai_summary": f"Analysis failed: {str(e)}",
        }).eq("id", analysis_id).execute()

        # Mark uploads as failed
        for uid in body.upload_ids:
            supabase.table("uploads").update({"status": "failed"}).eq("id", uid).execute()

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis pipeline failed: {str(e)}",
        )


@router.get("/analysis/{analysis_id}")
async def get_analysis(
    analysis_id: str,
    user: dict = Depends(get_current_user),
):
    """Get full analysis report data."""
    supabase = get_supabase()

    # Get analysis
    result = (
        supabase.table("analyses")
        .select("*")
        .eq("id", analysis_id)
        .eq("user_id", user["id"])
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    analysis = result.data[0]

    # Get subject name
    subject = (
        supabase.table("subjects")
        .select("name")
        .eq("id", analysis["subject_id"])
        .execute()
    )
    subject_name = subject.data[0]["name"] if subject.data else "Unknown"

    # Get chapter stats
    stats = (
        supabase.table("chapter_stats")
        .select("*")
        .eq("analysis_id", analysis_id)
        .execute()
    )

    # Get questions
    questions = (
        supabase.table("questions")
        .select("*")
        .eq("analysis_id", analysis_id)
        .order("question_number")
        .execute()
    )

    # Get years from questions
    years = sorted(set(q["year"] for q in (questions.data or []) if q.get("year")))

    # Difficulty distribution
    diff_dist = {}
    for q in (questions.data or []):
        d = q.get("difficulty", "Medium")
        diff_dist[d] = diff_dist.get(d, 0) + 1

    # Never tested chapters
    tested_chapters = set(cs["chapter_name"] for cs in (stats.data or []) if cs.get("questions_asked", 0) > 0)
    all_chapters_result = (
        supabase.table("syllabus_chapters")
        .select("chapter_name")
        .eq("subject_id", analysis["subject_id"])
        .execute()
    )
    all_chapters = [ch["chapter_name"] for ch in (all_chapters_result.data or [])]
    never_tested = [ch for ch in all_chapters if ch not in tested_chapters]

    return {
        "analysis_id": analysis_id,
        "subject_name": subject_name,
        "subject_id": analysis["subject_id"],
        "years_analyzed": years,
        "created_at": analysis.get("created_at"),
        "status": analysis.get("status"),
        "efs_score": {
            "total": analysis.get("efs_score", 0),
            "tbi_score": analysis.get("tbi_score", 0),
            "scs_score": analysis.get("scs_score", 0),
            "rp_score": analysis.get("rp_score", 0),
            "label": analysis.get("efs_label", ""),
        },
        "ai_summary": analysis.get("ai_summary", ""),
        "chapter_stats": stats.data or [],
        "never_tested": never_tested,
        "questions": questions.data or [],
        "difficulty_distribution": diff_dist,
    }


@router.get("/analysis/{analysis_id}/status")
async def get_analysis_status(
    analysis_id: str,
    user: dict = Depends(get_current_user),
):
    """Get current analysis status for polling."""
    supabase = get_supabase()

    result = (
        supabase.table("analyses")
        .select("id, status")
        .eq("id", analysis_id)
        .eq("user_id", user["id"])
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    return {
        "analysis_id": analysis_id,
        "status": result.data[0]["status"],
    }


@router.get("/analysis/{analysis_id}/predictions")
async def get_predictions(
    analysis_id: str,
    user: dict = Depends(get_current_user),
):
    """Get topic predictions for an analysis."""
    from services.prediction_engine import generate_predictions

    supabase = get_supabase()

    # Verify ownership
    analysis = (
        supabase.table("analyses")
        .select("id, subject_id")
        .eq("id", analysis_id)
        .eq("user_id", user["id"])
        .execute()
    )
    if not analysis.data:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    subject_id = analysis.data[0]["subject_id"]

    # Get questions
    questions = (
        supabase.table("questions")
        .select("assigned_chapter, year")
        .eq("analysis_id", analysis_id)
        .execute()
    )

    # Get syllabus chapters
    chapters_result = (
        supabase.table("syllabus_chapters")
        .select("chapter_name")
        .eq("subject_id", subject_id)
        .order("chapter_order")
        .execute()
    )
    chapters = [ch["chapter_name"] for ch in (chapters_result.data or [])]

    # Get years
    years = sorted(set(q["year"] for q in (questions.data or []) if q.get("year")))

    # Generate predictions
    result = generate_predictions(questions.data or [], chapters, years)

    return result


@router.post("/analysis/{analysis_id}/practice-questions")
async def generate_practice_questions_endpoint(
    analysis_id: str,
    user: dict = Depends(get_current_user),
):
    """Generate AI practice questions based on predicted topics."""
    import json
    import re
    from services.groq_service import _chat_completion, _parse_json_response

    supabase = get_supabase()

    # Verify ownership
    analysis = (
        supabase.table("analyses")
        .select("id, subject_id")
        .eq("id", analysis_id)
        .eq("user_id", user["id"])
        .execute()
    )
    if not analysis.data:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    subject_id = analysis.data[0]["subject_id"]

    # Get subject name
    subject = (
        supabase.table("subjects")
        .select("name")
        .eq("id", subject_id)
        .execute()
    )
    subject_name = subject.data[0]["name"] if subject.data else "Unknown"

    # Get predictions to determine which chapters to focus on
    from services.prediction_engine import generate_predictions

    questions = (
        supabase.table("questions")
        .select("assigned_chapter, year, difficulty")
        .eq("analysis_id", analysis_id)
        .execute()
    )

    chapters_result = (
        supabase.table("syllabus_chapters")
        .select("chapter_name")
        .eq("subject_id", subject_id)
        .order("chapter_order")
        .execute()
    )
    chapters = [ch["chapter_name"] for ch in (chapters_result.data or [])]
    years = sorted(set(q["year"] for q in (questions.data or []) if q.get("year")))

    pred_result = generate_predictions(questions.data or [], chapters, years)
    top_predictions = [p for p in pred_result["predictions"] if p["label"] in ("Very Likely", "Likely")][:6]

    if not top_predictions:
        top_predictions = pred_result["predictions"][:5]

    # Difficulty distribution
    diff_counts = {"Easy": 0, "Medium": 0, "Hard": 0}
    for q in (questions.data or []):
        d = q.get("difficulty", "Medium")
        if d in diff_counts:
            diff_counts[d] += 1
    total = sum(diff_counts.values()) or 1
    easy_pct = round(diff_counts["Easy"] / total * 100)
    med_pct = round(diff_counts["Medium"] / total * 100)
    hard_pct = round(diff_counts["Hard"] / total * 100)

    # Format predicted chapters
    predicted_str = "\n".join(
        f"  - {p['chapter_name']} ({p['label']}, appeared in {p['appearance_rate']}% of years)"
        for p in top_predictions
    )

    try:
        # System prompt — from api.md Prompt 3
        system_prompt = (
            "You are an expert university examiner. Generate realistic exam questions "
            "in the same style as university past papers. Questions should test understanding, "
            "not just memorization. Match the difficulty distribution of the original exam."
        )

        # User prompt — from api.md Prompt 3
        user_prompt = (
            f"Generate 8–10 university exam questions for the following subject and chapters.\n"
            f"These are predicted high-probability topics based on historical exam analysis.\n\n"
            f"Subject: {subject_name}\n"
            f"Target Chapters:\n{predicted_str}\n\n"
            f"Original exam difficulty distribution:\n"
            f"Easy: {easy_pct}%, Medium: {med_pct}%, Hard: {hard_pct}%\n\n"
            "Requirements:\n"
            "- Mix question types: theory, numerical, short answer, long answer\n"
            "- Match the difficulty distribution above\n"
            "- Questions should be specific and detailed, not vague\n"
            "- Each question should be answerable in a typical exam setting\n\n"
            "Return a JSON array. Each element:\n"
            '{\n'
            '  "question": "full question text",\n'
            '  "chapter": "chapter name",\n'
            '  "difficulty": "Easy | Medium | Hard",\n'
            '  "marks": suggested marks (2, 5, or 10),\n'
            '  "type": "Theory | Numerical | Short Answer | Long Answer"\n'
            '}\n\n'
            "Respond ONLY with valid JSON. No preamble."
        )

        raw = _chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.5,
            max_tokens=4096,
        )

        practice_questions = _parse_json_response(raw)

        return {"questions": practice_questions}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate practice questions: {str(e)}",
        )
