"""
EFS Calculator — Examination Fairness Score

The EFS Score quantifies how fairly an exam covers the syllabus on a 0–10 scale.
Formula: EFS = (TBI × 0.40) + (SCS × 0.35) + (RP × 0.25)

Components:
  TBI (Topic Bias Index) — Measures variance in question distribution.
      A fair exam distributes questions evenly across chapters.
  SCS (Syllabus Coverage Score) — Measures what % of syllabus chapters appear.
      A fair exam tests all chapters at least once.
  RP (Recurrence Penalty) — Penalizes exams where the same few chapters
      dominate year after year.

Labels:
  8.5–10.0  →  Excellent
  7.0–8.4   →  Good
  5.0–6.9   →  Moderate
  3.0–4.9   →  Poor
  0.0–2.9   →  Critical
"""

import math
from collections import Counter


def calculate_efs(
    classifications: list[dict],
    chapters: list[str],
    years: list[int],
) -> dict:
    """
    Calculate the full EFS Score from classified questions.

    Args:
        classifications: List of {"assigned_chapter": str, "question_number": int, ...}
                         from the AI classification step
        chapters: Full list of syllabus chapter names
        years: List of years in the analysis

    Returns:
        Dict with efs_score, tbi_score, scs_score, rp_score, efs_label, chapter_stats, etc.
    """
    total_chapters = len(chapters)
    total_questions = len(classifications)

    if total_chapters == 0 or total_questions == 0:
        return _empty_result()

    # --- Count questions per chapter ---
    chapter_counts = Counter()
    for c in classifications:
        chapter_counts[c["assigned_chapter"]] += 1

    # Include chapters with 0 questions
    for ch in chapters:
        if ch not in chapter_counts:
            chapter_counts[ch] = 0

    # --- Calculate expected questions per chapter ---
    # If the exam were perfectly fair, each chapter would get an equal share
    expected_per_chapter = total_questions / total_chapters

    # =========================================================
    # TBI Score (Topic Bias Index) — Weight: 0.40
    #
    # Measures how evenly questions are distributed across chapters.
    # Uses standard deviation of "bias values" per chapter.
    # Bias value = (actual - expected) / expected for each chapter.
    #
    # Formula: TBI = 10 - min(StdDev(bias_values) × 2, 10)
    # A perfectly even exam → StdDev = 0 → TBI = 10
    # A heavily biased exam → high StdDev → TBI approaches 0
    # =========================================================
    bias_values = []
    for ch in chapters:
        actual = chapter_counts.get(ch, 0)
        # Bias value: how far this chapter deviates from expected
        bias = (actual - expected_per_chapter) / expected_per_chapter if expected_per_chapter > 0 else 0
        bias_values.append(bias)

    # Standard deviation of bias values
    mean_bias = sum(bias_values) / len(bias_values) if bias_values else 0
    variance = sum((b - mean_bias) ** 2 for b in bias_values) / len(bias_values) if bias_values else 0
    std_dev = math.sqrt(variance)

    # TBI: higher is better (10 = perfectly even, 0 = extremely biased)
    tbi_score = 10 - min(std_dev * 2, 10)
    tbi_score = max(0, min(10, tbi_score))  # Clamp to [0, 10]

    # =========================================================
    # SCS Score (Syllabus Coverage Score) — Weight: 0.35
    #
    # Measures what fraction of the syllabus actually appears in exams.
    # Simple ratio: chapters that got ≥1 question / total chapters.
    #
    # Formula: SCS = (ChaptersAppeared / TotalChapters) × 10
    # All chapters tested → SCS = 10
    # Half chapters tested → SCS = 5
    # =========================================================
    chapters_appeared = sum(1 for ch in chapters if chapter_counts.get(ch, 0) > 0)
    scs_score = (chapters_appeared / total_chapters) * 10
    scs_score = max(0, min(10, scs_score))  # Clamp to [0, 10]

    # =========================================================
    # RP Score (Recurrence Penalty) — Weight: 0.25
    #
    # Penalizes exams where the same top chapters keep appearing.
    # Looks at the top 3 most-tested chapters and their share of
    # total questions. High concentration = low RP score.
    #
    # Formula: RP = 10 - (AvgRecurrenceRateOfTop3 × 10)
    # RecurrenceRate = chapter_count / total_questions
    # If top 3 chapters hog most questions → RP is low (bad)
    # If questions are spread out → RP is high (good)
    # =========================================================
    sorted_counts = sorted(chapter_counts.values(), reverse=True)
    top_3_counts = sorted_counts[:3] if len(sorted_counts) >= 3 else sorted_counts

    # Average recurrence rate of top 3 chapters
    if total_questions > 0 and top_3_counts:
        avg_recurrence = sum(c / total_questions for c in top_3_counts) / len(top_3_counts)
    else:
        avg_recurrence = 0

    rp_score = 10 - (avg_recurrence * 10)
    rp_score = max(0, min(10, rp_score))  # Clamp to [0, 10]

    # =========================================================
    # Final EFS Score
    # EFS = (TBI × 0.40) + (SCS × 0.35) + (RP × 0.25)
    # =========================================================
    efs_score = (tbi_score * 0.40) + (scs_score * 0.35) + (rp_score * 0.25)
    efs_score = round(efs_score, 2)

    # Assign label based on score range
    efs_label = _get_label(efs_score)

    # --- Build chapter stats ---
    chapter_stats = []
    for i, ch in enumerate(chapters):
        actual = chapter_counts.get(ch, 0)
        # Bias score: ratio of actual/expected (>1 = over-tested, <1 = under-tested)
        ch_bias = round(actual / expected_per_chapter, 2) if expected_per_chapter > 0 else 0

        if actual == 0:
            status = "Never tested"
        elif ch_bias > 1.5:
            status = "Over-tested"
        elif ch_bias < 0.5:
            status = "Under-tested"
        else:
            status = "Fair"

        chapter_stats.append({
            "chapter_name": ch,
            "chapter_order": i + 1,
            "questions_asked": actual,
            "expected_questions": round(expected_per_chapter, 1),
            "bias_score": ch_bias,
            "status": status,
        })

    # Sort by questions asked descending for display
    chapter_stats.sort(key=lambda x: x["questions_asked"], reverse=True)

    # Never-tested chapters list
    never_tested = [ch for ch in chapters if chapter_counts.get(ch, 0) == 0]

    # Difficulty distribution
    difficulty_dist = Counter(c.get("difficulty", "Medium") for c in classifications)

    return {
        "efs_score": efs_score,
        "tbi_score": round(tbi_score, 2),
        "scs_score": round(scs_score, 2),
        "rp_score": round(rp_score, 2),
        "efs_label": efs_label,
        "chapter_stats": chapter_stats,
        "never_tested": never_tested,
        "total_questions": total_questions,
        "chapters_appeared": chapters_appeared,
        "total_chapters": total_chapters,
        "difficulty_distribution": dict(difficulty_dist),
    }


def _get_label(score: float) -> str:
    """Assign a human-readable label based on EFS score."""
    if score >= 8.5:
        return "Excellent"
    elif score >= 7.0:
        return "Good"
    elif score >= 5.0:
        return "Moderate"
    elif score >= 3.0:
        return "Poor"
    else:
        return "Critical"


def _empty_result() -> dict:
    """Return an empty EFS result when there's no data."""
    return {
        "efs_score": 0,
        "tbi_score": 0,
        "scs_score": 0,
        "rp_score": 0,
        "efs_label": "Critical",
        "chapter_stats": [],
        "never_tested": [],
        "total_questions": 0,
        "chapters_appeared": 0,
        "total_chapters": 0,
        "difficulty_distribution": {},
    }
