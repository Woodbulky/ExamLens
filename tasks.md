# ExamLens — Task Phases

## How to Use This File

Read Rule 0 in `rules.md` before anything else.
Work on exactly one phase at a time.
Do not start the next phase until every checkbox in the current phase is ticked.
Update this file as you complete tasks.

---

## PHASE 1 — Project Setup & Infrastructure
**Goal:** Both repos exist, environments are configured, Supabase is ready, and you can run both frontend and backend locally.

### Backend Setup
- [ ] Create `/backend` folder
- [ ] Create Python virtual environment
- [ ] Create `requirements.txt` with all dependencies from `environment.md`
- [ ] Install all dependencies
- [ ] Create `main.py` with a basic FastAPI app
- [ ] Create `.env` with all required keys (see `environment.md`)
- [ ] Backend runs locally at `http://localhost:8000`
- [ ] `GET /` returns `{ "status": "ExamLens API running" }`
- [ ] CORS configured to allow frontend URL

### Frontend Setup
- [ ] Create `/frontend` folder using Stitch MCP
- [ ] Create `.env` with all required keys
- [ ] Frontend runs locally at `http://localhost:5173`
- [ ] Supabase client initialized in `lib/supabaseClient.js`
- [ ] API client initialized in `lib/api.js` pointing to backend

### Supabase Setup
- [ ] Supabase project created
- [ ] `exam-papers` storage bucket created with correct policies
- [ ] All 9 database tables created (SQL from `environment.md`)
- [ ] RLS enabled on all tables
- [ ] Email auth enabled
- [ ] Can create a test user and log in via Supabase Auth dashboard

### Completion Checklist
- [ ] Backend health check returns 200
- [ ] Frontend loads without errors
- [ ] Supabase connection works (test auth from frontend)
- [ ] All env vars documented and working

---

## PHASE 2 — Authentication
**Goal:** Users can sign up, log in, and log out. Protected routes work.

### Backend
- [ ] `POST /auth/verify` endpoint that validates a Supabase JWT and returns user info
- [ ] Auth middleware that protects all routes (returns 401 if no valid token)
- [ ] Profile auto-created in `profiles` table on first login

### Frontend (via Stitch MCP)
- [ ] Login page with email and password fields
- [ ] Sign up page with email, password, display name
- [ ] Auth state stored and available across the app
- [ ] Protected route wrapper — unauthenticated users redirected to login
- [ ] Logout button works and clears session
- [ ] Supabase access token sent as `Authorization: Bearer` header on all API calls

### Completion Checklist
- [ ] New user can sign up
- [ ] Existing user can log in
- [ ] Logged-in user sees dashboard
- [ ] Logged-out user redirected to login
- [ ] API calls from frontend include auth token
- [ ] Backend rejects requests with invalid/missing token

---

## PHASE 3 — Upload Flow
**Goal:** User can upload a PDF, enter subject name and syllabus, and see it saved.

### Backend
- [ ] `POST /upload` endpoint — accepts PDF file, saves to Supabase Storage
- [ ] File validation: PDF only, max 20MB
- [ ] Subject created in `subjects` table if new
- [ ] Upload record created in `uploads` table with status `pending`
- [ ] `POST /subjects` endpoint
- [ ] `GET /subjects` endpoint

### Frontend (via Stitch MCP)
- [ ] Upload page with drag-and-drop PDF upload zone
- [ ] Subject name text input
- [ ] Syllabus chapters textarea
- [ ] Validates that all fields are filled before submitting
- [ ] Shows filename and file size after selecting file
- [ ] Calls `POST /upload` and handles response
- [ ] Shows success confirmation after upload

### Completion Checklist
- [ ] PDF uploads to Supabase Storage correctly
- [ ] Upload record appears in Supabase DB
- [ ] Subject record created in DB
- [ ] File size validation works (reject >20MB)
- [ ] File type validation works (reject non-PDFs)
- [ ] UI shows confirmation after successful upload

---

## PHASE 4 — Analysis Pipeline
**Goal:** After upload, full analysis runs and results are saved to DB.

### Backend — PDF Processing
- [ ] `services/pdf_parser.py` extracts raw text from PDF
- [ ] `services/question_extractor.py` splits text into individual questions
- [ ] Handles multi-page PDFs
- [ ] Handles PDFs with numbered questions (Q1, Q2 etc.)

### Backend — Claude Classification
- [ ] `services/claude_service.py` with `classify_questions()` function
- [ ] Uses Prompt 1 from `api.md` exactly
- [ ] Returns list of classifications with chapter, difficulty, confidence
- [ ] Handles Claude API errors gracefully
- [ ] Classifications saved to `questions` table

### Backend — EFS Calculation
- [ ] `services/efs_calculator.py`
- [ ] TBI Score formula implemented and commented
- [ ] SCS Score formula implemented and commented
- [ ] RP Score formula implemented and commented
- [ ] Final EFS formula implemented
- [ ] Label assigned based on score range
- [ ] Results saved to `analyses` and `chapter_stats` tables

### Backend — AI Summary
- [ ] `generate_summary()` in `claude_service.py`
- [ ] Uses Prompt 2 from `api.md` exactly
- [ ] Summary saved to `analyses.ai_summary`
- [ ] Fallback summary if Claude fails

### Backend — API Endpoints
- [ ] `POST /analyze` triggers full pipeline
- [ ] `GET /analysis/{id}/status` returns pipeline progress
- [ ] `GET /analysis/{id}` returns full report data
- [ ] Upload status updated to `done` or `failed` correctly

### Frontend (via Stitch MCP)
- [ ] Submit button on Upload page calls `POST /analyze`
- [ ] Progress screen shows with animated status steps
- [ ] Polls `GET /analysis/{id}/status` every 3 seconds
- [ ] On completion, navigates to Report page
- [ ] On failure, shows error message with retry option

### Completion Checklist
- [ ] Upload a real exam PDF and full pipeline completes
- [ ] Questions extracted correctly
- [ ] Each question classified into a chapter
- [ ] EFS score calculated and makes sense
- [ ] AI summary generated and saved
- [ ] Report page loads with real data

---

## PHASE 5 — Report & Dashboard UI
**Goal:** Report page fully renders all analysis data. Dashboard shows summary stats.

### Frontend (via Stitch MCP)
- [ ] EFS Score card with TBI, SCS, RP sub-scores
- [ ] AI summary paragraph displayed
- [ ] Horizontal bar chart (topic frequency) with color coding
- [ ] Chapter breakdown table with status badges
- [ ] Never-tested chapters callout card
- [ ] AI Classification Details collapsible section
- [ ] Difficulty distribution section
- [ ] Dashboard home with stat cards
- [ ] Recent analyses list
- [ ] My Subjects page with subject cards

### Completion Checklist
- [ ] All report sections render with real data
- [ ] Charts display correctly on mobile
- [ ] Color coding works (red/amber/teal/grey bars)
- [ ] Never-tested callout shows correct chapters
- [ ] Dashboard stats reflect real numbers from DB

---

## PHASE 6 — Predictions
**Goal:** Predictions page shows ranked topics and trend chart.

### Backend
- [ ] `services/prediction_engine.py` — ranks chapters by historical frequency
- [ ] Assigns Very Likely / Likely / Possible labels
- [ ] Calculates year-on-year trend data
- [ ] `GET /analysis/{id}/predictions` endpoint
- [ ] `POST /analysis/{id}/practice-questions` endpoint using Prompt 3
- [ ] Predictions saved to `predictions` table

### Frontend (via Stitch MCP)
- [ ] Predictions page with ranked topic cards
- [ ] Confidence bars on each prediction card
- [ ] Year-on-year trend line chart
- [ ] "Generate Practice Questions" button + modal/panel
- [ ] Disclaimer note about prediction basis

### Completion Checklist
- [ ] Predictions load from real analysis data
- [ ] Practice questions generated by Claude look realistic
- [ ] Trend chart shows multiple years if available
- [ ] Labels (Very Likely etc.) make sense relative to data

---

## PHASE 7 — Export
**Goal:** All export formats work and download correctly.

### Backend
- [ ] PDF report generation (reportlab)
- [ ] CSV export (pandas)
- [ ] JSON export
- [ ] PNG chart export (matplotlib)
- [ ] Research ZIP package (methodology note via Prompt 4 + all files)
- [ ] Shareable public link generation
- [ ] `POST /export` endpoint
- [ ] `POST /export/share` endpoint
- [ ] `GET /export/history` endpoint
- [ ] Export history saved to `export_history` table

### Frontend (via Stitch MCP)
- [ ] Export page with all format tiles
- [ ] Individual component download buttons
- [ ] Research Export Mode toggle
- [ ] Share buttons (copy link + WhatsApp)
- [ ] Export history table at bottom

### Completion Checklist
- [ ] PDF downloads and looks professional
- [ ] CSV opens correctly in Excel
- [ ] JSON is valid and complete
- [ ] Research ZIP contains all required files
- [ ] Share link opens report without login
- [ ] Export history records saved to DB

---

## PHASE 8 — Polish & Research Readiness
**Goal:** App is production-ready and research paper can be submitted.

- [ ] All pages fully responsive on mobile (375px)
- [ ] Loading states on all data-fetching operations
- [ ] Empty states for users with no data yet
- [ ] Error boundaries on all pages
- [ ] Settings page (edit name, change password, delete account)
- [ ] Onboarding flow for new users (sample data walkthrough)
- [ ] Deploy backend to Render.com
- [ ] Deploy frontend to Vercel
- [ ] Production env vars set on both platforms
- [ ] End-to-end test with real exam papers
- [ ] Research Export Mode generates valid methodology note
- [ ] Dataset of at least 3 subjects × 3 years collected for paper

---

## Phase Status Summary

| Phase | Name | Status |
|---|---|---|
| 1 | Project Setup & Infrastructure | [ ] Not Started |
| 2 | Authentication | [ ] Not Started |
| 3 | Upload Flow | [ ] Not Started |
| 4 | Analysis Pipeline | [ ] Not Started |
| 5 | Report & Dashboard UI | [ ] Not Started |
| 6 | Predictions | [ ] Not Started |
| 7 | Export | [ ] Not Started |
| 8 | Polish & Research Readiness | [ ] Not Started |