# SIH26166 Frontend — Developer/Agent Protocol

## Role

You are the frontend developer/agent for SIH26166.

You own the dashboard and all visualization logic inside `frontend/`.

You do NOT own the CV pipeline, backend computation, or the API server.

---

## Mandatory Startup

Before any frontend work:

1. Read `AGENT.md` (root level)
2. Read `flow.md` (root level)
3. Read `doc/frontend/README.md`
4. Read `doc/frontend/FRONTEND_PLAN.md`
5. Check `contracts/example_result.json` exists
6. Inspect Git branch
7. Inspect existing `frontend/` code (if any)

---

## Boundaries

### You Own

- `frontend/` — everything inside
- `frontend/app/main.py` — Streamlit entry point
- `frontend/components/` — all visualization components
- `frontend/mock/result.json` — mock data copy
- `frontend/assets/` — placeholder images

### You Do NOT Touch

- `backend/` — CV pipeline code
- `contracts/result.schema.json` — schema definition (read-only, change requires both teams)
- `ground_truth/` — reference dataset

---

## Mock-First Rule

The frontend must always be runnable without the backend.

Load `frontend/mock/result.json` by default.

Keep mock mode functional even after API integration is complete.

---

## Scientific Display Rules

1. Never label reprojection error as "accuracy" or "ground-truth error"
2. Always show the Ground-Truth Validation panel as a **separate section**
3. Use status labels: SUCCESS / SUCCESS_WITHOUT_INDEPENDENT_VALIDATION / LOW_CONFIDENCE / REFERENCE_LIMITED / FAILURE
4. When ground-truth values are null, display "N/A — reference limited" — not zero

---

## After Every Meaningful Change

1. Inspect Git branch
2. Update `progress.md` (root) with your change entry
3. Update `flow.md` if the dashboard architecture changed
4. Update `technical-questions.md` if a technical question arose or was answered

---

## Completion Checklist

```
[ ] Read current documentation
[ ] Inspected Git branch
[ ] Used contracts/example_result.json schema
[ ] Mock mode still works
[ ] Scientific display rules respected
[ ] Updated progress.md
[ ] Updated flow.md if architecture changed
[ ] Updated technical-questions.md if needed
```

---

*Last updated: 2026-08-31*
