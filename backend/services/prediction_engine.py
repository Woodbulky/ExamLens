"""
Prediction Engine — Ranks chapters by likelihood of appearing in future exams.

Uses historical frequency data from past analyses to predict which topics
are most likely to appear. Assigns labels:
  - Very Likely: appeared in 80%+ of years, high question count
  - Likely: appeared in 50-79% of years
  - Possible: appeared in <50% of years but at least once
  - Unlikely: never appeared (still listed for completeness)
"""

from collections import Counter, defaultdict


def generate_predictions(
    questions: list[dict],
    chapters: list[str],
    years: list[int],
) -> dict:
    """
    Generate topic predictions based on historical exam data.

    Args:
        questions: Classified questions with assigned_chapter, year
        chapters: Full syllabus chapter list
        years: List of exam years

    Returns:
        Dict with predictions list and trend_data for charting
    """
    if not questions or not chapters or not years:
        return {"predictions": [], "trend_data": {"years": [], "chapters": []}}

    total_years = len(set(years))
    total_questions = len(questions)

    # --- Build per-chapter stats ---
    # Count questions per chapter per year
    chapter_year_counts = defaultdict(lambda: defaultdict(int))
    chapter_total_counts = Counter()

    for q in questions:
        ch = q.get("assigned_chapter", "")
        yr = q.get("year", 0)
        if ch and yr:
            chapter_year_counts[ch][yr] += 1
            chapter_total_counts[ch] += 1

    # --- Calculate predictions ---
    predictions = []

    for ch in chapters:
        total_count = chapter_total_counts.get(ch, 0)
        years_appeared = [y for y in years if chapter_year_counts[ch].get(y, 0) > 0]
        appearance_rate = len(set(years_appeared)) / total_years if total_years > 0 else 0

        # Average questions per year when it appears
        avg_per_year = total_count / total_years if total_years > 0 else 0

        # Confidence score (0-1): combines appearance rate and question volume
        # Appearance rate is weighted more (60%) than volume (40%)
        volume_score = min(total_count / (total_questions / len(chapters)), 1.0) if total_questions > 0 and len(chapters) > 0 else 0
        confidence = (appearance_rate * 0.6) + (volume_score * 0.4)
        confidence = min(confidence, 1.0)

        # Assign label based on appearance rate and confidence
        if appearance_rate >= 0.8 and total_count > 0:
            label = "Very Likely"
        elif appearance_rate >= 0.5 and total_count > 0:
            label = "Likely"
        elif total_count > 0:
            label = "Possible"
        else:
            label = "Unlikely"

        predictions.append({
            "chapter_name": ch,
            "label": label,
            "confidence": round(confidence, 2),
            "total_questions": total_count,
            "years_appeared": sorted(set(years_appeared)),
            "avg_questions_per_year": round(avg_per_year, 1),
            "appearance_rate": round(appearance_rate * 100),
        })

    # Sort by confidence descending
    predictions.sort(key=lambda x: x["confidence"], reverse=True)

    # Assign rank
    for i, p in enumerate(predictions):
        p["rank"] = i + 1

    # --- Build trend data for charting ---
    sorted_years = sorted(set(years))
    trend_chapters = []

    for ch in chapters:
        counts = [chapter_year_counts[ch].get(y, 0) for y in sorted_years]
        if sum(counts) > 0:  # Only include chapters that appeared at least once
            trend_chapters.append({
                "chapter_name": ch,
                "counts": counts,
            })

    # Sort trend by total count descending
    trend_chapters.sort(key=lambda x: sum(x["counts"]), reverse=True)

    return {
        "predictions": predictions,
        "trend_data": {
            "years": sorted_years,
            "chapters": trend_chapters[:10],  # Top 10 for chart readability
        },
    }
