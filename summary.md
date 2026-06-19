# ExamLens — Complete Project Summary

> **AI-Powered Examination Fairness Analysis Platform**  
> Built for IEEE TALE / IEEE EDUCON research publication

---

## 📌 Project Overview

ExamLens is a full-stack web application that analyzes university exam papers using AI to quantify examination fairness. It takes past exam papers (PDFs), classifies every question into syllabus chapters using Large Language Models (LLMs), and computes a novel metric called the **Examination Fairness Score (EFS)** — a 0–10 score that measures how fairly an exam covers the syllabus. The platform is designed for both **students** (to understand exam patterns and prepare smartly) and **professors** (to improve exam quality and balance).

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        USER BROWSER                          │
│                   React App (Vite)                            │
│                   Deployed on Vercel                         │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST API calls (HTTPS)
┌──────────────────────────▼──────────────────────────────────┐
│                   BACKEND (FastAPI)                           │
│                 Python — Render.com                           │
│                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ PDF Parser  │  │ Groq / NVIDIA│  │  EFS Calculator   │  │
│  │ (PyMuPDF)   │  │ (Classifier) │  │  (pandas/numpy)   │  │
│  └─────────────┘  └──────────────┘  └───────────────────┘  │
└──────────┬───────────────────────────────────┬──────────────┘
           │                                   │
┌──────────▼──────────┐           ┌────────────▼─────────────┐
│  SUPABASE STORAGE   │           │    SUPABASE DATABASE      │
│  (PDF Files)        │           │    (PostgreSQL)           │
│  bucket: exam-papers│           │    All structured data    │
└─────────────────────┘           └──────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer          | Technology                                    |
|----------------|-----------------------------------------------|
| **Frontend**   | React 18, Vite, React Router v6, Axios        |
| **Styling**    | Vanilla CSS (custom design system)            |
| **Icons**      | Lucide React                                  |
| **Backend**    | Python 3.10+, FastAPI, Uvicorn                |
| **AI / LLM**   | Groq (Primary) → Cerebras → NVIDIA (Fallback) |
| **AI Model**   | Llama 3.3 70B Versatile                       |
| **Database**   | Supabase (PostgreSQL + Auth + Storage)        |
| **PDF Parse**  | PyMuPDF (fitz) + pdfplumber (fallback)        |
| **PDF Export** | ReportLab                                     |
| **Data**       | Pandas, NumPy                                 |
| **Deployment** | Vercel (Frontend) + Render.com (Backend)      |

---

## 📄 Complete Feature List

### 1. 🔐 Authentication System
- **Email/password registration** and login via Supabase Auth
- **JWT-based authentication** — access token sent as `Authorization: Bearer` header
- **Protected routes** — unauthenticated users are redirected to login page
- **Auto profile creation** — `profiles` table entry created on first login
- **Role-based access** — supports `student` and `professor` roles
- Logout functionality with session clearing

### 2. 📤 PDF Upload & Subject Management
- **Drag-and-drop PDF upload** with click-to-browse fallback
- **Multi-file upload** — upload multiple exam papers at once
- Per-file **exam year assignment** (user enters the year for each paper)
- **File validation** — PDF-only, max 20MB, duplicate detection, empty file rejection
- **Subject name input** with auto-creation in database
- Upload progress bar showing real-time percentage
- Files stored securely in **Supabase Storage** bucket (`exam-papers`)
- Upload metadata tracked in `uploads` table with status (`pending → processing → done → failed`)

### 3. 📝 Syllabus Input — Manual & AI Auto-Detect
- **Manual mode** — enter chapter names one per line in a textarea
- **PDF mode (AI Auto-Detect)** — upload a syllabus PDF and let AI extract chapter names automatically
  - Uses LLM (Prompt 3) to identify chapter/unit/module headings from raw PDF text
  - Extracted chapters displayed as editable chips
  - Users can **edit**, **delete**, or **add** chapters after extraction
  - Drag-and-drop support for syllabus PDF
- Toggle between manual and PDF modes

### 4. 🤖 AI Analysis Pipeline (Core Engine)
The analysis pipeline triggers automatically after upload and runs the following steps:

#### Step 1 — PDF Text Extraction
- Uses **PyMuPDF** (primary) with **pdfplumber** fallback
- Handles multi-page PDFs
- Extracts raw text preserving structure

#### Step 2 — Question Extraction
- Identifies individual questions from raw text
- Uses **regex patterns** for numbered questions (Q1, Q2, etc.)
- Falls back to **paragraph splitting** for unstructured papers

#### Step 3 — AI Question Classification (Prompt 1)
- Each question classified into a **syllabus chapter** by the LLM
- **Difficulty level** assigned: Easy / Medium / Hard
- **Confidence score** assigned: High / Medium / Low
- **Reasoning** provided for each classification
- Processed in **batches of 8** to stay within token limits
- Rate limiting with 1-second delay between batches
- Graceful fallback if AI fails (assigns to first chapter with Low confidence)

#### Step 4 — EFS Score Calculation
Computes the **Examination Fairness Score (EFS)** — a novel 0–10 metric:

```
EFS = (TBI × 0.40) + (SCS × 0.35) + (RP × 0.25)

Where:
  TBI = 10 - min(StdDev(ChapterBiasValues) × 2, 10)    ← Topic Bias Index
  SCS = (ChaptersAppeared / TotalChapters) × 10          ← Syllabus Coverage Score
  RP  = 10 - (AvgRecurrenceRateOfTop3 × 10)              ← Recurrence Penalty
```

| EFS Range | Label     | Meaning                              |
|-----------|-----------|--------------------------------------|
| 8.5–10.0  | Excellent | Very fair and balanced exam          |
| 7.0–8.4   | Good      | Mostly fair with minor bias          |
| 5.0–6.9   | Moderate  | Noticeable topic imbalance           |
| 3.0–4.9   | Poor      | Significant bias toward some topics  |
| 0.0–2.9   | Critical  | Heavily biased exam                  |

#### Step 5 — AI Summary Generation (Prompt 2)
- Generates a **4–5 sentence plain English summary** of the findings
- Covers: overall fairness verdict, dominant topics, never-tested chapters, student advice, syllabus coverage
- Fallback summary generated if AI fails

#### Step 6 — Topic Predictions
- Ranks chapters by **historical frequency** across uploaded years
- Assigns prediction labels: **Very Likely / Likely / Possible / Unlikely**
- Calculates appearance rate, avg questions per year, and total questions per chapter

### 5. 📊 Analysis Report Page
- **EFS Score Card** — displays the overall score with TBI, SCS, RP sub-scores and visual bars
- **AI Summary** — plain English interpretation of the analysis
- **Topic Frequency Chart** — horizontal bar chart showing questions per chapter with expected vs. actual comparison
- **Chapter Breakdown Table** — detailed table with questions asked, expected questions, bias score, and status badges (Over-tested / Balanced / Under-tested / Never tested)
- **Never-Tested Topics Callout** — highlights chapters that have never appeared in any exam
- **AI Classification Details** — collapsible section showing individual question classifications
- **Difficulty Distribution** — shows breakdown of Easy / Medium / Hard questions
- Navigation to Predictions, Export, and Study Plan pages

### 6. 🎯 Topic Predictions Page
- **Ranked prediction cards** — chapters ordered by likelihood of appearing in next exam
- **Confidence bars** — visual progress bars showing prediction confidence percentage
- **Prediction labels** — color-coded: Very Likely (green), Likely (teal), Possible (amber), Unlikely (grey)
- **Year-on-Year Trend Table** — shows question counts per chapter per year across all analyzed years
- **Prediction metadata** — total questions, avg per year, appearance rate for each chapter
- **Disclaimer notice** — reminds users predictions are pattern-based, not guarantees
- Link to **AI Study Planner** from this page

### 7. 📝 AI Practice Question Generation
- Generates **8–10 realistic university-level practice questions** based on predicted topics
- Each question includes:
  - Question text
  - Chapter assignment
  - Difficulty level (Easy / Medium / Hard)
  - Marks allocation
  - Question type (Theory / Numerical / Short Answer)
- **Copy individual question** to clipboard
- **Copy all questions** at once
- **Regenerate** button for new set of questions
- Uses **Cerebras API** (optimized for creative tasks) with Groq/NVIDIA fallback

### 8. 📅 AI Study Planner (Recently Added)
- **Personalized day-by-day study schedule** based on exam predictions
- User inputs:
  - **Exam date** (date picker)
  - **Hours per day** available for study (0.5–16 hours)
- AI generates a structured plan with:
  - **Multiple phases** (e.g., Foundation, Deep Dive, Revision)
  - **Daily schedule** with focus topic, date, hours, and priority level
  - **Task chips** for each day
  - **Study tips** section
- Shows overview stats: total study days, total hours, days until exam
- Accessible from the Predictions page via "Create Study Plan" CTA

### 9. 💬 AI Chat Assistant — "Ask ExamLens" (Recently Added)
- **Floating chatbot** available on all authenticated pages (bottom-right FAB button)
- **Context-aware** — automatically detects `analysis_id` from the current URL (Report, Predictions, Export, Study Plan pages)
- When on an analysis page: injects the full analysis data as context (EFS scores, chapter stats, questions, difficulty distribution, etc.)
- When on other pages: provides general overview of user's subjects and recent analyses
- **Suggested prompts** for quick actions:
  - "Which chapters were never tested?"
  - "How has difficulty changed over years?"
  - "Generate 5 hard practice questions"
  - "Summarize my exam analysis"
- **Typing indicator** with animated dots
- **Clean text rendering** — strips markdown artifacts from AI responses
- Auto-scroll to latest message
- Auto-focus input when panel opens
- Responds with plain text formatting (no markdown) for clean chat bubbles

### 10. 👨‍🏫 Professor Dashboard (Recently Added)
- **Role-based access** — only users with `professor` role can access
- **Stats overview** — total exams analyzed, average EFS, best EFS, worst EFS, total questions
- **Exam cards** with EFS scores, TBI/SCS/RP sub-scores, question count, and EFS label badges
- **AI Improvement Suggestions** — per-exam AI-generated suggestions to improve exam fairness
  - Analyzes chapter breakdown, over-tested/under-tested/never-tested chapters
  - Provides 4–6 specific, actionable recommendations
  - Uses Cerebras API for creative suggestions
- **Compare vs Average** — compare any exam's scores against the professor's overall average
  - Side-by-side comparison of EFS, TBI, SCS, RP scores
  - Color-coded: green (better than avg), red (worse than avg), neutral
  - Requires at least 2 analyzed exams
- Quick navigation to full report for each exam

### 11. 📥 Export & Share
- **PDF Report** — professional formatted document with EFS scores, chapter breakdown, question classifications (via ReportLab)
- **CSV Export** — Excel-compatible file with all question classifications (question #, text, chapter, difficulty, confidence, year)
- **JSON Export** — full machine-readable analysis data
- **Research ZIP** — complete IEEE research package containing:
  - AI-generated **methodology note** (Prompt 4) — formal 2-paragraph methodology description suitable for IEEE/Springer submission
  - CSV dataset
  - Full JSON analysis
  - Plain-text analysis summary
- **Shareable public links** — unique token-based URLs (no login required)
- **Export history** — tracks all downloads with timestamps and format types

### 12. 📊 Dashboard
- **Summary stat cards** — papers uploaded, subjects analyzed, average EFS score
- **Recent analyses** list with quick access to reports
- **Quick action tiles** for common tasks (upload, analyze, etc.)

### 13. 📚 Multi-Subject Management
- **Subjects page** listing all analyzed subjects with EFS scores
- Add new subjects with papers
- View all analyses per subject
- Delete subjects and associated data

### 14. ⚙️ Settings Page
- **Edit display name** and email
- **Change password**
- **Delete account** with confirmation

### 15. 🎨 Landing Page
- **Animated hero section** with gradient background and grid pattern
- **Stats bar** with animated counters
- **Feature cards** — AI Classification, EFS Score, Topic Predictions, Research Exports
- **How It Works** — 4-step visual guide
- **EFS Score Explainer** — dark card with TBI/SCS/RP components and sample score ring
- **Call-to-action** sections for signup

---

## 🔄 Complete Application Flow

### User Journey (Student)

```
1. LANDING PAGE
   └→ User visits ExamLens → sees features & EFS explainer
   └→ Clicks "Get Started" → navigates to Signup

2. AUTHENTICATION
   └→ Signs up with email + password
   └→ Profile auto-created in DB
   └→ Redirected to Dashboard

3. DASHBOARD
   └→ Sees stat cards (0 papers, 0 subjects initially)
   └→ Clicks "New Analysis" or "Upload"

4. UPLOAD PAGE
   └→ Enters subject name (e.g., "Data Structures")
   └→ Enters syllabus chapters (manual OR uploads syllabus PDF for AI extraction)
   └→ Drag-drops exam paper PDFs (assigns year to each)
   └→ Clicks "Upload & Analyze"

5. ANALYSIS PIPELINE (Backend — ~60-90 seconds)
   └→ PDFs uploaded to Supabase Storage
   └→ Subject + upload records created in DB
   └→ Syllabus chapters saved to DB
   └→ POST /analyze triggers pipeline:
       a. PDF text extracted (PyMuPDF)
       b. Questions identified (regex + paragraph splitting)
       c. AI classifies each question → chapter, difficulty, confidence
       d. EFS Score calculated (TBI × 0.40 + SCS × 0.35 + RP × 0.25)
       e. AI generates plain-English summary
       f. Predictions generated from historical frequency
       g. All results saved to DB
   └→ Progress bar updates on frontend

6. ANALYSIS COMPLETE
   └→ EFS score and label shown on success screen
   └→ User clicks "View Full Report"

7. REPORT PAGE
   └→ EFS Score card with sub-scores (TBI, SCS, RP)
   └→ AI summary paragraph
   └→ Topic frequency chart (expected vs. actual)
   └→ Chapter breakdown table with status badges
   └→ Never-tested topics highlighted
   └→ Difficulty distribution
   └→ Navigation to Predictions, Export

8. PREDICTIONS PAGE
   └→ Ranked topic cards with confidence bars
   └→ Year-on-year trend table
   └→ "Generate Practice Questions" → AI creates 8-10 exam-style questions
   └→ Copy individual/all questions to clipboard
   └→ "Create Study Plan" CTA → navigates to Study Planner

9. AI STUDY PLANNER
   └→ User enters exam date + hours/day
   └→ AI generates multi-phase day-by-day schedule
   └→ Shows daily focus topics, tasks, and study tips

10. EXPORT PAGE
    └→ Download PDF report / CSV data / JSON export / Research ZIP
    └→ Generate shareable public link
    └→ View export history

11. ASK EXAMLENS (CHATBOT — available on all pages)
    └→ Click floating ✨ button → chat panel opens
    └→ Context-aware: uses current analysis data if on report/predictions page
    └→ Ask about chapters, difficulty trends, generate questions, etc.

12. SUBJECTS PAGE
    └→ View all analyzed subjects with EFS scores
    └→ Click to view latest report
    └→ Add more papers to existing subjects
```

### User Journey (Professor)

```
1. Login → Dashboard (redirected from student dashboard if role = professor)
2. PROFESSOR DASHBOARD
   └→ Stats: total exams, avg/best/worst EFS, total questions
   └→ Exam cards with EFS + sub-scores
   └→ "AI Suggestions" → get improvement recommendations
   └→ "Compare vs Avg" → compare exam against personal averages
   └→ "View Report" → navigate to full analysis
3. Upload & analyze exams (same as student flow)
4. Export research-ready data for publication
```

---

## 🗄️ Database Schema (9 Tables)

| Table                | Purpose                                           |
|----------------------|---------------------------------------------------|
| `profiles`           | User display names, role (student/professor)      |
| `subjects`           | User's exam subjects                              |
| `uploads`            | Uploaded PDF metadata + Supabase Storage paths     |
| `syllabus_chapters`  | Chapter list per subject with ordering             |
| `analyses`           | Analysis records with EFS scores + AI summary      |
| `chapter_stats`      | Per-chapter question counts + bias scores          |
| `questions`          | Individual question classifications                |
| `predictions`        | Topic prediction rankings                          |
| `export_history`     | User export download log                           |

**Security:** All tables have **Row Level Security (RLS)** enabled — users can only access their own data.

---

## 🔌 API Endpoints (Complete)

### Authentication
| Method | Endpoint           | Purpose                |
|--------|--------------------|------------------------|
| POST   | `/auth/signup`     | Register new user      |
| POST   | `/auth/login`      | Login with email/pass  |
| POST   | `/auth/verify`     | Verify JWT token       |

### Subjects
| Method | Endpoint           | Purpose                |
|--------|--------------------|------------------------|
| GET    | `/subjects`        | List user's subjects   |
| POST   | `/subjects`        | Create subject         |
| DELETE | `/subjects/{id}`   | Delete subject + data  |

### Upload & Syllabus
| Method | Endpoint            | Purpose                         |
|--------|---------------------|---------------------------------|
| POST   | `/upload`           | Upload exam PDF                 |
| POST   | `/syllabus`         | Add syllabus chapter            |
| POST   | `/syllabus/extract` | AI-extract chapters from PDF    |

### Analysis
| Method | Endpoint                                | Purpose                          |
|--------|-----------------------------------------|----------------------------------|
| POST   | `/analyze`                              | Run full analysis pipeline       |
| GET    | `/analysis/{id}`                        | Get full report data             |
| GET    | `/analysis/{id}/status`                 | Poll analysis status             |
| GET    | `/analysis/{id}/predictions`            | Get topic predictions            |
| POST   | `/analysis/{id}/practice-questions`     | Generate AI practice questions   |
| POST   | `/analysis/{id}/study-plan`             | Generate AI study plan           |

### Dashboard
| Method | Endpoint            | Purpose              |
|--------|---------------------|----------------------|
| GET    | `/dashboard/stats`  | Dashboard summary    |
| GET    | `/dashboard/recent` | Recent analyses      |

### Export
| Method | Endpoint           | Purpose                       |
|--------|--------------------|-------------------------------|
| POST   | `/export`          | Download PDF/CSV/JSON/ZIP     |
| POST   | `/export/share`    | Generate shareable link       |
| GET    | `/export/history`  | Export download history       |

### Chat
| Method | Endpoint  | Purpose                        |
|--------|-----------|--------------------------------|
| POST   | `/chat`   | AI chat with exam context      |

### Professor
| Method | Endpoint                        | Purpose                         |
|--------|---------------------------------|---------------------------------|
| GET    | `/professor/dashboard`          | Professor stats + exam list     |
| POST   | `/professor/improve`            | AI improvement suggestions      |
| GET    | `/professor/compare/{id}`       | Compare exam vs average         |

---

## 🤖 AI Pipeline — All LLM Calls

ExamLens uses AI at **6 distinct points**:

| #  | Task                           | Provider Priority           | Purpose                                    |
|----|--------------------------------|-----------------------------|--------------------------------------------|
| 1  | Question Classification        | Groq → Cerebras → NVIDIA   | Map questions to chapters + difficulty      |
| 2  | AI Summary Generation          | Groq → Cerebras → NVIDIA   | Plain-English findings paragraph            |
| 3  | Syllabus Chapter Extraction    | Groq → Cerebras → NVIDIA   | Extract chapters from syllabus PDF          |
| 4  | Practice Question Generation   | Cerebras → Groq → NVIDIA   | Create exam-style practice questions        |
| 5  | AI Chat Responses              | Groq → Cerebras → NVIDIA   | Context-aware chatbot answers               |
| 6  | Professor Improvement Suggestions | Cerebras → Groq → NVIDIA | Exam quality improvement recommendations  |

**Fallback Strategy:** Each AI call uses a multi-provider fallback chain. If the primary provider fails, it automatically tries the next provider in the chain.

---

## 🆕 Recently Added Features

### ✅ AI Chat Assistant ("Ask ExamLens")
- Floating chatbot on all authenticated pages
- Context-aware: auto-detects analysis from URL
- Suggested quick prompts
- Clean plain-text responses (no markdown)

### ✅ AI Study Planner
- Personalized day-by-day study schedule
- Based on exam predictions + user's available time
- Multi-phase planning with daily tasks and tips

### ✅ Professor Dashboard
- Role-based professor view
- AI improvement suggestions per exam
- Compare exam scores against personal averages

### ✅ Syllabus Auto-Detect (PDF Upload)
- Upload syllabus PDF instead of typing chapters manually
- AI extracts chapter headings automatically
- Editable/deletable/addable chapter chips after extraction

### ✅ Multi-Provider AI Fallback
- Groq (Primary) → Cerebras (Secondary) → NVIDIA (Fallback)
- Task-specific routing: creative tasks → Cerebras first
- Automatic failover ensures reliability

### ✅ Practice Questions with Copy
- Copy individual questions or all at once
- Formatted with chapter, difficulty, marks, type
- Regenerate button for fresh questions

---

## 🔒 Security & Non-Functional Requirements

| Aspect           | Implementation                                                    |
|------------------|-------------------------------------------------------------------|
| **Authentication** | Supabase Auth with JWT tokens                                    |
| **Authorization**  | Row Level Security on all tables (`user_id = auth.uid()`)        |
| **API Security**   | All keys in environment variables, never in frontend code        |
| **Role Access**    | Professor endpoints validate role before processing              |
| **Performance**    | Analysis pipeline completes within 90 seconds per paper          |
| **Reliability**    | AI fallback chain, graceful error handling, retry on upload fail  |
| **Responsiveness** | Fully responsive on mobile (375px) and desktop                   |
| **CORS**           | Configured for specific allowed origins only                     |

---

## 📂 Project Structure

```
examlens/
├── frontend/                    ← React + Vite
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Landing.jsx          Landing page with hero + features
│   │   │   ├── Login.jsx            Email/password login
│   │   │   ├── Signup.jsx           Registration form
│   │   │   ├── Dashboard.jsx        Student dashboard
│   │   │   ├── ProfDashboard.jsx    Professor dashboard (NEW)
│   │   │   ├── Upload.jsx           PDF upload + syllabus input
│   │   │   ├── Subjects.jsx         Multi-subject management
│   │   │   ├── Report.jsx           Full analysis report
│   │   │   ├── Predictions.jsx      Topic predictions
│   │   │   ├── StudyPlan.jsx        AI study planner (NEW)
│   │   │   ├── Export.jsx           Export & share
│   │   │   └── Settings.jsx         Account settings
│   │   ├── components/
│   │   │   ├── Sidebar.jsx          Navigation sidebar
│   │   │   ├── AppLayout.jsx        Layout wrapper
│   │   │   ├── ChatBot.jsx          AI chat assistant (NEW)
│   │   │   ├── ProtectedRoute.jsx   Auth guard
│   │   │   └── ErrorBoundary.jsx    Error handling
│   │   ├── context/
│   │   │   └── AuthContext.jsx      Auth state management
│   │   └── lib/
│   │       ├── api.js               Axios API client
│   │       └── supabaseClient.js    Supabase Auth client
│   └── index.html
│
├── backend/                     ← Python FastAPI
│   ├── main.py                      Entry point (9 routers registered)
│   ├── middleware/
│   │   └── auth.py                  JWT verification middleware
│   ├── db/
│   │   └── supabase_client.py       Supabase service-role client
│   ├── routers/
│   │   ├── auth.py                  Authentication endpoints
│   │   ├── subjects.py              Subject CRUD
│   │   ├── upload.py                PDF upload handling
│   │   ├── syllabus.py              Syllabus management + AI extraction
│   │   ├── analysis.py              Analysis pipeline + report data
│   │   ├── dashboard.py             Dashboard stats
│   │   ├── export.py                Export (PDF/CSV/JSON/ZIP) + share
│   │   ├── chat.py                  AI chat assistant (NEW)
│   │   └── professor.py             Professor dashboard + suggestions (NEW)
│   └── services/
│       ├── groq_service.py          All AI/LLM calls (multi-provider)
│       ├── pdf_parser.py            PDF text extraction
│       ├── efs_calculator.py        EFS score computation
│       └── prediction_engine.py     Topic prediction logic
│
├── Papers/                      ← Research papers & references
├── README.md                    ← Project overview
├── architecture.md              ← Technical architecture
├── requirements.md              ← Functional requirements
├── api.md                       ← API reference & AI prompts
├── rules.md                     ← Development rules
├── tasks.md                     ← Phase-by-phase task breakdown
├── summary.md                   ← This file
└── render.yaml                  ← Render.com deployment config
```

---

## 🎓 Research Context

- **Target Conferences:** IEEE TALE, IEEE EDUCON, Springer Education & IT (Scopus indexed)
- **Key Contribution:** EFS Score — a novel, reproducible, AI-powered metric for quantifying examination fairness
- **Research Export Mode:** One-click IEEE-formatted ZIP with methodology notes, datasets, and analysis data
- **Reproducibility:** All EFS calculations are deterministic; AI classifications stored with confidence scores for auditability

---

*Built with ❤️ using ExamLens — AI-Powered Examination Fairness Analysis*
