# ExamLens — Environment Setup

## Prerequisites

Before starting, install the following tools:

| Tool | Version | Install |
|---|---|---|
| Node.js | 18+ | https://nodejs.org |
| Python | 3.11+ | https://python.org |
| Git | Latest | https://git-scm.com |
| pip | Latest | Comes with Python |

---

## Repository Structure

```
examlens/
├── frontend/          ← React app (Stitch MCP)
├── backend/           ← Python FastAPI
└── docs/              ← This documentation folder
```

---

## Frontend Environment

### Setup Steps

```bash
cd frontend
npm install
cp .env.example .env
```

### `.env` file (frontend)
```
VITE_SUPABASE_URL=https://your-project-id.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key-here
VITE_API_BASE_URL=http://localhost:8000
```

For production, change `VITE_API_BASE_URL` to:
```
VITE_API_BASE_URL=https://examlens-api.onrender.com
```

### Run Frontend Locally
```bash
npm run dev
# Runs at http://localhost:5173
```

### Build for Production
```bash
npm run build
```

---

## Backend Environment

### Setup Steps

```bash
cd backend
python -m venv venv

# On Windows:
venv\Scripts\activate

# On Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

### `.env` file (backend)
```
# Anthropic Claude API
ANTHROPIC_API_KEY=sk-ant-...

# Supabase
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key-here

# CORS — frontend URL allowed to call this API
FRONTEND_URL=http://localhost:5173

# Environment
ENV=development
```

For production backend `.env`:
```
FRONTEND_URL=https://examlens.vercel.app
ENV=production
```

### Run Backend Locally
```bash
uvicorn main:app --reload --port 8000
# Runs at http://localhost:8000
# API docs at http://localhost:8000/docs
```

---

## Supabase Setup

### Step 1 — Create Project
1. Go to https://supabase.com
2. Create a new project
3. Note down: Project URL, anon key, service role key

### Step 2 — Create Storage Bucket
1. Go to Storage in your Supabase dashboard
2. Create a new bucket named: `exam-papers`
3. Set bucket to Private (not public)
4. Add storage policy:
```sql
-- Allow authenticated users to upload their own files
CREATE POLICY "Users can upload own files"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'exam-papers' AND auth.uid()::text = (storage.foldername(name))[1]);

-- Allow authenticated users to read their own files
CREATE POLICY "Users can read own files"
ON storage.objects FOR SELECT
TO authenticated
USING (bucket_id = 'exam-papers' AND auth.uid()::text = (storage.foldername(name))[1]);
```

### Step 3 — Run Database Migrations
Copy and run this SQL in Supabase SQL Editor in order:

```sql
-- 1. Profiles table
CREATE TABLE profiles (
  id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  display_name text,
  created_at timestamptz DEFAULT now()
);
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users manage own profile" ON profiles
  USING (id = auth.uid()) WITH CHECK (id = auth.uid());

-- 2. Subjects table
CREATE TABLE subjects (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES profiles(id) ON DELETE CASCADE,
  name text NOT NULL,
  created_at timestamptz DEFAULT now()
);
ALTER TABLE subjects ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users manage own subjects" ON subjects
  USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

-- 3. Uploads table
CREATE TABLE uploads (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  subject_id uuid REFERENCES subjects(id) ON DELETE CASCADE,
  user_id uuid REFERENCES profiles(id),
  file_path text NOT NULL,
  year int,
  filename text,
  status text DEFAULT 'pending',
  created_at timestamptz DEFAULT now()
);
ALTER TABLE uploads ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users manage own uploads" ON uploads
  USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

-- 4. Syllabus chapters
CREATE TABLE syllabus_chapters (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  subject_id uuid REFERENCES subjects(id) ON DELETE CASCADE,
  chapter_name text NOT NULL,
  chapter_order int DEFAULT 0
);
ALTER TABLE syllabus_chapters ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users manage own chapters" ON syllabus_chapters
  USING (EXISTS (
    SELECT 1 FROM subjects s WHERE s.id = syllabus_chapters.subject_id AND s.user_id = auth.uid()
  ));

-- 5. Questions table
CREATE TABLE questions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  upload_id uuid REFERENCES uploads(id) ON DELETE CASCADE,
  subject_id uuid REFERENCES subjects(id),
  question_text text,
  assigned_chapter uuid REFERENCES syllabus_chapters(id),
  difficulty text CHECK (difficulty IN ('Easy', 'Medium', 'Hard')),
  confidence text CHECK (confidence IN ('High', 'Medium', 'Low')),
  question_number int
);
ALTER TABLE questions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users manage own questions" ON questions
  USING (EXISTS (
    SELECT 1 FROM uploads u WHERE u.id = questions.upload_id AND u.user_id = auth.uid()
  ));

-- 6. Analyses table
CREATE TABLE analyses (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  subject_id uuid REFERENCES subjects(id) ON DELETE CASCADE,
  user_id uuid REFERENCES profiles(id),
  efs_score float,
  tbi_score float,
  scs_score float,
  rp_score float,
  efs_label text,
  ai_summary text,
  years_analyzed int[],
  created_at timestamptz DEFAULT now()
);
ALTER TABLE analyses ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users manage own analyses" ON analyses
  USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

-- 7. Chapter stats
CREATE TABLE chapter_stats (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  analysis_id uuid REFERENCES analyses(id) ON DELETE CASCADE,
  chapter_id uuid REFERENCES syllabus_chapters(id),
  questions_asked int DEFAULT 0,
  expected_questions float,
  bias_score float,
  status text
);
ALTER TABLE chapter_stats ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users manage own chapter stats" ON chapter_stats
  USING (EXISTS (
    SELECT 1 FROM analyses a WHERE a.id = chapter_stats.analysis_id AND a.user_id = auth.uid()
  ));

-- 8. Predictions
CREATE TABLE predictions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  analysis_id uuid REFERENCES analyses(id) ON DELETE CASCADE,
  chapter_id uuid REFERENCES syllabus_chapters(id),
  rank int,
  label text,
  confidence float
);
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users manage own predictions" ON predictions
  USING (EXISTS (
    SELECT 1 FROM analyses a WHERE a.id = predictions.analysis_id AND a.user_id = auth.uid()
  ));

-- 9. Export history
CREATE TABLE export_history (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES profiles(id),
  analysis_id uuid REFERENCES analyses(id),
  export_type text,
  created_at timestamptz DEFAULT now()
);
ALTER TABLE export_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users manage own export history" ON export_history
  USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
```

### Step 4 — Enable Email Auth
1. Go to Authentication > Providers in Supabase
2. Ensure Email provider is enabled
3. Optionally disable email confirmation for development

---

## MCP Server Setup in Google Antigravity

### Supabase MCP
In your Google Antigravity / AI Studio settings, add the Supabase MCP server with:
```
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
```

### Stitch MCP
Connect the Stitch MCP server in AI Studio. This is used exclusively for frontend generation. When asking Antigravity to work on the frontend, reference the Stitch MCP explicitly.

---

## Python Requirements (backend/requirements.txt)

```
fastapi==0.111.0
uvicorn==0.29.0
python-multipart==0.0.9
anthropic==0.25.0
supabase==2.4.0
PyMuPDF==1.24.0
pdfplumber==0.11.0
pandas==2.2.0
numpy==1.26.0
python-dotenv==1.0.1
httpx==0.27.0
pydantic==2.7.0
reportlab==4.1.0
openpyxl==3.1.2
Pillow==10.3.0
```

---

## Local Development Checklist

Before starting development each session:
- [ ] Backend `.env` has all four keys filled in
- [ ] Frontend `.env` has all three keys filled in
- [ ] Supabase project is active (free tier pauses after inactivity)
- [ ] Python venv is activated before running backend
- [ ] Both frontend (port 5173) and backend (port 8000) running simultaneously for full local testing