# GEPA Cycle 20 Report — 2026-06-11

**Strategy:** Direct Parent Execution (LLM-as-Judge, Strategy A) — CLI GEPA timed out at 300s on synthetic dataset generation for `llama-cpp` skill (pitfall #31). All 5 skills completed via parent-session patch calls.

**Skills Evolved:** 5 (word-count fallback, delta-driven yielded 0 actionable)

| Skill | From | To | Size Δ | Method |
|-------|------|-----|--------|--------|
| mlops/training/torchtitan | 1.0.0 | 1.1.0 | +4.7KB | trigger_conditions + When to Use + Not For + Pitfalls |
| mlops/inference/llama-cpp | 2.1.2 | 2.2.0 | +5.1KB | trigger_conditions + When to Use + Not For + Pitfalls |
| mlops/cloud/modal | 1.0.0 | 1.1.0 | +4.8KB | trigger_conditions + When to Use + Not For + Pitfalls |
| mlops/training/accelerate | 1.0.0 | 1.1.0 | +4.7KB | trigger_conditions + When to Use + Not For + Pitfalls |
| mlops/vector-databases/pinecone | 1.0.0 | 1.1.0 | +4.7KB | trigger_conditions + When to Use + Not For + Pitfalls |

**Delta-Driven Rationale:** Git log (`--after=2026-06-10 -- skills/`) found 1 commit (move red-team skills to optional-skills). Live-path `find -newer` found 4 skills: flask-web-app-patterns, chroma, vllm, pytorch-lightning. All 4 already at v1.1.0 with all 4 gaps filled from interrupted Cycle 19. Delta-driven = 0 actionable. Fell back to word-count (missing 3+ gaps, size descending).

**Top Blocker:** `write_file` stream timeout on ~13KB content (pitfall #30). Evolved via `patch` with multiple calls instead. **Secondary:** `evolve_skill` CLI hung at synthetic dataset generation (pitfall #31). Strategy A bypassed this entirely.

**Sync Status:** Skills evolved in live path (`~/.hermes/skills/`) but NOT synced to `~/.hermes/hermes-agent/skills/` or `~/hermes-skills/` (pitfall #32). The hermes-agent repo remained clean (behind origin by 68 commits, nothing to commit). Next cycle must explicitly sync before patch generation.

**New Pitfalls Documented:** 30–34 (write_file timeout, CLI dataset hang, Strategy A requires explicit sync, live-path-only skills, interrupted cycle fully-evolved skills).
