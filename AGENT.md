# AGENT.md — SIH26166 Development Memory & Documentation Controller

## 1. Role

You are the development agent for the SIH26166 project.

Your job is not only to write code. You must continuously maintain the project's development memory through three living Markdown files:

- `flow.md`
- `progress.md`
- `technical-questions.md`

These files describe the project **as it actually evolves during development**.

Do not assume the architecture, implementation, or technical decisions are fixed.

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

Never make a significant change based only on the user's latest request without understanding the current state recorded in these files.

---

## 3. The Three Living Files

### `flow.md` — CURRENT SYSTEM STATE

`flow.md` is NOT an SRS, PRD, roadmap, or requirements document.

It is the **current implementation/architecture map**.

It answers:

> "How does the system work right now?"

It must describe the system as it exists **after the latest accepted changes**.

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

Architecture is expected to change.

When implementation changes the architecture:

1. update the code;
2. update `flow.md` to reflect the NEW state;
3. record the change in `progress.md`;
4. update `technical-questions.md` if the change resolves or creates a technical question.

Never preserve an outdated architecture merely because it was previously documented.

---

### `progress.md` — DEVELOPMENT HISTORY

`progress.md` is NOT the architecture document.

It answers:

> "What happened during development, when, why, and by whom/which Git branch?"

Record meaningful development events.

Each entry should include:

```text
Date/time:
Git branch:
Change:
Files/modules:
Reason:
Technical impact:
Validation:
Result:
Problems/limitations:
Next step:
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

The Git branch is mandatory for every meaningful entry.

If the agent does not know the branch, inspect Git before writing the entry. Never invent it.

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

Each question should preferably contain:

```text
## Q: <question>

Status: OPEN / ANSWERED / SUPERSEDED

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
- If an answer changes later, preserve the previous understanding in `progress.md` and update the current answer.
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
   "How?"          "What changed?"  "Why/what do we know?"
```

Example:

A developer changes:

```text
SIFT → RIFT2
```

Then:

### `flow.md`

Change the current pipeline:

```text
Preprocessing
→ RIFT2
→ RANSAC
→ Registration
```

### `progress.md`

Record:

```text
Branch: feature/rift2

Changed matcher from SIFT to RIFT2.

Reason:
SIFT failed on tested radiometric-variation pairs.

Validation:
...

Result:
...

```

### `technical-questions.md`

Add/update:

```text
Q: Why does RIFT2 perform better on this pair?

Status: ANSWERED

Evidence:
Benchmark X...

Decision:
Use RIFT2 for this pair class.
```

This is the required relationship.

---

## 5. Development Change Protocol

For every meaningful task:

### Before

Read:

```text
AGENT.md
flow.md
progress.md
technical-questions.md
```

Inspect:

```bash
git branch --show-current
git status --short
```

### During

Understand the existing architecture before changing it.

Prefer the smallest change that solves the task.

Do not unnecessarily redesign unrelated modules.

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

---

## 6. Documentation Decision Rules

### Code changed, architecture unchanged

Usually update:

```text
progress.md
```

Update `technical-questions.md` only if technical understanding changed.

Do not rewrite `flow.md` unnecessarily.

### Architecture changed

Update:

```text
flow.md
progress.md
```

And update:

```text
technical-questions.md
```

if the architectural change creates/resolves a technical question.

### Technical discovery without code change

Update:

```text
technical-questions.md
progress.md
```

Update `flow.md` only if the discovery changes the accepted current architecture.

### Failed experiment

Update:

```text
progress.md
technical-questions.md
```

Update `flow.md` only if the failed experiment changed the current system.

### Rejected proposal

Do not put it into `flow.md`.

If useful, record it in:

```text
progress.md
technical-questions.md
```

with its status clearly marked.

---

## 7. Current vs Historical Information

Never mix these concepts.

`flow.md`:

```text
ONLY current accepted system state
```

`progress.md`:

```text
historical evolution
```

`technical-questions.md`:

```text
current technical understanding + unresolved questions
```

If the architecture was:

```text
SIFT → RANSAC
```

and later becomes:

```text
RIFT2 → RANSAC
```

then `flow.md` should show only:

```text
RIFT2 → RANSAC
```

The fact that SIFT was previously used belongs in `progress.md`.

---

## 8. Git Tracking

Git branch tracking is mandatory because multiple developers/agents may modify the project.

Every meaningful progress entry must include:

```text
Branch: <actual branch>
```

Also record the branch when documenting architecture changes.

If useful, include:

```text
Author/Agent: <developer or agent identifier>
Commit: <hash>
```

but never fabricate these values.

---

## 9. Technical Integrity

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

## 10. SIH26166 Context

The current project is developing an image-correspondence and registration system for Chandrayaan-2 imagery.

The current MVP may use an optical OHRC ↔ TMC-2 pipeline, but this is an implementation state, not a permanent architectural rule.

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

The agent must update the living architecture when these actually become part of the system.

Do not put future plans into `flow.md` as if they already exist.

---

## 11. Validation Documentation

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
- what the metric means.

---

## 12. Completion Checklist

Before declaring a meaningful development task complete:

```text
[ ] Read current AGENT.md
[ ] Read current flow.md
[ ] Read current progress.md
[ ] Read current technical-questions.md
[ ] Inspected Git branch
[ ] Inspected relevant code
[ ] Implemented requested change
[ ] Ran relevant validation/tests
[ ] Inspected output
[ ] Updated flow.md if current architecture changed
[ ] Updated progress.md
[ ] Updated technical-questions.md if knowledge/questions changed
[ ] Recorded actual Git branch
[ ] Recorded unresolved issues
```

The documentation must describe the repository's actual current state when the task is finished.
