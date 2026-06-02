# ExamLens — API Reference

## Base URL
```
Development:  http://localhost:8000
Production:   https://examlens-api.onrender.com
```

## Authentication
All endpoints (except health check) require a Supabase JWT token in the Authorization header:
```
Authorization: Bearer <supabase_access_token>
```
The backend validates this token using the Supabase service key.

---

## Endpoints

### Health Check
```
GET /
Response: { "status": "ExamLens API running" }
```

---

### Upload

#### Upload Exam Paper PDF
```
POST /upload
Content-Type: multipart/form-data

Body:
  file        File    ← PDF file (max 20MB)
  subject_id  string  ← UUID of subject (or "new" to create one)
  subject_name string ← Required if subject_id is "new"
  year        int     ← Exam year e.g. 2023

Response 200:
{
  "upload_id": "uuid",
  "file_path": "exam-papers/user_id/filename.pdf",
  "status": "uploaded"
}

Response 400: { "error": "File too large / Invalid file type" }
```

---

### Analysis

#### Trigger Full Analysis
```
POST /analyze
Content-Type: application/json

Body:
{
  "upload_ids": ["uuid1", "uuid2"],      ← One or more upload IDs
  "subject_id": "uuid",
  "syllabus": [
    "Chapter 1 - Arrays and Strings",
    "Chapter 2 - Linked Lists",
    "Chapter 3 - Trees and Binary Search Trees"
  ]
}

Response 200:
{
  "analysis_id": "uuid",
  "status": "processing"
}
```

#### Poll Analysis Status
```
GET /analysis/{analysis_id}/status

Response 200:
{
  "analysis_id": "uuid",
  "status": "pending | processing | done | failed",
  "progress": {
    "step": "Classifying questions with AI",
    "step_number": 3,
    "total_steps": 5
  },
  "error": null
}
```

#### Get Full Analysis Report
```
GET /analysis/{analysis_id}

Response 200:
{
  "analysis_id": "uuid",
  "subject_name": "Data Structures",
  "years_analyzed": [2021, 2022, 2023],
  "created_at": "2025-05-01T10:30:00Z",

  "efs_score": {
    "total": 6.35,
    "tbi_score": 6.2,
    "scs_score": 7.5,
    "rp_score": 5.0,
    "label": "Moderate"
  },

  "ai_summary": "Data Structures exam papers from 2021–2023 show moderate examination bias...",

  "chapter_stats": [
    {
      "chapter_name": "Arrays and Strings",
      "chapter_order": 1,
      "questions_asked": 18,
      "expected_questions": 7.5,
      "bias_score": 2.4,
      "status": "Over-tested"
    }
  ],

  "never_tested": ["Dynamic Programming", "Graph Theory"],

  "questions": [
    {
      "question_number": 1,
      "question_text": "Explain the time complexity of binary search.",
      "assigned_chapter": "Chapter 4 - Sorting and Searching",
      "difficulty": "Medium",
      "confidence": "High",
      "year": 2023
    }
  ],

  "difficulty_distribution": {
    "Easy": 12,
    "Medium": 28,
    "Hard": 20
  }
}
```

#### Get All Analyses for a Subject
```
GET /subjects/{subject_id}/analyses

Response 200:
{
  "analyses": [
    {
      "analysis_id": "uuid",
      "created_at": "...",
      "efs_score": 6.35,
      "label": "Moderate",
      "years_analyzed": [2021, 2022, 2023]
    }
  ]
}
```

---

### Subjects

#### List All Subjects
```
GET /subjects

Response 200:
{
  "subjects": [
    {
      "subject_id": "uuid",
      "name": "Data Structures",
      "papers_count": 3,
      "latest_efs": 6.35,
      "latest_label": "Moderate",
      "last_analyzed": "2025-05-01T10:30:00Z"
    }
  ]
}
```

#### Create New Subject
```
POST /subjects
Body: { "name": "Data Structures" }
Response 200: { "subject_id": "uuid", "name": "Data Structures" }
```

#### Delete Subject
```
DELETE /subjects/{subject_id}
Response 200: { "deleted": true }
```

---

### Predictions

#### Get Predictions for an Analysis
```
GET /analysis/{analysis_id}/predictions

Response 200:
{
  "predictions": [
    {
      "rank": 1,
      "chapter_name": "Trees and Binary Search Trees",
      "label": "Very Likely",
      "confidence": 0.91,
      "years_appeared": [2021, 2022, 2023],
      "avg_questions_per_year": 5.3
    }
  ],
  "trend_data": {
    "years": [2021, 2022, 2023],
    "chapters": [
      {
        "chapter_name": "Arrays and Strings",
        "counts": [6, 7, 5]
      }
    ]
  }
}
```

#### Generate Practice Questions
```
POST /analysis/{analysis_id}/practice-questions

Response 200:
{
  "questions": [
    {
      "question": "Explain the difference between a binary tree and a binary search tree with an example.",
      "chapter": "Trees and Binary Search Trees",
      "difficulty": "Medium"
    }
  ]
}
```

---

### Export

#### Export Report
```
POST /export
Body:
{
  "analysis_id": "uuid",
  "format": "pdf | csv | json | zip | png_chart | png_scorecard"
}

Response 200:
{
  "download_url": "https://...",
  "expires_at": "2025-05-02T10:30:00Z"
}
```

#### Generate Shareable Link
```
POST /export/share
Body: { "analysis_id": "uuid" }

Response 200:
{
  "share_url": "https://examlens.vercel.app/report/public/abc123",
  "token": "abc123"
}
```

#### Get Export History
```
GET /export/history

Response 200:
{
  "history": [
    {
      "export_type": "PDF",
      "analysis_id": "uuid",
      "subject_name": "Data Structures",
      "created_at": "2025-05-01T10:30:00Z"
    }
  ]
}
```

---

## Claude API Prompts

### Prompt 1 — Question Classification + Difficulty + Confidence

**Used in:** `services/claude_service.py` → `classify_questions()`

**System Prompt:**
```
You are an expert academic analysis assistant. Your job is to analyze university exam questions and classify each one into the correct syllabus chapter. You must also assess the difficulty level and your confidence in the classification.

You will be given:
1. A numbered list of exam questions
2. A list of syllabus chapters

For each question, return a JSON object. Respond ONLY with valid JSON, no preamble, no explanation, no markdown backticks.
```

**User Prompt:**
```
Syllabus Chapters:
{chapters_list}

Exam Questions:
{questions_list}

Classify each question. Return a JSON array where each element has:
- question_number: int
- assigned_chapter: exact chapter name from the syllabus list above
- difficulty: "Easy" | "Medium" | "Hard"
- confidence: "High" | "Medium" | "Low"
- reasoning: one sentence explaining why this chapter was chosen

If a question spans multiple chapters, assign it to the most dominant one.
If a question cannot be matched to any chapter, assign it to the closest chapter and set confidence to "Low".
```

**Expected Output:**
```json
[
  {
    "question_number": 1,
    "assigned_chapter": "Chapter 3 - Trees and Binary Search Trees",
    "difficulty": "Medium",
    "confidence": "High",
    "reasoning": "The question asks about BST insertion which is the core topic of Chapter 3."
  }
]
```

---

### Prompt 2 — AI Summary Generation

**Used in:** `services/claude_service.py` → `generate_summary()`

**System Prompt:**
```
You are an academic analysis assistant for ExamLens, a tool that measures examination fairness. Write clear, factual, helpful summaries for students. Be specific with numbers. Do not use jargon. Write in third person about the exam, not about yourself.
```

**User Prompt:**
```
Generate a 4–5 sentence plain English summary of this exam analysis. The summary will be shown to students on their report page. Be specific and actionable.

Subject: {subject_name}
Years Analyzed: {years}
EFS Score: {efs_score} / 10 ({efs_label})
TBI Score: {tbi_score} (Topic Bias Index)
SCS Score: {scs_score} (Syllabus Coverage Score)
RP Score: {rp_score} (Recurrence Penalty)

Most tested chapters: {top_chapters_with_counts}
Never tested chapters: {never_tested_list}
Total questions analyzed: {total_questions}
Total chapters in syllabus: {total_chapters}
Chapters that appeared at least once: {chapters_appeared}

Write the summary covering:
1. Overall fairness verdict with EFS score
2. Which topics dominate the exam and by how much
3. Which topics have never been tested
4. Practical advice for a student preparing for this exam
5. One sentence about syllabus coverage

Respond with only the summary paragraph, no headings or labels.
```

---

### Prompt 3 — Practice Question Generation

**Used in:** `services/claude_service.py` → `generate_practice_questions()`

**System Prompt:**
```
You are an expert university examiner. Generate realistic exam questions in the same style as university past papers. Questions should test understanding, not just memorization. Match the difficulty distribution of the original exam.
```

**User Prompt:**
```
Generate 8–10 university exam questions for the following subject and chapters.
These are predicted high-probability topics based on historical exam analysis.

Subject: {subject_name}
Target Chapters:
{predicted_chapters_with_labels}

Original exam difficulty distribution:
Easy: {easy_pct}%, Medium: {medium_pct}%, Hard: {hard_pct}%

Requirements:
- Mix question types: theory, numerical, short answer, long answer
- Match the difficulty distribution above
- Questions should be specific and detailed, not vague
- Each question should be answerable in a typical exam setting

Return a JSON array. Each element:
{
  "question": "full question text",
  "chapter": "chapter name",
  "difficulty": "Easy | Medium | Hard",
  "marks": suggested marks (2, 5, or 10),
  "type": "Theory | Numerical | Short Answer | Long Answer"
}

Respond ONLY with valid JSON. No preamble.
```

---

### Prompt 4 — Research Methodology Note

**Used in:** `services/claude_service.py` → `generate_methodology_note()`

**System Prompt:**
```
You are an academic writing assistant. Write formal, precise methodology descriptions suitable for IEEE or Springer journal submission. Use passive voice, precise language, and cite the logical steps clearly. Do not use first person.
```

**User Prompt:**
```
Write a formal 2-paragraph methodology description for the following exam analysis system. This will be included as supplementary material in a research paper submission to IEEE TALE or IEEE EDUCON.

System: ExamLens — AI-Powered Examination Fairness Analysis
Metric: EFS Score (Examination Fairness Score)

EFS Formula:
  EFS = (TBI × 0.40) + (SCS × 0.35) + (RP × 0.25)
  Where:
    TBI = 10 - min(StandardDeviation(ChapterBiasValues) × 2, 10)
    SCS = (ChaptersAppeared / TotalChapters) × 10
    RP = 10 - (AverageRecurrenceRateOfTop3Chapters × 10)

Dataset for this analysis:
  Subject: {subject_name}
  Years analyzed: {years}
  Total questions classified: {total_questions}
  Total syllabus chapters: {total_chapters}
  AI model used: Claude Sonnet (claude-sonnet-4-20250514)
  Classification confidence distribution: High: {high_pct}%, Medium: {med_pct}%, Low: {low_pct}%

Paragraph 1: Describe the data collection and preprocessing methodology (PDF extraction, question segmentation, AI classification).
Paragraph 2: Describe the EFS Score calculation methodology including the three components and their weights.

Use formal academic language. Do not include results, only methodology.
```

---

## Error Codes

| Code | Meaning |
|---|---|
| 400 | Bad request — invalid input |
| 401 | Unauthorized — missing or invalid token |
| 403 | Forbidden — user does not own this resource |
| 404 | Not found |
| 422 | Unprocessable — PDF could not be parsed |
| 500 | Internal server error — pipeline failure |
| 503 | Claude API unavailable |