# ExamLens — Requirements

## Project Overview
ExamLens is an AI-powered web application that analyzes university past exam papers to detect topic bias, measure examination fairness using the EFS Score, and predict likely questions for future exams. It is being built as an ASEP for research publication in IEEE TALE, IEEE EDUCON, or Springer Education and Information Technologies (Scopus indexed).

**Developer:** Harsh (university student, basic Python knowledge)
**AI Coding Agent:** Google Antigravity (AI Studio)
**MCP Servers:** Supabase MCP, Stitch MCP

---

## Functional Requirements

### FR-01 — Authentication
- User can sign up with email and password
- User can log in and log out
- Supabase Auth handles all authentication
- Protected routes redirect unauthenticated users to login

### FR-02 — Exam Paper Upload
- User can upload one or more PDF files (past exam papers)
- User enters the subject name
- User enters syllabus chapters (one per line)
- Files are stored in Supabase Storage bucket: `exam-papers`
- Upload metadata is stored in Supabase DB table: `uploads`

### FR-03 — AI Analysis Pipeline
- On upload submission, a pipeline is triggered:
  1. PDF text extraction (PyMuPDF / pdfplumber)
  2. Question extraction (identify individual questions from raw text)
  3. Claude API classifies each question into a syllabus chapter
  4. Claude API assigns difficulty level (Easy / Medium / Hard) per question
  5. Claude API returns a confidence level (High / Medium / Low) per classification
  6. EFS Score is calculated from the classified data
  7. Predictions are generated based on historical frequency
  8. A structured summary is saved to Supabase DB
- After every analysis, an AI-generated summary paragraph is saved describing the findings in plain English

### FR-04 — EFS Score Calculation
- Three components computed: TBI Score, SCS Score, RP Score
- Final EFS = (TBI × 0.40) + (SCS × 0.35) + (RP × 0.25)
- Score range: 0–10
- Labels: Excellent (8.5–10), Good (7–8.4), Moderate (5–6.9), Poor (3–4.9), Critical (0–2.9)

### FR-05 — Analysis Report
- User can view a full report for any completed analysis
- Report includes: EFS Score card, topic frequency chart, chapter breakdown table, never-tested topics, AI classification details, difficulty distribution

### FR-06 — Predictions
- System predicts likely topics for the next exam
- Based on historical frequency across uploaded years
- Labels: Very Likely, Likely, Possible
- Year-on-year trend chart shown
- "Generate Practice Questions" button triggers Claude API to produce sample questions

### FR-07 — Export
- Export full report as PDF
- Export raw data as CSV / Excel / JSON
- Export individual components as PNG (chart, score card)
- Research Export Mode: ZIP package with methodology notes, metadata, confidence distributions
- Share via unique public URL

### FR-08 — Multi-Subject Management
- User can manage multiple subjects
- My Subjects page lists all analyzed subjects with EFS scores
- User can add more papers to an existing subject

### FR-09 — Dashboard
- Summary stats: papers uploaded, subjects analyzed, average EFS score
- Recent analyses list
- Quick action tiles

### FR-10 — Settings
- Edit display name and email
- Change password
- Delete account

---

## Non-Functional Requirements

### NFR-01 — Performance
- Analysis pipeline completes within 90 seconds for a single paper
- Dashboard loads within 2 seconds
- PDF upload supports files up to 20MB

### NFR-02 — Security
- All API keys stored in environment variables, never in frontend code
- Supabase Row Level Security (RLS) enabled on all tables
- Users can only access their own data

### NFR-03 — Reliability
- Analysis failures are caught and reported to the user with a clear error message
- Failed uploads are retried once automatically

### NFR-04 — Usability
- Fully responsive — works on mobile and desktop
- No action requires more than 3 clicks from the dashboard
- Progress feedback shown during analysis

### NFR-05 — Research Validity
- All EFS Score calculations are deterministic and reproducible
- Methodology is documented and exportable
- AI classifications are stored with confidence scores for auditability

---

## Out of Scope (v1)
- Mobile native app
- Real-time collaboration
- Examiner pattern analysis
- OCR for handwritten papers
- Integration with university LMS systems