# PRD — SIH26166 MVP (Proctor/Demo Round)
**Product:** Chandrayaan-2 Image Correspondence Engine — MVP
**Owner:** Team
**Timeline:** 3–5 days build (not 7 — cut scope, not time)

---

## 1. Problem
Judges need to see one thing in 90 seconds: two lunar images go in, correct correspondences come out, alignment is visually obvious. Everything else is noise at demo stage.

## 2. Decision: Scope Cut
Build one pipeline, one sensor pair, one algorithm path. No comparisons, no benchmarking, no multimodal, no IIRS. A founder does not build three options to pick the best one in a 5-day sprint — they pick the option most likely to visibly work and commit.

**Pair:** OHRC ↔ TMC-2 (both panchromatic — avoids the radiometric-difference problem entirely, which is Phase 3's job, not the demo's).

## 3. Success Metric (single, binary)
Does the one-click demo produce a visually aligned overlay with a non-trivial inlier count, on a laptop, with zero manual intervention? Yes/No. Nothing else matters for this round.

## 4. In Scope
1. Load source + reference image (grayscale conversion, contrast normalization, optional CLAHE).
2. SIFT feature detection + descriptor generation.
3. BFMatcher/FLANN + Lowe's ratio test.
4. RANSAC homography estimation, inliers vs raw matches visualized separately.
5. Grid-based spatial filtering (prevents match clustering — this is what separates "toy demo" from "credible engineering" to a judge who's seen ten SIFT demos already).
6. Warp source → reference frame; render overlay/blink view.
7. Metrics panel: total matches, inliers, inlier ratio, transform type, coverage score.
8. Single Streamlit app, one upload flow, one "Register" button.

## 5. Explicitly Out of Scope
- Any custom neural network or learned matcher.
- IIRS / hyperspectral anything.
- Multi-pair benchmarking, comparative matcher evaluation.
- User accounts, auth, cloud deployment, mobile.
- Sub-pixel refinement.

If a team member proposes any of the above before Gate A is hit, the answer is no — that's Phase 2+ work, and it competes for the same 5 days.

## 6. Risks and What Most Teams Miss
- **Dataset risk is the real risk, not algorithm risk.** SIFT/RANSAC/homography is solved, boring, and works. The thing that kills teams is not having a clean, verified common-area image pair by day 2. Get the pair first, write zero code until you have it.
- **Teams over-invest in the UI.** Streamlit is a means to show the pipeline, not a product. A judge forgives an ugly UI; they don't forgive a pipeline that silently fails on their sample image.
- **Silent failure at demo time is the actual enemy.** Build a fallback: if inlier count is below a threshold, show that explicitly ("low-confidence registration") instead of crashing or rendering garbage. A visible, honest failure mode reads as engineering maturity to judges; a crash reads as an unfinished project.
- **Metadata loss.** Keep original resolution/geolocation even while working on a downsampled pyramid — needed later, cheap to preserve now, expensive to reconstruct later.

## 7. Acceptance Criteria (Gate A)
- One-click run, no manual point-clicking.
- At least one pair produces geometrically coherent inliers.
- Overlay visibly aligns major terrain features.
- Match coordinates exportable (CSV/JSON).
- Inlier count + ratio shown on dashboard.
- Runs on a CPU-only laptop.

## 8. Team Allocation for This Round
Don't split five ways for a 5-day MVP — that's coordination overhead you can't afford. Two tracks:
- **Pipeline (2 people):** preprocessing → SIFT → matching → RANSAC → warp → metrics.
- **App/Integration (1–2 people):** Streamlit shell, upload flow, visualization panes, export.
Everyone else works dataset acquisition and validation until Gate A is done — that's the actual bottleneck.