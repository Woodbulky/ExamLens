"""
AI Service — Handles all LLM calls for ExamLens.

Provider strategy:
  1. Groq API     (Primary — fastest inference, used for classification & summaries)
  2. Cerebras API (Secondary — used for practice question generation)
  3. NVIDIA API   (Last-resort fallback)

Key rotation:
  Supports multiple API keys per provider (comma-separated in .env).
  Keys are rotated round-robin to distribute load and avoid rate limits.
  Example: GROQ_API_KEY=gsk_key1,gsk_key2,gsk_key3

Task routing:
  - Upload / Classification / Summary / Syllabus Extraction → Groq (fast)
  - Practice Question Generation → Cerebras (creative tasks)
  - If primary fails → fallback chain: Groq → Cerebras → NVIDIA

Used for:
  1. Question classification (chapter, difficulty, confidence)
  2. AI summary generation
  3. Practice question generation
  4. Syllabus chapter extraction
"""

import os
import json
import re
import threading
from dotenv import load_dotenv

load_dotenv()


# --------------- Key Rotation Helper ---------------
RATE_LIMIT_COOLDOWN = 60  # seconds to skip a rate-limited key

class KeyRotator:
    """Thread-safe round-robin API key rotator with rate-limit cooldown.

    Accepts a comma-separated string of keys and cycles through them
    on each call to `next()`. When a key hits a rate limit, it is put
    on cooldown and skipped for subsequent calls until the cooldown expires.
    """

    def __init__(self, env_var: str):
        raw = os.getenv(env_var, "")
        self.keys = [k.strip() for k in raw.split(",") if k.strip()]
        self._index = 0
        self._lock = threading.Lock()
        self._cooldowns: dict[str, float] = {}  # key -> timestamp when cooldown expires

    @property
    def available(self) -> bool:
        return len(self.keys) > 0

    @property
    def count(self) -> int:
        return len(self.keys)

    def mark_rate_limited(self, key: str):
        """Put a key on cooldown after a rate limit error."""
        import time
        with self._lock:
            self._cooldowns[key] = time.time() + RATE_LIMIT_COOLDOWN
            # Advance index past this key so next() skips it
            try:
                limited_idx = self.keys.index(key)
                if self._index % len(self.keys) == limited_idx:
                    self._index += 1
            except ValueError:
                pass
        key_num = self.keys.index(key) + 1 if key in self.keys else "?"
        print(f"    ↳ Key {key_num} on cooldown for {RATE_LIMIT_COOLDOWN}s")

    def _is_cooled_down(self, key: str) -> bool:
        """Check if a key is still on cooldown."""
        import time
        expire = self._cooldowns.get(key)
        if expire is None:
            return False
        if time.time() >= expire:
            # Cooldown expired — remove it
            del self._cooldowns[key]
            return False
        return True

    def next(self) -> str:
        """Return the next available (non-cooled-down) key in round-robin order."""
        if not self.keys:
            raise RuntimeError("No API keys available")
        with self._lock:
            # Try each key in rotation, skipping cooled-down ones
            for _ in range(len(self.keys)):
                key = self.keys[self._index % len(self.keys)]
                self._index += 1
                if not self._is_cooled_down(key):
                    return key
            # All keys on cooldown — return the one closest to expiry
            self._index += 1
            return self.keys[self._index % len(self.keys)]

    def available_keys(self) -> list[str]:
        """Return keys not currently on cooldown (for exhaustive retry)."""
        return [k for k in self.keys if not self._is_cooled_down(k)]

    def all_keys(self) -> list[str]:
        """Return all keys including cooled-down ones (last resort)."""
        return list(self.keys)


# --------------- Provider config ---------------
# Groq — Primary (fastest inference via custom LPU hardware)
groq_keys = KeyRotator("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"

# Cerebras — Secondary (fast inference, used for creative tasks)
cerebras_keys = KeyRotator("CEREBRAS_API_KEY")
CEREBRAS_BASE_URL = "https://api.cerebras.ai/v1"
CEREBRAS_MODEL = "llama-3.3-70b"

# NVIDIA — Last-resort fallback
nvidia_keys = KeyRotator("NVIDIA_API_KEY")
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_MODEL = "meta/llama-3.3-70b-instruct"

# Legacy single-key variables (for backward compat in export router etc.)
GROQ_API_KEY = groq_keys.keys[0] if groq_keys.available else None
CEREBRAS_API_KEY = cerebras_keys.keys[0] if cerebras_keys.available else None
NVIDIA_API_KEY = nvidia_keys.keys[0] if nvidia_keys.available else None

# Expose a MODULE-level MODEL variable for backward compatibility
MODEL = GROQ_MODEL if groq_keys.available else CEREBRAS_MODEL if cerebras_keys.available else NVIDIA_MODEL

# Log key counts at startup
for name, rotator in [("Groq", groq_keys), ("Cerebras", cerebras_keys), ("NVIDIA", nvidia_keys)]:
    if rotator.available:
        print(f"[AI] {name}: {rotator.count} API key(s) loaded")


def _make_groq_client(api_key: str):
    """Create a Groq client with a specific key."""
    from groq import Groq
    return Groq(api_key=api_key)


def _make_cerebras_client(api_key: str):
    """Create a Cerebras client with a specific key."""
    from openai import OpenAI
    return OpenAI(base_url=CEREBRAS_BASE_URL, api_key=api_key)


def _make_nvidia_client(api_key: str):
    """Create an NVIDIA client with a specific key."""
    from openai import OpenAI
    return OpenAI(base_url=NVIDIA_BASE_URL, api_key=api_key)


# Keep legacy client getters for any external code that imports them
def _get_groq_client():
    if not groq_keys.available:
        return None
    return _make_groq_client(groq_keys.next())

def _get_cerebras_client():
    if not cerebras_keys.available:
        return None
    return _make_cerebras_client(cerebras_keys.next())

def _get_nvidia_client():
    if not nvidia_keys.available:
        return None
    return _make_nvidia_client(nvidia_keys.next())


def _try_provider_with_rotation(name: str, rotator: KeyRotator, client_fn, model: str,
                                 messages: list[dict], temperature: float,
                                 max_tokens: int, log_prefix: str = "[AI]") -> str | None:
    """
    Try available keys for a single provider before giving up.
    Skips keys that are on cooldown from recent rate limits.
    Returns the response text on success, raises on failure.
    """
    # Get keys not on cooldown first, fall back to all keys if all cooled down
    keys = rotator.available_keys()
    if not keys:
        keys = rotator.all_keys()
    if not keys:
        return None

    # Start with the round-robin pick, then try the rest
    start_key = rotator.next()
    if start_key in keys:
        ordered_keys = [start_key] + [k for k in keys if k != start_key]
    else:
        ordered_keys = keys

    last_error = None
    for i, key in enumerate(ordered_keys):
        try:
            client = client_fn(key)
            key_num = rotator.all_keys().index(key) + 1 if key in rotator.all_keys() else i + 1
            key_label = f"key {key_num}/{rotator.count}"
            print(f"{log_prefix} Trying {name} ({model}, {key_label})...")
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            print(f"{log_prefix} ✓ {name} succeeded ({key_label})")
            return response.choices[0].message.content
        except Exception as e:
            last_error = e
            error_str = str(e)
            is_rate_limit = any(term in error_str.lower() for term in ["rate_limit", "rate limit", "429", "too many requests"])
            key_num = rotator.all_keys().index(key) + 1 if key in rotator.all_keys() else i + 1
            key_label = f"key {key_num}/{rotator.count}"
            if is_rate_limit:
                rotator.mark_rate_limited(key)
                if i < len(ordered_keys) - 1:
                    print(f"{log_prefix} ⚠ {name} rate limited ({key_label}), rotating to next key...")
                    continue
            print(f"{log_prefix} ✗ {name} failed ({key_label}): {e}")
            break  # Non-rate-limit error or last key — move to next provider

    raise last_error  # Re-raise so the caller can catch it


def _chat_completion(messages: list[dict], temperature: float = 0.1,
                     max_tokens: int = 2048) -> str:
    """
    Send a chat completion request.
    Priority: Groq → Cerebras → NVIDIA.
    Each provider tries all available keys before falling through.
    Used for classification, summaries, and syllabus extraction.
    Returns the raw text content of the first choice.
    """
    providers = []

    if groq_keys.available:
        providers.append(("Groq", groq_keys, _make_groq_client, GROQ_MODEL))
    if cerebras_keys.available:
        providers.append(("Cerebras", cerebras_keys, _make_cerebras_client, CEREBRAS_MODEL))
    if nvidia_keys.available:
        providers.append(("NVIDIA", nvidia_keys, _make_nvidia_client, NVIDIA_MODEL))

    if not providers:
        raise RuntimeError(
            "No AI API key configured. Set GROQ_API_KEY, CEREBRAS_API_KEY, or NVIDIA_API_KEY in .env"
        )

    last_error = None
    for name, rotator, client_fn, model in providers:
        try:
            result = _try_provider_with_rotation(
                name, rotator, client_fn, model,
                messages, temperature, max_tokens, "[AI]"
            )
            if result is not None:
                return result
        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(
        f"All AI providers failed. Last error: {last_error}"
    )


def _chat_completion_cerebras(messages: list[dict], temperature: float = 0.5,
                              max_tokens: int = 4096) -> str:
    """
    Send a chat completion request optimized for creative tasks.
    Priority: Cerebras → Groq → NVIDIA.
    Each provider tries all available keys before falling through.
    Used for practice question generation.
    """
    providers = []

    # Cerebras first for creative/generation tasks
    if cerebras_keys.available:
        providers.append(("Cerebras", cerebras_keys, _make_cerebras_client, CEREBRAS_MODEL))
    if groq_keys.available:
        providers.append(("Groq", groq_keys, _make_groq_client, GROQ_MODEL))
    if nvidia_keys.available:
        providers.append(("NVIDIA", nvidia_keys, _make_nvidia_client, NVIDIA_MODEL))

    if not providers:
        raise RuntimeError(
            "No AI API key configured. Set CEREBRAS_API_KEY, GROQ_API_KEY, or NVIDIA_API_KEY in .env"
        )

    last_error = None
    for name, rotator, client_fn, model in providers:
        try:
            result = _try_provider_with_rotation(
                name, rotator, client_fn, model,
                messages, temperature, max_tokens, "[AI-Creative]"
            )
            if result is not None:
                return result
        except Exception as e:
            last_error = e
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
# assigns difficulty (Easy/Medium/Hard), confidence level,
# Bloom's Taxonomy level, and extracts marks if present.
# ============================================================
def classify_questions(
    questions: list[dict],
    chapters: list[str],
) -> list[dict]:
    """
    Classify exam questions into syllabus chapters using AI.
    Processes in batches of 10 to stay under token limits.

    Also classifies each question by Bloom's Taxonomy level
    and extracts marks allocation from the question text.

    Args:
        questions: List of {"number": int, "text": str}
        chapters: List of chapter names

    Returns:
        List of classification dicts with chapter, difficulty,
        confidence, reasoning, blooms_level, and marks
    """
    if not questions or not chapters:
        return []

    import time

    chapters_list = "\n".join(f"  - {ch}" for ch in chapters)

    # System prompt
    system_prompt = (
        "You are an expert academic analysis assistant. Your job is to analyze "
        "university exam questions and classify each one into the correct syllabus "
        "chapter. You must also assess the difficulty level, your confidence in "
        "the classification, the Bloom's Taxonomy cognitive level, and extract "
        "the marks/points if mentioned in the question.\n\n"
        "Bloom's Taxonomy levels (from lowest to highest cognitive demand):\n"
        "  - Remember: Recall facts, definitions, terms\n"
        "  - Understand: Explain concepts, describe, summarize\n"
        "  - Apply: Use knowledge in new situations, solve problems, calculate\n"
        "  - Analyze: Break down information, compare, contrast, examine\n"
        "  - Evaluate: Justify, critique, assess, judge\n"
        "  - Create: Design, construct, propose, formulate new solutions\n\n"
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
            '- blooms_level: "Remember" | "Understand" | "Apply" | "Analyze" | "Evaluate" | "Create"\n'
            '- marks: integer or null (extract from question text if marks/points are mentioned, e.g. "[5M]", "(10 marks)", "5 pts". If not mentioned, use null)\n'
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
                # Validate blooms_level
                blooms = item.get("blooms_level", "Understand")
                if blooms not in ("Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"):
                    blooms = "Understand"

                # Validate marks
                marks = item.get("marks")
                if marks is not None:
                    try:
                        marks = int(marks)
                        if marks <= 0 or marks > 100:
                            marks = None
                    except (ValueError, TypeError):
                        marks = None

                all_classifications.append({
                    "question_number": item.get("question_number", 0),
                    "assigned_chapter": item.get("assigned_chapter", chapters[0] if chapters else "Unknown"),
                    "difficulty": item.get("difficulty", "Medium"),
                    "confidence": item.get("confidence", "Medium"),
                    "blooms_level": blooms,
                    "marks": marks,
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
                    "blooms_level": "Understand",
                    "marks": None,
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


# ============================================================
# Prompt 3 — Syllabus Chapter Extraction
# Extracts chapter/unit/topic headings from a syllabus PDF.
# Returns a clean list of chapter name strings.
# ============================================================
def extract_syllabus_chapters(raw_text: str) -> list[str]:
    """
    Extract chapter/unit names from syllabus PDF text using AI.

    Args:
        raw_text: Raw text extracted from a syllabus PDF

    Returns:
        List of chapter name strings
    """
    if not raw_text or len(raw_text.strip()) < 20:
        raise ValueError("Syllabus text is too short to extract chapters from.")

    # Truncate to ~6000 chars to stay within token limits
    truncated_text = raw_text[:6000]

    system_prompt = (
        "You are an expert academic assistant. Your job is to extract "
        "chapter names, unit names, module names, or topic headings from "
        "university syllabus documents. Extract ONLY the main chapter/unit "
        "headings — not sub-topics, learning objectives, or reference books.\n\n"
        "Return a JSON array of strings. Each string should be a clean chapter "
        "name without numbering prefixes like 'Unit 1:', 'Chapter 2:', 'Module III:' etc. "
        "Respond ONLY with valid JSON, no preamble, no explanation."
    )

    user_prompt = (
        "Extract the chapter/unit/module names from this syllabus text. "
        "Return them as a JSON array of strings in the order they appear.\n\n"
        "Rules:\n"
        "- Extract only main headings (chapters, units, modules)\n"
        "- Remove numbering prefixes (e.g., 'Unit 1: Arrays' → 'Arrays')\n"
        "- Keep names concise but descriptive\n"
        "- If a heading has a colon, keep only the descriptive part\n"
        "- Typical syllabi have 4–10 chapters. If you find more than 15, "
        "you are likely extracting sub-topics — merge them.\n"
        "- If the text doesn't look like a syllabus, return an empty array []\n\n"
        f"Syllabus Text:\n{truncated_text}"
    )

    try:
        raw = _chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=1024,
        )

        chapters = _parse_json_response(raw)

        if not isinstance(chapters, list):
            raise ValueError("AI returned non-list response.")

        # Clean and validate
        cleaned = []
        for ch in chapters:
            if isinstance(ch, str) and ch.strip():
                cleaned.append(ch.strip())

        if not cleaned:
            raise ValueError("No chapters could be extracted from the syllabus.")

        return cleaned

    except json.JSONDecodeError:
        raise ValueError(
            "AI returned invalid JSON. The syllabus format may not be recognized."
        )
    except Exception as e:
        if "No chapters" in str(e) or "too short" in str(e):
            raise
        raise ValueError(f"Failed to extract chapters: {str(e)}")
