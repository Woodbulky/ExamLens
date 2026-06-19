"""
Export Router — PDF, CSV, JSON export + shareable links + research ZIP + study plan PDF.

Endpoints:
  POST /export              — Generate export file (PDF/CSV/JSON/research_zip)
  POST /export/study-plan   — Export study plan as PDF
  POST /export/share        — Generate shareable public link
  GET  /export/history      — Get user's export history
"""

import io
import json
import csv
import zipfile
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from middleware.auth import get_current_user
from db.supabase_client import get_supabase

router = APIRouter(tags=["Export"])


class ExportRequest(BaseModel):
    analysis_id: str
    format: str  # "pdf" | "csv" | "json" | "research_zip"


class ShareRequest(BaseModel):
    analysis_id: str


# ============================================================
# Helper — fetch full report data for export
# ============================================================
def _fetch_report_data(supabase, analysis_id: str, user_id: str) -> dict:
    """Fetch all report data needed for exports."""
    # Analysis record
    analysis = (
        supabase.table("analyses")
        .select("*")
        .eq("id", analysis_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not analysis.data:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    a = analysis.data[0]

    # Subject name
    subject = supabase.table("subjects").select("name").eq("id", a["subject_id"]).execute()
    subject_name = subject.data[0]["name"] if subject.data else "Unknown"

    # Chapter stats
    stats = supabase.table("chapter_stats").select("*").eq("analysis_id", analysis_id).execute()

    # Questions
    questions = (
        supabase.table("questions")
        .select("*")
        .eq("analysis_id", analysis_id)
        .order("question_number")
        .execute()
    )

    # Syllabus chapters
    chapters = (
        supabase.table("syllabus_chapters")
        .select("chapter_name")
        .eq("subject_id", a["subject_id"])
        .execute()
    )

    years = sorted(set(q["year"] for q in (questions.data or []) if q.get("year")))

    return {
        "analysis": a,
        "subject_name": subject_name,
        "chapter_stats": stats.data or [],
        "questions": questions.data or [],
        "chapters": [ch["chapter_name"] for ch in (chapters.data or [])],
        "years": years,
    }


# ============================================================
# PDF Export
# ============================================================
def _generate_pdf(data: dict) -> bytes:
    """Generate a professional PDF report."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=25*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle('CustomTitle', parent=styles['Title'],
                                  fontSize=22, spaceAfter=6, textColor=colors.HexColor('#0F2744'))
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'],
                                     fontSize=11, textColor=colors.HexColor('#6B7280'))
    heading_style = ParagraphStyle('SectionHead', parent=styles['Heading2'],
                                    fontSize=14, spaceAbove=18, spaceBefore=12,
                                    textColor=colors.HexColor('#0D9488'))
    body_style = ParagraphStyle('Body', parent=styles['Normal'],
                                 fontSize=10, leading=14, spaceAfter=6)

    elements = []
    a = data["analysis"]

    # Header
    elements.append(Paragraph("ExamLens — Analysis Report", title_style))
    elements.append(Paragraph(f"Subject: {data['subject_name']}", subtitle_style))
    elements.append(Paragraph(
        f"Years: {', '.join(str(y) for y in data['years'])} · "
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        subtitle_style))
    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E5E7EB')))
    elements.append(Spacer(1, 8))

    # EFS Score
    elements.append(Paragraph("Examination Fairness Score (EFS)", heading_style))
    efs_data = [
        ["Metric", "Score", "Weight"],
        ["Topic Bias Index (TBI)", f"{a.get('tbi_score', 0):.2f}", "40%"],
        ["Syllabus Coverage (SCS)", f"{a.get('scs_score', 0):.2f}", "35%"],
        ["Recurrence Penalty (RP)", f"{a.get('rp_score', 0):.2f}", "25%"],
        ["EFS Total", f"{a.get('efs_score', 0):.2f} / 10 — {a.get('efs_label', '')}", "100%"],
    ]
    t = Table(efs_data, colWidths=[200, 120, 80])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F0FDFA')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0D9488')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#F0FDFA')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 8))

    # AI Summary
    if a.get("ai_summary"):
        elements.append(Paragraph("AI Analysis Summary", heading_style))
        elements.append(Paragraph(a["ai_summary"], body_style))
        elements.append(Spacer(1, 6))

    # Chapter Breakdown
    elements.append(Paragraph("Chapter Breakdown", heading_style))
    ch_header = ["Chapter", "Questions", "Expected", "Bias", "Status"]
    ch_rows = [ch_header]
    for cs in data["chapter_stats"]:
        ch_rows.append([
            cs["chapter_name"][:40],
            str(cs.get("questions_asked", 0)),
            str(cs.get("expected_questions", 0)),
            f"{cs.get('bias_score', 0):.2f}",
            cs.get("status", "Fair") if cs.get("questions_asked", 0) > 0 else "Never tested",
        ])
    if len(ch_rows) > 1:
        ct = Table(ch_rows, colWidths=[180, 65, 65, 50, 80])
        ct.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F0FDFA')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0D9488')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(ct)

    # Questions
    elements.append(Paragraph(f"Question Classifications ({len(data['questions'])})", heading_style))
    q_header = ["#", "Question (preview)", "Chapter", "Difficulty", "Year"]
    q_rows = [q_header]
    for q in data["questions"][:50]:  # Limit to 50 for PDF
        q_rows.append([
            str(q.get("question_number", "")),
            (q.get("question_text", "")[:60] + "...") if len(q.get("question_text", "")) > 60 else q.get("question_text", ""),
            q.get("assigned_chapter", "")[:30],
            q.get("difficulty", ""),
            str(q.get("year", "")),
        ])
    if len(q_rows) > 1:
        qt = Table(q_rows, colWidths=[25, 180, 120, 55, 40])
        qt.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F0FDFA')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0D9488')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(qt)

    # Footer
    elements.append(Spacer(1, 16))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#E5E7EB')))
    elements.append(Paragraph(
        "Generated by ExamLens — AI-Powered Examination Fairness Analysis",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#9CA3AF'))
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# CSV Export
# ============================================================
def _generate_csv(data: dict) -> bytes:
    """Generate CSV with question classifications."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Question #", "Question Text", "Assigned Chapter", "Difficulty", "Confidence", "Year"])
    for q in data["questions"]:
        writer.writerow([
            q.get("question_number", ""),
            q.get("question_text", ""),
            q.get("assigned_chapter", ""),
            q.get("difficulty", ""),
            q.get("confidence", ""),
            q.get("year", ""),
        ])
    return buffer.getvalue().encode('utf-8')


# ============================================================
# JSON Export
# ============================================================
def _generate_json(data: dict) -> bytes:
    """Generate full JSON export of analysis data."""
    a = data["analysis"]
    export = {
        "examlens_version": "1.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "subject_name": data["subject_name"],
        "years_analyzed": data["years"],
        "efs_score": {
            "total": a.get("efs_score"),
            "tbi_score": a.get("tbi_score"),
            "scs_score": a.get("scs_score"),
            "rp_score": a.get("rp_score"),
            "label": a.get("efs_label"),
        },
        "ai_summary": a.get("ai_summary"),
        "chapter_stats": data["chapter_stats"],
        "questions": data["questions"],
        "syllabus_chapters": data["chapters"],
    }
    return json.dumps(export, indent=2, default=str).encode('utf-8')


# ============================================================
# Research ZIP (methodology note + all files)
# ============================================================
def _generate_research_zip(data: dict) -> bytes:
    """Generate research ZIP with methodology note, CSV, JSON, and summary."""
    from services.groq_service import _chat_completion, MODEL

    a = data["analysis"]

    # Generate methodology note (Prompt 4)
    try:
        # Confidence distribution
        conf_counts = {"High": 0, "Medium": 0, "Low": 0}
        for q in data["questions"]:
            c = q.get("confidence", "Medium")
            if c in conf_counts:
                conf_counts[c] += 1
        total_q = len(data["questions"]) or 1
        high_pct = round(conf_counts["High"] / total_q * 100)
        med_pct = round(conf_counts["Medium"] / total_q * 100)
        low_pct = round(conf_counts["Low"] / total_q * 100)

        system_prompt = (
            "You are an academic writing assistant. Write formal, precise methodology "
            "descriptions suitable for IEEE or Springer journal submission. Use passive "
            "voice, precise language, and cite the logical steps clearly. Do not use first person."
        )

        user_prompt = (
            "Write a formal 2-paragraph methodology description for the following exam analysis system. "
            "This will be included as supplementary material in a research paper submission to IEEE TALE or IEEE EDUCON.\n\n"
            "System: ExamLens — AI-Powered Examination Fairness Analysis\n"
            "Metric: EFS Score (Examination Fairness Score)\n\n"
            "EFS Formula:\n"
            "  EFS = (TBI × 0.40) + (SCS × 0.35) + (RP × 0.25)\n"
            "  Where:\n"
            "    TBI = 10 - min(StandardDeviation(ChapterBiasValues) × 2, 10)\n"
            "    SCS = (ChaptersAppeared / TotalChapters) × 10\n"
            "    RP = 10 - (AverageRecurrenceRateOfTop3Chapters × 10)\n\n"
            f"Dataset for this analysis:\n"
            f"  Subject: {data['subject_name']}\n"
            f"  Years analyzed: {', '.join(str(y) for y in data['years'])}\n"
            f"  Total questions classified: {len(data['questions'])}\n"
            f"  Total syllabus chapters: {len(data['chapters'])}\n"
            f"  AI model used: {MODEL} (via NVIDIA/Groq)\n"
            f"  Classification confidence distribution: High: {high_pct}%, Medium: {med_pct}%, Low: {low_pct}%\n\n"
            "Paragraph 1: Describe the data collection and preprocessing methodology (PDF extraction, question segmentation, AI classification).\n"
            "Paragraph 2: Describe the EFS Score calculation methodology including the three components and their weights.\n\n"
            "Use formal academic language. Do not include results, only methodology."
        )

        methodology_note = _chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=1024,
        ).strip()
    except Exception:
        methodology_note = "Methodology note generation failed. Please regenerate."

    # Build ZIP
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Methodology note
        zf.writestr("methodology_note.txt", methodology_note)

        # Summary
        summary = (
            f"ExamLens Research Export\n"
            f"{'=' * 40}\n"
            f"Subject: {data['subject_name']}\n"
            f"Years: {', '.join(str(y) for y in data['years'])}\n"
            f"EFS Score: {a.get('efs_score', 0):.2f} / 10 ({a.get('efs_label', '')})\n"
            f"TBI: {a.get('tbi_score', 0):.2f} | SCS: {a.get('scs_score', 0):.2f} | RP: {a.get('rp_score', 0):.2f}\n"
            f"Total Questions: {len(data['questions'])}\n"
            f"Syllabus Chapters: {len(data['chapters'])}\n\n"
            f"AI Summary:\n{a.get('ai_summary', 'N/A')}\n"
        )
        zf.writestr("analysis_summary.txt", summary)

        # CSV data
        zf.writestr("questions_data.csv", _generate_csv(data).decode('utf-8'))

        # JSON data
        zf.writestr("full_analysis.json", _generate_json(data).decode('utf-8'))

    buffer.seek(0)
    return buffer.getvalue()


# ============================================================
# Export Endpoint
# ============================================================
@router.post("/export")
async def export_analysis(
    body: ExportRequest,
    user: dict = Depends(get_current_user),
):
    """Export analysis in the requested format."""
    supabase = get_supabase()
    data = _fetch_report_data(supabase, body.analysis_id, user["id"])

    fmt = body.format.lower()

    if fmt == "pdf":
        content = _generate_pdf(data)
        media_type = "application/pdf"
        filename = f"ExamLens_{data['subject_name'].replace(' ', '_')}_Report.pdf"
    elif fmt == "csv":
        content = _generate_csv(data)
        media_type = "text/csv"
        filename = f"ExamLens_{data['subject_name'].replace(' ', '_')}_Data.csv"
    elif fmt == "json":
        content = _generate_json(data)
        media_type = "application/json"
        filename = f"ExamLens_{data['subject_name'].replace(' ', '_')}_Full.json"
    elif fmt == "research_zip":
        content = _generate_research_zip(data)
        media_type = "application/zip"
        filename = f"ExamLens_{data['subject_name'].replace(' ', '_')}_Research.zip"
    else:
        raise HTTPException(status_code=400, detail="Invalid export format. Use: pdf, csv, json, research_zip")

    # Save to export history
    try:
        supabase.table("export_history").insert({
            "user_id": user["id"],
            "analysis_id": body.analysis_id,
            "export_type": fmt.upper(),
            "subject_name": data["subject_name"],
        }).execute()
    except Exception:
        pass  # Non-critical

    return StreamingResponse(
        io.BytesIO(content),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ============================================================
# Study Plan PDF Export
# ============================================================
class ExportStudyPlanRequest(BaseModel):
    analysis_id: str
    subject_name: str
    exam_date: str
    days_until: int
    hours_per_day: float
    plan: dict  # The full AI-generated plan object


def _generate_study_plan_pdf(data: dict) -> bytes:
    """Generate a professional PDF for the AI Study Plan."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=25*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle('CustomTitle', parent=styles['Title'],
                                  fontSize=22, spaceAfter=6, textColor=colors.HexColor('#0F2744'))
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'],
                                     fontSize=11, textColor=colors.HexColor('#6B7280'))
    heading_style = ParagraphStyle('SectionHead', parent=styles['Heading2'],
                                    fontSize=14, spaceAbove=18, spaceBefore=12,
                                    textColor=colors.HexColor('#0D9488'))
    body_style = ParagraphStyle('Body', parent=styles['Normal'],
                                 fontSize=10, leading=14, spaceAfter=6)
    tip_style = ParagraphStyle('Tip', parent=styles['Normal'],
                                fontSize=9, leading=13, textColor=colors.HexColor('#4B5563'),
                                leftIndent=12, spaceAfter=4)

    elements = []
    plan = data.get("plan", {})

    # Header
    elements.append(Paragraph("ExamLens — AI Study Plan", title_style))
    elements.append(Paragraph(f"Subject: {data.get('subject_name', 'N/A')}", subtitle_style))
    elements.append(Paragraph(
        f"Exam Date: {data.get('exam_date', 'N/A')} · "
        f"{data.get('days_until', 0)} days to go · "
        f"{data.get('hours_per_day', 0)} hrs/day · "
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        subtitle_style))
    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E5E7EB')))
    elements.append(Spacer(1, 8))

    # Overview Stats Table
    elements.append(Paragraph("Overview", heading_style))
    total_days = plan.get("total_days", data.get("days_until", 0))
    total_hours = plan.get("total_hours", round(data.get("days_until", 0) * data.get("hours_per_day", 0)))
    overview_data = [
        ["Total Study Days", "Total Hours", "Hours / Day", "Days to Exam"],
        [str(total_days), str(total_hours), str(data.get("hours_per_day", 0)), str(data.get("days_until", 0))],
    ]
    ot = Table(overview_data, colWidths=[110, 110, 110, 110])
    ot.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F0FDFA')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0D9488')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, 1), 14),
    ]))
    elements.append(ot)
    elements.append(Spacer(1, 10))

    # Phases
    phases = plan.get("phases", [])
    for pi, phase in enumerate(phases):
        phase_name = phase.get("phase_name", f"Phase {pi + 1}")
        elements.append(Paragraph(phase_name, heading_style))

        days = phase.get("days", [])
        if days:
            day_header = ["Day", "Date", "Focus Topic", "Hours", "Priority", "Tasks"]
            day_rows = [day_header]
            for day in days:
                tasks_str = ", ".join(day.get("tasks", [])) if day.get("tasks") else "-"
                # Truncate long tasks for table readability
                if len(tasks_str) > 60:
                    tasks_str = tasks_str[:57] + "..."

                day_date = day.get("date", "-")
                if day_date and day_date != "-":
                    try:
                        from datetime import datetime as dt_parse
                        parsed = dt_parse.strptime(day_date, "%Y-%m-%d")
                        day_date = parsed.strftime("%b %d, %a")
                    except Exception:
                        pass

                day_rows.append([
                    str(day.get("day", pi * 100 + 1)),
                    day_date,
                    str(day.get("focus", "-"))[:35],
                    str(day.get("hours", "-")),
                    str(day.get("priority", "Medium")),
                    tasks_str,
                ])

            dt = Table(day_rows, colWidths=[30, 68, 120, 35, 50, 140])

            # Color-code priority column
            priority_colors = {
                "High": colors.HexColor('#DCFCE7'),
                "Medium": colors.HexColor('#FEF3C7'),
                "Low": colors.HexColor('#F3F4F6'),
            }
            style_commands = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F0FDFA')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0D9488')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]
            # Add priority row colors
            for ri, row in enumerate(day_rows[1:], start=1):
                priority = row[4]
                bg = priority_colors.get(priority, colors.HexColor('#FFFFFF'))
                style_commands.append(('BACKGROUND', (4, ri), (4, ri), bg))

            dt.setStyle(TableStyle(style_commands))
            elements.append(dt)
            elements.append(Spacer(1, 6))

    # Tips
    tips = plan.get("tips", [])
    if tips:
        elements.append(Paragraph("Study Tips", heading_style))
        for i, tip in enumerate(tips, 1):
            elements.append(Paragraph(f"• {tip}", tip_style))
        elements.append(Spacer(1, 8))

    # Footer
    elements.append(Spacer(1, 16))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#E5E7EB')))
    elements.append(Paragraph(
        "Generated by ExamLens — AI-Powered Examination Fairness Analysis",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#9CA3AF'))
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


@router.post("/export/study-plan")
async def export_study_plan(
    body: ExportStudyPlanRequest,
    user: dict = Depends(get_current_user),
):
    """Export the AI-generated study plan as a PDF."""
    supabase = get_supabase()

    # Verify ownership of the analysis
    analysis = (
        supabase.table("analyses")
        .select("id")
        .eq("id", body.analysis_id)
        .eq("user_id", user["id"])
        .execute()
    )
    if not analysis.data:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    # Generate PDF
    pdf_bytes = _generate_study_plan_pdf({
        "subject_name": body.subject_name,
        "exam_date": body.exam_date,
        "days_until": body.days_until,
        "hours_per_day": body.hours_per_day,
        "plan": body.plan,
    })

    filename = f"ExamLens_{body.subject_name.replace(' ', '_')}_StudyPlan.pdf"

    # Save to export history
    try:
        supabase.table("export_history").insert({
            "user_id": user["id"],
            "analysis_id": body.analysis_id,
            "export_type": "STUDY_PLAN_PDF",
            "subject_name": body.subject_name,
        }).execute()
    except Exception:
        pass  # Non-critical

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ============================================================
# Shareable Link
# ============================================================
@router.post("/export/share")
async def create_share_link(
    body: ShareRequest,
    user: dict = Depends(get_current_user),
):
    """Generate a shareable public link for an analysis."""
    supabase = get_supabase()

    # Verify ownership
    analysis = (
        supabase.table("analyses")
        .select("id, share_token")
        .eq("id", body.analysis_id)
        .eq("user_id", user["id"])
        .execute()
    )
    if not analysis.data:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    # Check if already has a share token
    existing_token = analysis.data[0].get("share_token")
    if existing_token:
        return {"share_token": existing_token, "share_url": f"/shared/{existing_token}"}

    # Generate new token
    token = str(uuid.uuid4())[:12]
    supabase.table("analyses").update({"share_token": token}).eq("id", body.analysis_id).execute()

    return {"share_token": token, "share_url": f"/shared/{token}"}


# ============================================================
# Export History
# ============================================================
@router.get("/export/history")
async def get_export_history(user: dict = Depends(get_current_user)):
    """Get the user's export history."""
    supabase = get_supabase()

    result = (
        supabase.table("export_history")
        .select("*")
        .eq("user_id", user["id"])
        .order("created_at", desc=True)
        .limit(20)
        .execute()
    )

    return {"history": result.data or []}
