"""
AI Service — Handles all LLM calls for ExamLens.

Provider priority:
  1. NVIDIA API (Llama 3.3 70B Instruct via OpenAI-compatible endpoint)
  2. Groq API  (Llama 3.3 70B Versatile — fallback)

Uses NVIDIA as primary provider. If the NVIDIA key is missing or the
call fails, it automatically falls back to Groq.

Used for:
  1. Question classification (chapter, difficulty, confidence)
  2. AI summary generation
  3. Practice question generation (Phase 6)
"""

import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

# --------------- Provider config ---------------
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_MODEL = "meta/llama-3.3-70b-instruct"

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"

# Expose a MODULE-level MODEL variable so existing
# `from services.groq_service import MODEL` works.
MODEL = NVIDIA_MODEL if NVIDIA_API_KEY else GROQ_MODEL


def _get_nvidia_client():
    """Get an OpenAI-compatible client pointed at NVIDIA."""
    from openai import OpenAI
    if not NVIDIA_API_KEY:
        return None
    return OpenAI(base_url=NVIDIA_BASE_URL, api_key=NVIDIA_API_KEY)


def _get_groq_client():
    """Get a Groq client instance (fallback)."""
    from groq import Groq
    if not GROQ_API_KEY:
        return None
    return Groq(api_key=GROQ_API_KEY)


def _get_client():
    """
    Return (client, model) for the highest-priority available provider.
    Raises RuntimeError if neither key is configured.
    """
    if NVIDIA_API_KEY:
        return _get_nvidia_client(), NVIDIA_MODEL
    if GROQ_API_KEY:
        return _get_groq_client(), GROQ_MODEL
    raise RuntimeError(
        "No AI API key configured. Set NVIDIA_API_KEY or GROQ_API_KEY in .env"
    )


def _chat_completion(messages: list[dict], temperature: float = 0.1,
                     max_tokens: int = 2048) -> str:
    """
    Send a chat completion request.
    Tries NVIDIA first; if it fails, falls back to Groq.
    Returns the raw text content of the first choice.
    """
    providers = []

    if NVIDIA_API_KEY:
        providers.append(("NVIDIA", _get_nvidia_client, NVIDIA_MODEL))
    if GROQ_API_KEY:
        providers.append(("Groq", _get_groq_client, GROQ_MODEL))

    if not providers:
        raise RuntimeError(
            "No AI API key configured. Set NVIDIA_API_KEY or GROQ_API_KEY in .env"
        )

    last_error = None
    for name, client_fn, model in providers:
        try:
            client = client_fn()
            if client is None:
                continue
            print(f"[AI] Trying {name} ({model})...")
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            print(f"[AI] ✓ {name} succeeded")
            return response.choices[0].message.content
        except Exception as e:
            last_error = e
            print(f"[AI] ✗ {name} failed: {e}")
            continue

    raise RuntimeError(
        f"All AI providers failed. Last error: {last_error}"
    )


def _parse_json_response(text: str) -> list | dict:
    """
    Parse JSON from LLM response, handling common formatting issues.
    LLMs sometimes wrap JSON in markdown code fences.
    """
    text = text.strip()
    if text.startswith("```"):
        # Remove opening fence (with optional language tag)
        text = re.sub(r'^```\w*\n?', '', text)
        # Remove closing fence
        text = re.sub(r'\n?```$', '', text)
        text = text.strip()

    return json.loads(text)


# ============================================================
# Prompt 1 — Question Classification
# Classifies each exam question into a syllabus chapter,
# assigns difficulty (Easy/Medium/Hard), and confidence level.
# ============================================================
def classify_questions(
    questions: list[dict],
    chapters: list[str],
) -> list[dict]:
    """
    Classify exam questions into syllabus chapters using AI.
    Processes in batches of 10 to stay under token limits.
    Tries NVIDIA first, falls back to Groq.

    Args:
        questions: List of {"number": int, "text": str}
        chapters: List of chapter names

    Returns:
        List of classification dicts with chapter, difficulty, confidence, reasoning
    """
    if not questions or not chapters:
        return []

    import time

    chapters_list = "\n".join(f"  - {ch}" for ch in chapters)

    # System prompt
    system_prompt = (
        "You are an expert academic analysis assistant. Your job is to analyze "
        "university exam questions and classify each one into the correct syllabus "
        "chapter. You must also assess the difficulty level and your confidence in "
        "the classification.\n\n"
        "For each question, return a JSON object. Respond ONLY with valid JSON, "
        "no preamble, no explanation, no markdown backticks."
    )

    all_classifications = []
    BATCH_SIZE = 8  # Small batches to stay under token limit

    for batch_start in range(0, len(questions), BATCH_SIZE):
        batch = questions[batch_start:batch_start + BATCH_SIZE]

        # Build questions string (truncate to 300 chars each)
        questions_list = "\n".join(
            f"  Q{q['number']}: {q['text'][:300]}" for q in batch
        )

        user_prompt = (
            f"Syllabus Chapters:\n{chapters_list}\n\n"
            f"Exam Questions:\n{questions_list}\n\n"
            "Classify each question. Return a JSON array where each element has:\n"
            '- question_number: int\n'
            '- assigned_chapter: exact chapter name from the syllabus list above\n'
            '- difficulty: "Easy" | "Medium" | "Hard"\n'
            '- confidence: "High" | "Medium" | "Low"\n'
            '- reasoning: one short sentence\n\n'
            "If a question spans multiple chapters, assign it to the most dominant one.\n"
            'If a question cannot be matched, assign closest chapter with confidence "Low".'
        )

        try:
            raw = _chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=2048,
            )

            batch_results = _parse_json_response(raw)

            for item in batch_results:
                all_classifications.append({
                    "question_number": item.get("question_number", 0),
                    "assigned_chapter": item.get("assigned_chapter", chapters[0] if chapters else "Unknown"),
                    "difficulty": item.get("difficulty", "Medium"),
                    "confidence": item.get("confidence", "Medium"),
                    "reasoning": item.get("reasoning", ""),
                })

        except Exception as e:
            print(f"[AI] Batch classification failed: {e}")
            # Fallback: assign questions to first chapter
            for q in batch:
                all_classifications.append({
                    "question_number": q["number"],
                    "assigned_chapter": chapters[0] if chapters else "Unknown",
                    "difficulty": "Medium",
                    "confidence": "Low",
                    "reasoning": f"Auto-assigned (AI error: {str(e)[:80]})",
                })

        # Rate limit delay between batches
        if batch_start + BATCH_SIZE < len(questions):
            time.sleep(1)

    return all_classifications


# ============================================================
# Prompt 2 — AI Summary Generation
# Generates a student-friendly 4-5 sentence summary of the
# analysis results including EFS score and practical advice.
# ============================================================
def generate_summary(
    subject_name: str,
    years: list[int],
    efs_score: float,
    efs_label: str,
    tbi_score: float,
    scs_score: float,
    rp_score: float,
    top_chapters: list[dict],
    never_tested: list[str],
    total_questions: int,
    total_chapters: int,
    chapters_appeared: int,
) -> str:
    """
    Generate an AI summary of the analysis results.

    Returns a 4-5 sentence summary paragraph.
    """
    try:
        # Format top chapters
        top_chapters_str = ", ".join(
            f"{ch['name']} ({ch['count']} questions)" for ch in top_chapters[:5]
        )
        never_tested_str = ", ".join(never_tested) if never_tested else "None"

        # System prompt — from api.md Prompt 2
        system_prompt = (
            "You are an academic analysis assistant for ExamLens, a tool that measures "
            "examination fairness. Write clear, factual, helpful summaries for students. "
            "Be specific with numbers. Do not use jargon. Write in third person about the "
            "exam, not about yourself."
        )

        # User prompt — from api.md Prompt 2
        user_prompt = (
            "Generate a 4–5 sentence plain English summary of this exam analysis. "
            "The summary will be shown to students on their report page. Be specific and actionable.\n\n"
            f"Subject: {subject_name}\n"
            f"Years Analyzed: {', '.join(str(y) for y in years)}\n"
            f"EFS Score: {efs_score:.2f} / 10 ({efs_label})\n"
            f"TBI Score: {tbi_score:.2f} (Topic Bias Index)\n"
            f"SCS Score: {scs_score:.2f} (Syllabus Coverage Score)\n"
            f"RP Score: {rp_score:.2f} (Recurrence Penalty)\n\n"
            f"Most tested chapters: {top_chapters_str}\n"
            f"Never tested chapters: {never_tested_str}\n"
            f"Total questions analyzed: {total_questions}\n"
            f"Total chapters in syllabus: {total_chapters}\n"
            f"Chapters that appeared at least once: {chapters_appeared}\n\n"
            "Write the summary covering:\n"
            "1. Overall fairness verdict with EFS score\n"
            "2. Which topics dominate the exam and by how much\n"
            "3. Which topics have never been tested\n"
            "4. Practical advice for a student preparing for this exam\n"
            "5. One sentence about syllabus coverage\n\n"
            "Respond with only the summary paragraph, no headings or labels."
        )

        result = _chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
            max_tokens=1024,
        )

        return result.strip()

    except Exception as e:
        # Fallback summary if AI fails — as required by rules.md
        return (
            f"Analysis complete. EFS Score: {efs_score:.2f}/10 ({efs_label}). "
            f"{total_questions} questions across {len(years)} year(s) were analyzed "
            f"against {total_chapters} syllabus chapters. "
            f"View the detailed breakdown below."
        )
