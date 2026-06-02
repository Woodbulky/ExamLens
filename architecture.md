# ExamLens — Architecture

## System Overview

ExamLens is split into two completely separate codebases:
1. **Frontend** — built via Stitch MCP (React), deployed on Vercel
2. **Backend** — Python FastAPI service, deployed on Render.com

They communicate exclusively through REST API calls. The frontend never directly touches the database or AI APIs. All sensitive operations go through the backend.

```
┌─────────────────────────────────────────────────────────────┐
│                        USER BROWSER                          │
│                   React App (Stitch MCP)                     │
│                   Deployed on Vercel                         │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST API calls
                           │ (HTTPS only)
┌──────────────────────────▼──────────────────────────────────┐
│                   BACKEND (FastAPI)                          │
│                 Python — Render.com                          │
│                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ PDF Parser  │  │ Claude API   │  │  EFS Calculator   │  │
│  │ (PyMuPDF)   │  │ (Classifier) │  │  (pandas/numpy)   │  │
│  └─────────────┘  └──────────────┘  └───────────────────┘  │
└──────────┬───────────────────────────────────┬──────────────┘
           │                                   │
┌──────────▼──────────┐           ┌────────────▼─────────────┐
│  SUPABASE STORAGE   │           │    SUPABASE DATABASE      │
│  (PDF Files)        │           │    (PostgreSQL)           │
│  bucket: exam-papers│           │    All structured data    │
└─────────────────────┘           └──────────────────────────┘
                                            │
                                  ┌─────────▼──────────┐
                                  │   CLAUDE API       │
                                  │ (Anthropic)        │
                                  │ Question classify  │
                                  │ Difficulty detect  │
                                  │ Summary generate   │
                                  │ Practice questions │
                                  └────────────────────┘
```

---

## Frontend Architecture

**Technology:** React (generated and managed via Stitch MCP)
**Deployment:** Vercel
**Styling:** Tailwind CSS
**Icons:** Lucide React
**Charts:** Recharts
**HTTP Client:** Axios
**Auth:** Supabase JS client (for auth only)

### Frontend Folder Structure
```
frontend/
├── src/
│   ├── pages/
│   │   ├── Landing.jsx
│   │   ├── Dashboard.jsx
│   │   ├── Upload.jsx
│   │   ├── Report.jsx
│   │   ├── Predictions.jsx
│   │   ├── Export.jsx
│   │   ├── Subjects.jsx
│   │   └── Settings.jsx
│   ├── components/
│   │   ├── Sidebar.jsx
│   │   ├── EFSScoreCard.jsx
│   │   ├── TopicFrequencyChart.jsx
│   │   ├── ChapterTable.jsx
│   │   ├── PredictionList.jsx
│   │   ├── ProgressTracker.jsx
│   │   └── ExportPanel.jsx
│   ├── lib/
│   │   ├── supabaseClient.js   ← Auth only
│   │   └── api.js              ← All backend API calls
│   └── App.jsx
├── .env
│   └── VITE_API_BASE_URL=https://examlens-api.onrender.com
│   └── VITE_SUPABASE_URL=...
│   └── VITE_SUPABASE_ANON_KEY=...
```

### Frontend Rules
- Frontend NEVER calls Claude API directly
- Frontend NEVER calls Supabase DB directly (only Supabase Auth)
- All data fetching goes through `lib/api.js` which calls the backend
- Auth token from Supabase is sent as Bearer token in every backend request

---

## Backend Architecture

**Technology:** Python FastAPI
**Deployment:** Render.com (free tier)
**PDF Parsing:** PyMuPDF (fitz) + pdfplumber fallback
**AI:** Claude API via Anthropic Python SDK
**Data Processing:** pandas, numpy
**Storage Client:** Supabase Python SDK

### Backend Folder Structure
```
backend/
├── main.py                    ← FastAPI app entry point
├── routers/
│   ├── upload.py              ← PDF upload endpoints
│   ├── analysis.py            ← Trigger and fetch analysis
│   ├── report.py              ← Report data endpoints
│   ├── predictions.py         ← Predictions endpoints
│   └── export.py              ← Export endpoints
├── services/
│   ├── pdf_parser.py          ← Extract text from PDFs
│   ├── question_extractor.py  ← Split text into questions
│   ├── claude_service.py      ← All Claude API calls
│   ├── efs_calculator.py      ← EFS Score math
│   ├── prediction_engine.py   ← Topic prediction logic
│   └── export_service.py      ← Generate export files
├── models/
│   └── schemas.py             ← Pydantic request/response models
├── db/
│   └── supabase_client.py     ← Supabase DB client
├── requirements.txt
└── .env
    └── ANTHROPIC_API_KEY=...
    └── SUPABASE_URL=...
    └── SUPABASE_SERVICE_KEY=...
```

---

## Database Architecture (Supabase PostgreSQL)

### Table: `users` (managed by Supabase Auth)
Auto-created by Supabase Auth. Extended via `profiles` table.

### Table: `profiles`
```sql
id          uuid  PRIMARY KEY REFERENCES auth.users(id)
display_name text
created_at  timestamptz DEFAULT now()
```

### Table: `subjects`
```sql
id           uuid  PRIMARY KEY DEFAULT gen_random_uuid()
user_id      uuid  REFERENCES profiles(id)
name         text  NOT NULL
created_at   timestamptz DEFAULT now()
```

### Table: `uploads`
```sql
id           uuid  PRIMARY KEY DEFAULT gen_random_uuid()
subject_id   uuid  REFERENCES subjects(id)
user_id      uuid  REFERENCES profiles(id)
file_path    text  NOT NULL        ← Supabase Storage path
year         int                   ← Exam year (extracted or entered)
filename     text
status       text  DEFAULT 'pending'  ← pending | processing | done | failed
created_at   timestamptz DEFAULT now()
```

### Table: `syllabus_chapters`
```sql
id           uuid  PRIMARY KEY DEFAULT gen_random_uuid()
subject_id   uuid  REFERENCES subjects(id)
chapter_name text  NOT NULL
chapter_order int
```

### Table: `questions`
```sql
id               uuid  PRIMARY KEY DEFAULT gen_random_uuid()
upload_id        uuid  REFERENCES uploads(id)
subject_id       uuid  REFERENCES subjects(id)
question_text    text
assigned_chapter uuid  REFERENCES syllabus_chapters(id)
difficulty       text  ← Easy | Medium | Hard
confidence       text  ← High | Medium | Low
question_number  int
```

### Table: `analyses`
```sql
id              uuid  PRIMARY KEY DEFAULT gen_random_uuid()
subject_id      uuid  REFERENCES subjects(id)
user_id         uuid  REFERENCES profiles(id)
efs_score       float
tbi_score       float
scs_score       float
rp_score        float
efs_label       text
ai_summary      text    ← AI-generated plain English summary paragraph
years_analyzed  int[]   ← Array of years e.g. [2021, 2022, 2023]
created_at      timestamptz DEFAULT now()
```

### Table: `chapter_stats`
```sql
id               uuid  PRIMARY KEY DEFAULT gen_random_uuid()
analysis_id      uuid  REFERENCES analyses(id)
chapter_id       uuid  REFERENCES syllabus_chapters(id)
questions_asked  int
expected_questions float
bias_score       float
status           text  ← Over-tested | Balanced | Ignored
```

### Table: `predictions`
```sql
id           uuid  PRIMARY KEY DEFAULT gen_random_uuid()
analysis_id  uuid  REFERENCES analyses(id)
chapter_id   uuid  REFERENCES syllabus_chapters(id)
rank         int
label        text  ← Very Likely | Likely | Possible
confidence   float
```

### Table: `export_history`
```sql
id           uuid  PRIMARY KEY DEFAULT gen_random_uuid()
user_id      uuid  REFERENCES profiles(id)
analysis_id  uuid  REFERENCES analyses(id)
export_type  text  ← PDF | CSV | JSON | ZIP | PNG
created_at   timestamptz DEFAULT now()
```

### Row Level Security
All tables have RLS enabled. Policy on every table:
```sql
USING (user_id = auth.uid())
```
Users can only read and write their own rows.

---

## AI Pipeline — What Claude Does

Claude is called at 4 distinct points in the pipeline. See `api.md` for full prompt details.

### Call 1 — Question Classification + Difficulty + Confidence
**When:** After PDF text is extracted and questions are split
**Input:** List of questions + list of syllabus chapters
**Output:** JSON mapping each question to a chapter, difficulty level, and confidence score
**Model:** claude-sonnet-4-20250514
**Purpose:** Core classification that powers the entire analysis

### Call 2 — AI Summary Generation
**When:** After EFS Score is calculated
**Input:** Full analysis results (EFS score, chapter stats, bias findings)
**Output:** A 3–5 sentence plain English paragraph summarizing the findings
**Purpose:** Shown on the Report page as the human-readable interpretation. Also included in exports.
**Example output:** "Data Structures exam papers from 2021–2023 show moderate examination bias with an EFS Score of 6.35. Trees and Sorting Algorithms account for nearly half of all questions despite representing only 25% of the syllabus. Dynamic Programming and Graph Theory have never been tested across all three years. Students preparing for this exam should focus heavily on Trees and Sorting while being aware that historically ignored topics could appear. Overall syllabus coverage is 75%, suggesting one-quarter of taught content is never examined."

### Call 3 — Practice Question Generation
**When:** User clicks "Generate Practice Questions" on Predictions page
**Input:** Top 3 predicted chapters + syllabus context
**Output:** 8–10 exam-style practice questions
**Purpose:** Gives students a ready-made revision set based on predicted topics

### Call 4 — Research Methodology Note
**When:** User enables Research Export Mode
**Input:** EFS formula parameters, dataset stats, classification methodology
**Output:** A formal 2-paragraph methodology description suitable for a research paper
**Purpose:** Auto-generates the Methods section content for Harsh's IEEE paper

---

## API Communication Flow

```
1. User uploads PDF on frontend
   → Frontend sends file to backend POST /upload
   → Backend stores PDF in Supabase Storage
   → Backend returns upload_id

2. User submits syllabus and triggers analysis
   → Frontend sends POST /analyze { upload_ids, syllabus, subject_name }
   → Backend starts pipeline:
       a. Fetch PDFs from Supabase Storage
       b. Extract text with PyMuPDF
       c. Extract individual questions
       d. Call Claude API (classification)
       e. Calculate EFS Score
       f. Call Claude API (summary)
       g. Save everything to Supabase DB
   → Backend returns analysis_id

3. Frontend polls GET /analysis/{analysis_id}/status
   → Returns: pending | processing | done | failed
   → When done, frontend navigates to Report page

4. Report page fetches GET /analysis/{analysis_id}
   → Returns full structured report data
   → Frontend renders charts and tables

5. Predictions page fetches GET /analysis/{analysis_id}/predictions
   → Returns ranked prediction list and trend data

6. Export page calls POST /export { analysis_id, format }
   → Backend generates file and returns download URL
```

---

## Deployment Architecture

| Component | Platform | URL Pattern |
|---|---|---|
| Frontend | Vercel | examlens.vercel.app |
| Backend API | Render.com | examlens-api.onrender.com |
| Database | Supabase | (managed) |
| File Storage | Supabase Storage | (managed) |
| AI | Anthropic Claude API | api.anthropic.com |

---

## Environment Variable Map

### Frontend (.env)
```
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
VITE_API_BASE_URL=https://examlens-api.onrender.com
```

### Backend (.env)
```
ANTHROPIC_API_KEY=
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
FRONTEND_URL=https://examlens.vercel.app
```