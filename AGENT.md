# AGENT.md — SIH26166 Development Memory & Documentation Controller

## 1. Role

You are the development agent for the SIH26166 project.

Your job is not only to write code. You must continuously maintain the project's
development memory through three living Markdown files:

- `flow.md`
- `progress.md`
- `technical-questions.md`

These files describe the project **as it actually evolves during development**.

Do not assume the architecture, implementation, or technical decisions are fixed.

This project is developed by **multiple teammates working on separate Git branches
in parallel**. Every rule in this document is designed to prevent conflicts and
preserve a truthful shared memory across all branches and all contributors.

---

## 2. Mandatory Startup Procedure

Before doing any development work:

1. Read `AGENT.md`.
2. Read `flow.md`.
3. Read `progress.md`.
4. Read `technical-questions.md`.
5. Inspect the current Git branch.
6. Inspect the working tree.
7. Inspect the relevant existing code/modules.
8. Determine whether the requested task changes:
   - architecture;
   - module responsibilities;
   - data flow;
   - interfaces;
   - algorithms;
   - configuration;
   - validation;
   - technical decisions.

Never make a significant change based only on the user's latest request without
understanding the current state recorded in these files.

---

## 3. The Three Living Files

### `flow.md` — CURRENT SYSTEM STATE

`flow.md` is NOT an SRS, PRD, roadmap, or requirements document.

It is the **current implementation/architecture map**.

It answers:

> "How does the system work right now, on `main`?"

It must describe the system as it exists **after the latest accepted changes
merged into `main`**.

Track:

- architecture;
- modules;
- module responsibilities;
- dependencies;
- data flow;
- control flow;
- important interfaces;
- inputs and outputs;
- transformations;
- coordinate conventions;
- configuration flow;
- validation flow;
- dashboard flow;
- external services/dependencies where relevant.

### Critical rule

`flow.md` reflects only **merged, accepted architecture**.

Do not update `flow.md` from a feature branch unless the change has been merged
into `main` or the team has agreed it is accepted.

Architecture is expected to change.

When implementation changes the architecture:

1. update the code;
2. merge or confirm acceptance;
3. update `flow.md` to reflect the NEW state;
4. record the change in `progress.md` with the branch name;
5. update `technical-questions.md` if the change resolves or creates a technical question.

Never preserve an outdated architecture merely because it was previously documented.

---

### `progress.md` — DEVELOPMENT HISTORY

`progress.md` is NOT the architecture document.

It answers:

> "What happened during development, when, why, and by whom/which Git branch?"

Record meaningful development events.

Each entry **MUST** use this exact format:

```text
## Entry NNN — <short title>

Date/time:       <YYYY-MM-DD HH:MM IST>
Git branch:      <exact branch name — never invented>
Author/Agent:    <developer name or agent identifier>
Workstream:      frontend | backend | ground_truth | shared | infra
Change:          <one-line summary>
Files/modules:   <list of files/modules changed>

### What Changed
<detailed description>

### Reason
<why this was done>

### Technical Impact
<what else is affected>

### Validation
<how it was tested>

### Result
<outcome — SUCCESS / PARTIAL / FAILURE>

### Problems/Limitations
<known issues>

### Next Step
<what comes next>
```

Track:

- code changes;
- architecture changes;
- experiments;
- algorithm changes;
- parameter changes that matter;
- validation changes;
- bugs discovered;
- bugs fixed;
- failed approaches;
- decisions;
- reversions;
- important refactors.

Do not record trivial formatting changes.

**The Git branch and Author/Agent are mandatory for every entry. Never invent them.
Run `git branch --show-current` before writing the entry.**

---

### `technical-questions.md` — EVOLVING TECHNICAL KNOWLEDGE

`technical-questions.md` is NOT a predefined exam sheet.

It is a **living technical knowledge base created during development**.

It answers:

> "What technical questions have arisen, what have we learned, and what is still unknown?"

Questions can be added at any time.

They should emerge from:

- implementation;
- debugging;
- experiments;
- architecture decisions;
- benchmark results;
- unexpected behavior;
- judge/pitch preparation;
- code review;
- research;
- disagreements between expected and observed behavior.

Each question **MUST** use this format:

```text
## Q: <question>

Status: OPEN / ANSWERED / SUPERSEDED
Branch-raised: <branch where question was first raised>
Last-updated-by: <developer name or agent>

Context:
Why this question matters.

Answer:
What the current evidence shows.

Evidence:
Code, experiment, documentation, benchmark, or other source.

Decision:
What we currently do.

Confidence:
HIGH / MEDIUM / LOW

Last updated:
<date>

Related modules:
<modules>
```

### Rules

- Do not invent answers before development provides evidence.
- If something is unknown, write `OPEN`.
- If an answer changes later, preserve the previous understanding in `progress.md`
  and update the current answer.
- If a decision is experimental, say so.
- Separate documented fact from inference.
- Separate hypothesis from verified behavior.
- Do not turn assumptions into facts.

---

## 4. How the Three Files Work Together

They have different purposes:

```text
                    AGENT.md
                       |
                       | controls
                       v
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
    flow.md       progress.md   technical-questions.md
        |              |              |
   CURRENT STATE    HISTORY       KNOWLEDGE
        |              |              |
   "How? (main)"   "What changed?  "Why/what do we know?"
                    which branch?"
```

Example:

A developer on `feature/frontend-dashboard` finishes the Streamlit skeleton.

### `progress.md`

```text
## Entry 002 — Frontend Streamlit Skeleton

Date/time:    2026-08-31 18:00 IST
Git branch:   feature/frontend-dashboard
Author/Agent: Alice
Workstream:   frontend
Change:       Created frontend/ directory + Streamlit app skeleton

### What Changed
Created frontend/app/main.py, frontend/mock/result.json ...

### Result
SUCCESS — streamlit run frontend/app/main.py starts without error.
```

### `flow.md`

NOT updated yet. `flow.md` is only updated after this is merged into `main`.

### `technical-questions.md`

Updated only if a technical question arose during the work.

---

## 5. Multi-Branch / Multi-Teammate Rules

### 5.1 Branch Naming Convention

All branches MUST follow this naming scheme:

```text
frontend/<feature>      e.g. frontend/dashboard-skeleton
backend/<feature>       e.g. backend/sift-pipeline
ground_truth/<feature>  e.g. ground_truth/pradan-download
data/<task>             e.g. data/lola-dem
fix/<description>       e.g. fix/ransac-inlier-count
```

### 5.2 Mandatory Branch Header in Every progress.md Entry

When you write a `progress.md` entry, the `Git branch:` field is **not optional**.
It is the primary way teammates know which branch produced the change.

```text
Git branch: feature/backend-sift   ← EXACT branch name from `git branch --show-current`
```

**Never write:**
```text
Git branch: main                   ← WRONG if you're on a feature branch
Git branch: unknown                ← Never acceptable
Git branch: (not recorded)         ← Never acceptable
```

### 5.3 `flow.md` is a Merge-Gate File

`flow.md` describes only **merged, accepted** architecture.

| Situation | Update flow.md? |
|-----------|----------------|
| Working on a feature branch | ❌ NO |
| Feature branch merged to main | ✅ YES |
| Architecture decision agreed but not merged | ❌ NO — wait for merge |
| Hotfix merged directly to main | ✅ YES |

If two branches both change `flow.md`, the **merge conflict is intentional**.
The person resolving the merge must pick the architecture that reflects `main` after the merge.

### 5.4 How to Resolve Conflicts in the Three Living Files

**`progress.md` — append-only, no real conflicts**

`progress.md` is **always append-only**. Each entry has a unique entry number.
New entries go at the **bottom** of the file.

If two branches both add entries, the merge conflict is resolved by keeping **both entries**,
renumbering if necessary. Never delete another branch's entry.

```text
## Entry 003 — [from branch A]     ← keep
...
## Entry 004 — [from branch B]     ← keep
...
```

**`technical-questions.md` — section-based, low conflict risk**

Each question is a separate `## Q:` section.
If two branches add different questions, keep both.
If two branches edit the **same question**, the person resolving the merge must:

1. Read both versions.
2. Write the answer that reflects the current evidence after both branches' work.
3. Update `Last-updated-by` and `Last updated` fields.
4. Record the merge resolution in `progress.md`.

**`flow.md` — last-merged-wins for the affected section**

`flow.md` reflects the **post-merge architecture of `main`**.
When merging two branches that both modified `flow.md`:

1. Do NOT blindly accept either branch's version.
2. Look at what architecture actually exists in the merged code.
3. Write `flow.md` to describe that merged code accurately.
4. Record the resolution in `progress.md`.

### 5.5 Do Not Edit Another Workstream's Files

| Workstream | May edit |
|------------|---------|
| frontend branch | `frontend/`, `progress.md`, `technical-questions.md` |
| backend branch | `backend/`, `progress.md`, `technical-questions.md` |
| data/ground_truth branch | `ground_truth/`, `progress.md`, `technical-questions.md` |
| **Any branch** | `flow.md` only after merge to main |
| **Any branch** | `contracts/` only by explicit team agreement |

No branch should edit another workstream's source directory.

### 5.6 The contracts/ Directory is Shared — Extra Caution

`contracts/result.schema.json` and `contracts/example_result.json` are shared
by frontend and backend.

**Any change to contracts/ requires:**

1. Both frontend and backend teammates agree.
2. The change is recorded in `progress.md` from the branch that made it.
3. The branch name is explicitly stated.
4. `flow.md` is updated after the change is merged to `main`.

### 5.7 Before Raising a Pull Request / Merging

The person merging must:

```text
[ ] Confirm the branch name matches the naming convention
[ ] Confirm progress.md has a valid entry with the correct branch name
[ ] Confirm flow.md does NOT contain unmerged architecture from this branch
[ ] Resolve any conflict in flow.md by looking at merged code
[ ] Resolve any conflict in progress.md by keeping all entries
[ ] Resolve any conflict in technical-questions.md by preserving all questions
[ ] Update flow.md to reflect the post-merge architecture (if architecture changed)
[ ] Add a merge entry to progress.md recording the merge
```

---

## 6. Development Change Protocol

For every meaningful task:

### Before

Run:

```bash
git branch --show-current      # know your branch
git status --short             # know your working tree state
git log --oneline -5           # know recent history
```

Read:

```text
AGENT.md
flow.md
progress.md
technical-questions.md
```

### During

Understand the existing architecture before changing it.

Prefer the smallest change that solves the task.

Do not unnecessarily redesign unrelated modules.

Do not touch another workstream's directory.

### After

Determine whether the change affects:

```text
architecture?
flow?
module responsibility?
interface?
algorithm?
technical understanding?
validation?
```

Then update the appropriate living files.

Always record the **exact branch name** in `progress.md`.

---

## 7. Documentation Decision Rules

### Code changed, architecture unchanged

Usually update:

```text
progress.md   ← with exact branch name
```

Update `technical-questions.md` only if technical understanding changed.

Do not rewrite `flow.md` unless the change is merged to `main` and changes architecture.

### Architecture changed

After merging to `main`, update:

```text
flow.md       ← post-merge, reflects merged code only
progress.md   ← merge entry with branch names involved
```

And update:

```text
technical-questions.md
```

if the architectural change creates/resolves a technical question.

### Technical discovery without code change

Update:

```text
technical-questions.md   ← add Branch-raised field
progress.md              ← with branch name
```

### Failed experiment

Update:

```text
progress.md              ← with branch name
technical-questions.md
```

Update `flow.md` only if the failed experiment changed the current accepted system.

### Rejected proposal

Do not put it into `flow.md`.

Record it in:

```text
progress.md
technical-questions.md
```

with status clearly marked as SUPERSEDED or REJECTED.

---

## 8. Current vs Historical Information

Never mix these concepts.

`flow.md`:

```text
ONLY current accepted system state (after merge to main)
```

`progress.md`:

```text
historical evolution — one entry per meaningful event, each with branch name
```

`technical-questions.md`:

```text
current technical understanding + unresolved questions,
each question tracking which branch raised it
```

---

## 9. Git Tracking — Non-Negotiable

Git branch tracking is mandatory because multiple teammates modify the project
on separate branches simultaneously.

**Every** meaningful progress entry must include:

```text
Git branch:   <exact branch from `git branch --show-current`>
Author/Agent: <name>
```

Also include when available:

```text
Commit: <hash from `git rev-parse --short HEAD`>
```

**Never invent, guess, or omit the branch name.**

If you do not know the branch, run:

```bash
git branch --show-current
```

If the command is unavailable, write:

```text
Git branch: UNKNOWN — could not inspect (reason: <reason>)
```

and resolve it at the next opportunity.

---

## 10. Technical Integrity

Never document something merely because it sounds technically reasonable.

For this project especially:

- do not fabricate accuracy;
- do not fabricate ground truth;
- do not call reprojection error ground-truth accuracy;
- do not claim sub-pixel accuracy without appropriate validation;
- do not claim an algorithm works because the visualization looks good;
- do not hide failed experiments;
- do not silently change coordinate conventions;
- do not silently change transformation direction;
- do not silently change evaluation methodology.

If evidence is missing:

```text
Status: OPEN
```

---

## 11. SIH26166 Context

The current project is developing an image-correspondence and registration system
for Chandrayaan-2 imagery.

The current MVP may use an optical OHRC ↔ TMC-2 pipeline, but this is an
implementation state, not a permanent architectural rule.

Future development may introduce:

- stronger preprocessing;
- different feature/matching algorithms;
- RIFT/RIFT2;
- learned matching;
- IIRS;
- strategy selection;
- sub-pixel refinement;
- validation improvements;
- other components discovered during development.

The agent must update the living architecture when these actually become part
of the system — **after** they are merged into `main`.

Do not put future plans into `flow.md` as if they already exist.

---

## 12. Workstream Ownership Summary

```text
Workstream        Branch prefix         Owns
─────────────────────────────────────────────────────────────
Frontend          frontend/*            frontend/
Backend           backend/*             backend/
Ground Truth      ground_truth/*        ground_truth/
Data              data/*                ground_truth/ (data only)
Shared/Infra      fix/*, infra/*        contracts/, root config
```

No workstream edits another workstream's source directory.

`contracts/` requires explicit agreement from both frontend and backend before change.

---

## 13. Validation Documentation

When a metric is produced, record what it actually measures.

Distinguish:

```text
match statistics
geometric self-consistency
independent ground-truth accuracy
```

If a validation method changes, record:

- what changed;
- why;
- what reference was used;
- whether the reference is independent;
- what the metric means;
- which branch made the change.

---

## 14. Completion Checklist

Before declaring a meaningful development task complete:

```text
[ ] Read current AGENT.md
[ ] Read current flow.md
[ ] Read current progress.md
[ ] Read current technical-questions.md
[ ] Ran: git branch --show-current
[ ] Ran: git status --short
[ ] Inspected relevant code
[ ] Implemented requested change
[ ] Ran relevant validation/tests
[ ] Inspected output
[ ] Did NOT edit another workstream's directory
[ ] Added progress.md entry with correct branch name and author
[ ] Updated technical-questions.md if knowledge/questions changed
[ ] Did NOT update flow.md from feature branch (only after merge to main)
[ ] Recorded unresolved issues
[ ] Raised PR / informed team if contracts/ was changed
```

The documentation must describe the repository's actual current state
when the task is finished.

---

## 15. Quick Reference Card

```text
┌─────────────────────────────────────────────────────────────────┐
│                   MULTI-BRANCH QUICK RULES                      │
├─────────────────────────────────────────────────────────────────┤
│ Branch naming:  frontend/* | backend/* | ground_truth/* | fix/* │
│                                                                 │
│ progress.md:    APPEND ONLY. Always include branch name.        │
│                 Never delete another branch's entry.            │
│                                                                 │
│ flow.md:        ONLY update after merge to main.                │
│                 On a feature branch: DO NOT touch flow.md.      │
│                                                                 │
│ technical-q:    Add questions freely. Keep all questions.       │
│                 Include Branch-raised field.                    │
│                                                                 │
│ contracts/:     Both frontend + backend must agree before edit. │
│                 Record change in progress.md.                   │
│                                                                 │
│ Conflicts:      progress.md → keep both entries                 │
│                 flow.md    → write what merged code actually is │
│                 tech-q     → keep both, merge answer carefully  │
└─────────────────────────────────────────────────────────────────┘
```
