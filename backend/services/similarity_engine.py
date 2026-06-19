"""
Similarity Engine — Detects repeated/copied questions across exam years.

Uses TF-IDF vectorization and cosine similarity to identify question pairs
that are substantially similar across different exam years. This is a
deterministic, reproducible approach (no AI calls) suitable for research.

Key decisions:
  - Threshold: 0.75 cosine similarity = "Likely Repeated"
  - Same-year matches are ignored (sub-questions may naturally overlap)
  - Uses sklearn's TfidfVectorizer with English stop words removed
  - Returns the Question Repetition Rate (QRR) as a percentage metric
"""

from collections import defaultdict


def detect_similar_questions(
    questions: list[dict],
    threshold: float = 0.75,
) -> dict:
    """
    Detect similar/repeated questions across different exam years.

    Args:
        questions: List of dicts with at least:
                   {"question_text": str, "year": int, "question_number": int}
        threshold: Cosine similarity threshold (0-1). Default 0.75.

    Returns:
        {
            "similar_pairs": [
                {
                    "q1_number": 3, "q1_text": "...", "q1_year": 2021,
                    "q2_number": 5, "q2_text": "...", "q2_year": 2023,
                    "similarity": 0.87
                }, ...
            ],
            "repetition_rate": 23.5,  # percentage of questions with a match
            "total_pairs_found": 4,
        }
    """
    # Filter questions that have both text and year
    valid_qs = [
        q for q in questions
        if q.get("question_text") and len(q["question_text"].strip()) > 20
        and q.get("year") and q["year"] > 0
    ]

    if len(valid_qs) < 4:
        return {
            "similar_pairs": [],
            "repetition_rate": 0,
            "total_pairs_found": 0,
        }

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
    except ImportError:
        print("[Similarity] scikit-learn not installed, skipping similarity detection")
        return {
            "similar_pairs": [],
            "repetition_rate": 0,
            "total_pairs_found": 0,
        }

    # Extract texts for TF-IDF
    texts = [q["question_text"].strip().lower() for q in valid_qs]

    # Build TF-IDF matrix
    vectorizer = TfidfVectorizer(
        stop_words="english",
        max_features=5000,
        ngram_range=(1, 2),  # Unigrams + bigrams for better matching
        min_df=1,
        max_df=0.95,
    )

    try:
        tfidf_matrix = vectorizer.fit_transform(texts)
    except ValueError:
        # Can happen if all texts are stop words or empty after processing
        return {
            "similar_pairs": [],
            "repetition_rate": 0,
            "total_pairs_found": 0,
        }

    # Compute pairwise cosine similarity
    sim_matrix = cosine_similarity(tfidf_matrix)

    # Find pairs above threshold, across different years only
    similar_pairs = []
    matched_question_indices = set()

    for i in range(len(valid_qs)):
        for j in range(i + 1, len(valid_qs)):
            # Skip same-year comparisons
            if valid_qs[i].get("year") == valid_qs[j].get("year"):
                continue

            similarity = float(sim_matrix[i][j])
            if similarity >= threshold:
                similar_pairs.append({
                    "q1_number": valid_qs[i].get("question_number", 0),
                    "q1_text": valid_qs[i]["question_text"][:300],
                    "q1_year": valid_qs[i].get("year", 0),
                    "q2_number": valid_qs[j].get("question_number", 0),
                    "q2_text": valid_qs[j]["question_text"][:300],
                    "q2_year": valid_qs[j].get("year", 0),
                    "similarity": round(similarity * 100, 1),
                })
                matched_question_indices.add(i)
                matched_question_indices.add(j)

    # Sort by similarity descending
    similar_pairs.sort(key=lambda x: x["similarity"], reverse=True)

    # Cap at 20 pairs to keep response size reasonable
    similar_pairs = similar_pairs[:20]

    # Question Repetition Rate (QRR)
    # Percentage of questions that have at least one high-similarity match
    repetition_rate = round(
        (len(matched_question_indices) / len(valid_qs)) * 100, 1
    ) if valid_qs else 0

    return {
        "similar_pairs": similar_pairs,
        "repetition_rate": repetition_rate,
        "total_pairs_found": len(similar_pairs),
    }
