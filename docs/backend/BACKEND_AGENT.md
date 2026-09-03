# SIH26166 Backend — Developer/Agent Protocol

## Role

You are the backend developer/agent for SIH26166.

You own the CV pipeline, validation logic, serialization, and API server inside `backend/`.

You do NOT own the dashboard, visualization, or frontend presentation.

---

## Mandatory Startup

Before any backend work:

1. Read `AGENT.md` (root level)
2. Read `flow.md` (root level)
3. Read `doc/backend/README.md`
4. Read `doc/backend/BACKEND_PLAN.md`
5. Check `contracts/result.schema.json` exists
6. Inspect Git branch
7. Inspect existing `backend/` code (if any)

---

## Boundaries

### You Own

- `backend/` — everything inside
- `backend/pipeline/` — all CV modules
- `backend/validation/` — ground-truth and synthetic validation
- `backend/api/` — API server
- `backend/models/` — data classes
- `backend/tests/` — test suite

### You Do NOT Touch

- `frontend/` — dashboard code
- `contracts/result.schema.json` — schema definition (read-only; changes require both teams)
- `ground_truth/` — reference dataset (read only, never modify)

---

## Scientific Integrity Rules

1. **Never use ground-truth control points to fit the homography.** CPs are evaluation-only.
2. **Reprojection error ≠ ground-truth accuracy.** These must be separate fields in result.json.
3. **Do not claim sub-pixel accuracy** unless independently validated against LOLA or manually annotated CPs.
4. **Synthetic validation proves implementation correctness** — not real lunar accuracy.
5. **Status must reflect reality:** REFERENCE_LIMITED when CPs have no reference coords.

---

## Coordinate Tracking Rule

Every preprocessing resize must preserve scale mapping:

```python
scale_x = original_width / working_width
scale_y = original_height / working_height

# When reporting metrics, convert working-space coords to original-space:
original_x = working_x * scale_x
original_y = working_y * scale_y
```

Every accuracy metric must state which coordinate system it uses.

---

## Result Schema Compliance

Every pipeline run must produce a `result.json` that validates against:

```
contracts/result.schema.json
```

Do not add fields or change field names without updating the schema AND coordinating with the frontend team.

---

## After Every Meaningful Change

1. Inspect Git branch
2. Update `progress.md` (root) with your change entry
3. Update `flow.md` if the pipeline architecture changed
4. Update `technical-questions.md` if a technical question arose or was answered

---

## Completion Checklist

```
[ ] Read current documentation
[ ] Inspected Git branch
[ ] Result JSON matches contracts/result.schema.json
[ ] Ground-truth CPs NOT used to fit homography
[ ] Reprojection error and GT error clearly separated
[ ] Coordinate scale mapping preserved
[ ] Tests pass
[ ] Updated progress.md
[ ] Updated flow.md if architecture changed
[ ] Updated technical-questions.md if needed
[ ] Unresolved issues documented
```

---

*Last updated: 2026-08-31*
