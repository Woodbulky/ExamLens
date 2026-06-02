# ExamLens — Development Rules

## RULE 0 — THE MOST IMPORTANT RULE: ONE PHASE AT A TIME

**Never start Phase N+1 until Phase N is fully complete and tested.**

At the start of every session, state which phase you are working on. Do not jump ahead. Do not partially implement future phases. Do not add features from a later phase "just because they're simple." Each phase has an explicit completion checklist — all items must be checked off before moving forward.

If you are unsure which phase to work on, read `tasks.md` and find the first phase that is not marked `[COMPLETE]`.

---

## RULE 1 — STRICT SEPARATION: FRONTEND AND BACKEND ARE DIFFERENT CODEBASES

- Frontend lives in `/frontend` — built using Stitch MCP
- Backend lives in `/backend` — built using Python FastAPI
- They are **never mixed**
- Frontend never imports Python code
- Backend never serves HTML pages (except a redirect to docs)
- All communication between frontend and backend is via REST API calls defined in `api.md`
- When working on frontend, use Stitch MCP tools
- When working on backend, write Python directly

---

## RULE 2 — FRONTEND NEVER CALLS AI OR DATABASE DIRECTLY

The frontend is only allowed to:
- Call Supabase Auth (login, logout, get session token)
- Call the ExamLens backend API (`VITE_API_BASE_URL`)

The frontend is **never** allowed to:
- Call the Anthropic Claude API
- Call Supabase DB tables directly
- Store or use `ANTHROPIC_API_KEY` anywhere in frontend code
- Store or use `SUPABASE_SERVICE_KEY` anywhere in frontend code

If you find yourself writing a Claude API call in a `.jsx` or `.js` file, stop and move that logic to the backend.

---

## RULE 3 — ENVIRONMENT VARIABLES ARE SACRED

- Never hardcode API keys anywhere in source code
- Never commit `.env` files to git
- Frontend env vars must start with `VITE_` to be accessible
- Backend env vars are loaded via `python-dotenv`
- If a key is missing at startup, the app must fail loudly with a clear error message, not silently

---

## RULE 4 — SUPABASE ROW LEVEL SECURITY IS ALWAYS ON

Every Supabase table must have RLS enabled. Every table must have a policy that ensures users can only access rows where `user_id = auth.uid()`. Never disable RLS for convenience. If data isn't loading, debug the RLS policy — don't disable it.

---

## RULE 5 — AI RESPONSES ARE ALWAYS VALIDATED

When Claude API returns JSON, always:
1. Wrap the parse in a try/catch
2. Validate that the expected fields exist before using them
3. Handle partial responses gracefully (some questions may fail classification)
4. Log failures to console with the raw response for debugging
5. Never crash the entire pipeline because one question failed classification

---

## RULE 6 — ANALYSIS PIPELINE IS ATOMIC

If any step in the analysis pipeline fails:
1. Mark the upload status as `failed` in Supabase
2. Store the error message in the `uploads` table
3. Return a clear error to the frontend
4. Do NOT save partial results as if analysis succeeded
5. Do NOT silently return empty data

The pipeline steps in order:
1. Fetch PDF from Supabase Storage
2. Extract text
3. Extract questions
4. Claude classification
5. EFS calculation
6. Claude summary generation
7. Save to database
8. Mark status as `done`

If step 4 fails, steps 5–8 do not run.

---

## RULE 7 — EVERY AI ANALYSIS GENERATES A SUMMARY

Every time an analysis completes, the `ai_summary` field in the `analyses` table must be populated. This is not optional. The summary is used on the Report page, in exports, and in the Research Export Mode. If summary generation fails, retry once. If it fails again, save a fallback summary: `"Analysis complete. EFS Score: {score}. View the detailed breakdown below."`

---

## RULE 8 — COMMITS ARE PER PHASE

When a phase is complete:
1. Run through the phase completion checklist in `tasks.md`
2. Test every item manually
3. Commit with message format: `phase-{N}: {phase name} complete`
4. Only then update `tasks.md` to mark the phase `[COMPLETE]`

Do not make commits mid-phase unless saving a checkpoint. Checkpoint commits use format: `phase-{N}-wip: {what was done}`

---

## RULE 9 — NO PLACEHOLDER LOGIC IN PRODUCTION CODE

During development, placeholder/mock data is acceptable only in the frontend UI layer for display purposes while the backend is being built. However:

- Never write a backend endpoint that returns hardcoded fake data and call it "done"
- Never mark a phase complete if any endpoint returns mock data
- Never ship a phase where the frontend is calling a backend endpoint that doesn't exist yet

If a backend endpoint is not ready, the frontend should show a clear "coming soon" state, not silently fail or show fake data as real.

---

## RULE 10 — ERRORS ARE ALWAYS SHOWN TO THE USER

When something fails, the user must see a human-readable error message. Never:
- Show a blank screen
- Show a raw error object `{"detail": "..."}`
- Silently fail and show empty data

Always show: what went wrong, and what the user can do about it (retry, contact support, etc.)

---

## RULE 11 — FOLLOW `api.md` EXACTLY

All API endpoints must match the request/response format defined in `api.md` exactly. If a change to the API is needed:
1. Update `api.md` first
2. Then update the backend
3. Then update the frontend

Never change the API in one place without updating the others.

---

## RULE 12 — MOBILE RESPONSIVENESS IS NOT OPTIONAL

Every frontend page must be tested at 375px width (iPhone SE) and 768px width (tablet) before a phase is marked complete. The sidebar must collapse to a hamburger menu on mobile. Charts must not overflow their containers on small screens.

---

## RULE 13 — CODE COMMENTS FOR AI PIPELINE ONLY

Add code comments only where the logic is non-obvious. The EFS calculation in `efs_calculator.py` must be commented line by line explaining the formula. All Claude prompt strings must have a comment above them explaining what they do. Everything else: clean code is self-documenting.

---

## Phase Completion Sign-off Format

When marking a phase complete in `tasks.md`, include:
```
[COMPLETE] Phase N — Phase Name
Completed: YYYY-MM-DD
Tested: manually / with test script
Notes: any known limitations or TODOs for later phases
```