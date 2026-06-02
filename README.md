# ExamLens — AI-Powered Examination Fairness Analysis

> 🎓 A web application that analyzes university exam papers using AI to quantify examination fairness through the **Examination Fairness Score (EFS)** — a novel metric designed for IEEE TALE / EDUCON research publication.

---

## 🧠 What is ExamLens?

ExamLens takes past university exam papers (PDF), uses AI to classify each question into syllabus chapters, and calculates a fairness score that reveals:

- **Topic Bias** — Are some chapters over-tested while others are ignored?
- **Syllabus Coverage** — What percentage of the syllabus actually appears in exams?
- **Recurrence Patterns** — Do the same topics dominate year after year?

The result is the **EFS Score (0–10)**, computed as:

```
EFS = (TBI × 0.40) + (SCS × 0.35) + (RP × 0.25)

Where:
  TBI = 10 - min(StdDev(ChapterBiasValues) × 2, 10)   ← Topic Bias Index
  SCS = (ChaptersAppeared / TotalChapters) × 10         ← Syllabus Coverage Score
  RP  = 10 - (AvgRecurrenceRateOfTop3 × 10)             ← Recurrence Penalty
```

| EFS Range | Label     |
|-----------|-----------|
| 8.5–10.0  | Excellent |
| 7.0–8.4   | Good      |
| 5.0–6.9   | Moderate  |
| 3.0–4.9   | Poor      |
| 0.0–2.9   | Critical  |

---

## ✨ Features

### 📄 Upload & Analyze
- Drag-and-drop PDF upload (max 20MB)
- Multi-year paper support
- Syllabus chapter input
- Automatic question extraction (regex + paragraph fallback)

### 🤖 AI Classification
- Each question classified to a syllabus chapter using **Llama 3.3 70B** (via Groq)
- Difficulty assessment (Easy / Medium / Hard)
- Confidence scoring (High / Medium / Low)

### 📊 EFS Score & Report
- Full EFS breakdown with TBI, SCS, RP component bars
- AI-generated summary (student-friendly, specific with numbers)
- Chapter breakdown chart with expected vs. actual comparison
- Never-tested topics callout
- Difficulty distribution visualization

### 🎯 Predictions
- Topics ranked by likelihood of appearing in future exams
- Year-on-year trend table
- AI-generated practice questions based on predicted topics

### 📥 Export & Share
- **PDF Report** — Professional formatted document
- **CSV Data** — Excel-compatible question classifications
- **JSON Export** — Machine-readable full analysis
- **Research ZIP** — IEEE methodology note + all data files
- Shareable public links (no login required)
- WhatsApp share button

### ⚙️ Account Management
- Supabase Auth (email/password)
- Profile editing
- Settings & account deletion

---

## 🏗️ Architecture

```
examlens/
├── frontend/          ← React + Vite
│   ├── src/
│   │   ├── components/   Sidebar, AppLayout, ErrorBoundary, ProtectedRoute
│   │   ├── context/      AuthContext (Supabase JWT)
│   │   ├── lib/          API client (Axios), Supabase client
│   │   └── pages/        Dashboard, Upload, Subjects, Report,
│   │                     Predictions, Export, Settings
│   └── index.html
│
├── backend/           ← Python FastAPI
│   ├── main.py           Entry point (8 routers)
│   ├── middleware/        JWT auth verification
│   ├── db/               Supabase service-role client
│   ├── routers/          auth, subjects, upload, syllabus,
│   │                     analysis, dashboard, export
│   └── services/         pdf_parser, groq_service, efs_calculator,
│                         prediction_engine
│
├── requirements.md       Project specification
├── api.md                API reference & AI prompts
├── rules.md              Development rules
└── tasks.md              Phase-by-phase task breakdown
```

---

## 🛠️ Tech Stack

| Layer      | Technology                          |
|------------|-------------------------------------|
| Frontend   | React 18, Vite, React Router, Axios |
| Styling    | Vanilla CSS (custom design system)  |
| Icons      | Lucide React                        |
| Backend    | Python, FastAPI, Uvicorn            |
| AI / LLM   | Groq API (Llama 3.3 70B Versatile) |
| Database   | Supabase (PostgreSQL + Auth + Storage) |
| PDF Parse  | PyMuPDF + pdfplumber (fallback)     |
| PDF Export | ReportLab                           |
| Data       | Pandas, NumPy                       |

---

## 🚀 Quick Start

### Prerequisites
- **Node.js** ≥ 18
- **Python** ≥ 3.10
- **Supabase** project (free tier works)
- **Groq** API key (free tier — https://console.groq.com)

### 1. Clone & Setup

```bash
git clone <repo-url>
cd examlens
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
```

Create `backend/.env`:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
GROQ_API_KEY=your-groq-api-key
```

Start the backend:
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

Create `frontend/.env`:
```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_API_URL=http://localhost:8000
```

Start the frontend:
```bash
npm run dev
```

### 4. Open the app
Navigate to **http://localhost:5173**

---

## 📐 Database Schema

| Table              | Purpose                                    |
|--------------------|--------------------------------------------|
| `subjects`         | User's exam subjects                       |
| `uploads`          | Uploaded PDF metadata + storage paths      |
| `syllabus_chapters`| Chapter list per subject                   |
| `analyses`         | Analysis records with EFS scores           |
| `chapter_stats`    | Per-chapter question counts + bias scores  |
| `questions`        | Individual question classifications        |
| `predictions`      | Topic prediction rankings                  |
| `export_history`   | User export download log                   |
| `profiles`         | User display names (from auth trigger)     |

---

## 🔬 Research Context

This project is built for **academic research publication** targeting:
- **IEEE TALE** (Teaching, Assessment, Learning and Engineering Education)
- **IEEE EDUCON** (Global Engineering Education Conference)

### Key Contribution
The **EFS Score** is a novel, reproducible metric that quantifies examination fairness using three weighted components. The AI-powered classification pipeline enables automated analysis at scale.

### Research Export Mode
The Export page includes a **Research ZIP** option that generates:
- IEEE-formatted methodology note (generated by AI using Prompt 4)
- CSV dataset of question classifications
- Full JSON analysis data
- Plain-text analysis summary

---

## 📁 API Endpoints

| Method | Endpoint                              | Purpose                          |
|--------|---------------------------------------|----------------------------------|
| POST   | `/auth/signup`                        | Register new user                |
| POST   | `/auth/login`                         | Login with email/password        |
| POST   | `/auth/verify`                        | Verify JWT token                 |
| GET    | `/subjects`                           | List user's subjects             |
| POST   | `/subjects`                           | Create subject                   |
| DELETE | `/subjects/{id}`                      | Delete subject + data            |
| POST   | `/upload`                             | Upload exam PDF                  |
| POST   | `/syllabus`                           | Add syllabus chapter             |
| POST   | `/analyze`                            | Run full analysis pipeline       |
| GET    | `/analysis/{id}`                      | Get full report data             |
| GET    | `/analysis/{id}/status`               | Poll analysis status             |
| GET    | `/analysis/{id}/predictions`          | Get topic predictions            |
| POST   | `/analysis/{id}/practice-questions`   | Generate AI practice questions   |
| GET    | `/dashboard/stats`                    | Dashboard summary stats          |
| GET    | `/dashboard/recent`                   | Recent analyses                  |
| POST   | `/export`                             | Download PDF/CSV/JSON/ZIP        |
| POST   | `/export/share`                       | Generate shareable link          |
| GET    | `/export/history`                     | Export download history          |

---

## 📄 License

This project is part of academic research. All rights reserved.

---

Built with ❤️ using **ExamLens** — AI-Powered Examination Fairness Analysis
