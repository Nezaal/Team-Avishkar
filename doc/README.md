# SIH26166 Documentation Index

> **Project:** Chandrayaan-2 Autonomous Image Correspondence MVP  
> **Team:** Team Avishkar  
> **Problem Statement:** SIH26166

---

## What This Folder Is

`doc/` is the **master documentation folder** for the SIH26166 project.

It contains:
- Project-wide planning documents (PRD, SRS, MVP Plan)
- Frontend-specific documentation (`doc/frontend/`)
- Backend-specific documentation (`doc/backend/`)

---

## Folder Structure

```
doc/
├── README.md                            ← This file (master index)
├── SIH26166_MVP_PLAN.md                 ← 15-hour parallel implementation plan
├── SIH26166_MVP_PRD_PARALLEL.md         ← Product Requirements Document
├── SIH26166_MVP_SRS_PARALLEL.md         ← Software Requirements Specification
├── SIH26166_Chandrayaan2_Project_Roadmap.docx
├── SIH_2026_Online_Evaluation_Round_II_Rubric.pdf
├── AGENT_4_PARALLEL.md                  ← Parallel-mode agent protocol
│
├── frontend/                            ← Frontend documentation
│   ├── README.md                        ← Frontend overview & ownership
│   ├── FRONTEND_PLAN.md                 ← Component-by-component task list
│   ├── FRONTEND_AGENT.md                ← Frontend developer/agent protocol
│   └── MOCK_DATA_GUIDE.md              ← How to use and extend mock data
│
└── backend/                             ← Backend documentation
    ├── README.md                        ← Backend overview & ownership
    ├── BACKEND_PLAN.md                  ← Pipeline module-by-module plan
    ├── BACKEND_AGENT.md                 ← Backend developer/agent protocol
    └── API_CONTRACT.md                  ← API endpoints & full result schema
```

---

## Living Files (Root Level — NOT in doc/)

These live at the repository root and track the **actual current state** of development.
They are updated by both teams after every meaningful change.

| File | Purpose | Rule |
|------|---------|------|
| `AGENT.md` | Master agent protocol | Read before any work |
| `flow.md` | Current system architecture map | Current state only — no future plans |
| `progress.md` | Development history log | Every meaningful change with Git branch |
| `technical-questions.md` | Technical questions + knowledge | OPEN / ANSWERED / SUPERSEDED |

---

## Quick Reference

| Need | Go to |
|------|-------|
| What to build first | `SIH26166_MVP_PLAN.md` → Section 4 |
| Frontend task list | `frontend/FRONTEND_PLAN.md` |
| Backend task list | `backend/BACKEND_PLAN.md` |
| API schema | `backend/API_CONTRACT.md` |
| Ground truth dataset | `../ground_truth/README.md` |
| Evaluation rubric | `SIH_2026_Online_Evaluation_Round_II_Rubric.pdf` |
| Agent startup | `../AGENT.md` |

---

## Documentation Hierarchy

```
AGENT.md                    ← Master protocol (controls all agents)
    ↓
doc/                        ← Planning and requirements
    ├── Master docs (PRD, SRS, MVP Plan)
    ├── frontend/           ← Frontend team workspace
    └── backend/            ← Backend team workspace
    ↓
Implementation (to be built)
    ├── frontend/           ← Dashboard code
    ├── backend/            ← CV pipeline code
    └── contracts/          ← Shared API schema
    ↓
ground_truth/               ← Scientific reference dataset
```

---

## Current Development State (2026-08-31)

| Component | Status |
|-----------|--------|
| Ground truth dataset | ✅ Complete (20 pairs, 612 CPs) |
| Planning documents | ✅ Complete |
| API contract | ✅ Documented in `doc/backend/API_CONTRACT.md` |
| `contracts/` directory | ❌ Not yet created |
| `frontend/` code | ❌ Not yet started |
| `backend/` code | ❌ Not yet started |

**Next action:** Create `contracts/result.schema.json` and `contracts/example_result.json`.

---

*Last updated: 2026-08-31*
