# Recursive Research v3 — Socratic Enhanced

*Recursive Research with Socratic question improvement at every level.*

**Status**: Design complete, implementation pending

---

## The Core Enhancement

> **Don't just explore questions — improve them as you go.**

v1 and v2 take questions as given and explore them. v3 applies Socratic principles throughout:

- **Before**: Improve the root question before decomposing
- **During**: Challenge assumptions at each decomposition
- **After**: Transform weak leaves into better questions

---

## What's New in v3

| Aspect | v1 | v2 | v3 |
|--------|----|----|-----|
| Root question | Accepted as-is | Prepared (pre-mortem, type ID) | Socratically improved |
| Sub-questions | Generated | MECE checked | Assumption-challenged |
| Weak leaves | Re-researched | Re-researched with critique | Transformed via Socratic process |
| Core addition | — | Critic + Audit | Question Alchemy at every level |

---

## Architecture: Enhanced Flow

```
                    ┌─────────────────┐
                    │ ORIGINAL QUESTION│
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │    SOCRATIC     │  ← NEW: Improve root question
                    │   IMPROVEMENT   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │    PHASE 0:     │
                    │    PREPARE      │  (from v2)
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │    PHASE 1:     │
                    │   DECOMPOSE     │
                    │ + assumption    │  ← NEW: Check assumptions per branch
                    │   challenges    │
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
    ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
    │   IMPROVED    │ │   IMPROVED    │ │   IMPROVED    │
    │ SUB-QUESTION  │ │ SUB-QUESTION  │ │ SUB-QUESTION  │
    └───────┬───────┘ └───────┬───────┘ └───────┬───────┘
            │                │                │
            ▼                ▼                ▼
    ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
    │   EXPLORE     │ │   EXPLORE     │ │   EXPLORE     │
    └───────┬───────┘ └───────┬───────┘ └───────┬───────┘
            │                │                │
            │         [WEAK LEAF?]            │
            │                │                │
            │       ┌────────▼────────┐       │
            │       │    SOCRATIC     │       │  ← NEW: Transform weak leaves
            │       │  TRANSFORMATION │       │
            │       └────────┬────────┘       │
            │                │                │
            └────────────────┼────────────────┘
                             │
                    ┌────────▼────────┐
                    │    PHASE 3:     │
                    │    CRITIQUE     │  (from v2)
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │    PHASE 4:     │
                    │    CONNECT      │  (from v2)
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │    PHASE 5:     │
                    │   SYNTHESIZE    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │    PHASE 6:     │
                    │     AUDIT       │  (from v2)
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │     OUTPUT      │
                    └─────────────────┘
```

---

## The Three Socratic Enhancements

### Enhancement A: Root Question Improvement

**Before any decomposition, improve the root question.**

Apply the Socratic Engine's core process:
1. Excavate assumptions
2. Challenge questionable ones
3. Find the deeper question
4. Reconstruct if needed

**Prompt:**
```
Before researching this question, improve it:

ORIGINAL: [question]

1. ASSUMPTIONS: What does this question assume?
2. CHALLENGES: Which assumptions are questionable?
3. DEEPER: What question lies beneath this one?
4. RECONSTRUCTION: Should we research a better version?

If the question should be improved:
- State the IMPROVED QUESTION
- Explain WHY it's better
- Proceed with the improved version

If the question is already well-formed:
- Confirm it's good
- Note what makes it well-formed
- Proceed as-is
```

---

### Enhancement B: Decomposition with Assumption Checks

**At each decomposition, check assumptions for every sub-question.**

Standard decomposition:
```
Q: Why do startups fail?
├── Q: What are common founder mistakes?
├── Q: What market conditions cause failure?
└── Q: What operational failures occur?
```

Socratic-enhanced decomposition:
```
Q: Why do startups fail? [assumptions checked]
├── Q: What are common founder mistakes?
│   └── [Assumption check: assumes founders are the key variable]
│   └── [Better: "What founder-controllable factors correlate with failure?"]
├── Q: What market conditions cause failure?
│   └── [Assumption check: assumes market is external/fixed]
│   └── [Better: "How does market-founder fit affect outcomes?"]
└── Q: What operational failures occur?
    └── [Assumption check: good as-is, operationally concrete]
```

**Prompt addition for decomposition:**
```
For each sub-question you generate:

1. STATE the sub-question
2. CHECK ASSUMPTIONS: What does this sub-question assume?
3. CHALLENGE: Are any assumptions questionable?
4. IMPROVE: If assumptions are flawed, state a better sub-question
5. PROCEED with the improved version

Only skip improvement if the sub-question's assumptions are solid.
```

---

### Enhancement C: Weak Leaf Transformation

**When a leaf returns weak/empty, don't just re-research — transform the question.**

Standard v2 approach:
```
Leaf returns weak → Re-research the same question
```

Socratic v3 approach:
```
Leaf returns weak → WHY is it weak?
                 → Is the question flawed?
                 → Apply Socratic process
                 → Research the TRANSFORMED question
```

**Prompt:**
```
This leaf returned weak/empty results:

QUESTION: [leaf question]
RESULT: [weak result]

Before re-researching, examine the question:

1. WHY WEAK? Is the question itself the problem?
2. ASSUMPTIONS: What assumptions might be causing the weakness?
3. TRANSFORM: Can we ask a better question that would yield stronger results?

If question should be transformed:
- State the TRANSFORMED QUESTION
- Research that instead

If question is fine and just needs deeper research:
- Confirm the question is well-formed
- Research more deeply
```

---

## Complete Phase Structure

### Phase -1: Socratic Root Improvement (NEW)
- Excavate root question assumptions
- Challenge questionable ones
- Reconstruct if needed
- Proceed with best version of the question

### Phase 0: Prepare (from v2)
- Pre-mortem
- Assumption surfacing (now faster — already did deep version)
- Generativity check
- Type identification

### Phase 1: Decompose with Assumption Checks (ENHANCED)
- MECE breakdown
- Relationship mapping
- **NEW**: Assumption check per sub-question
- **NEW**: Improve sub-questions as needed
- Contrarian injection
- Essence preservation check

### Phase 2: Explore with Leaf Transformation (ENHANCED)
- Multi-lens exploration
- Ensemble at leaves
- Adaptive depth
- **NEW**: Weak leaves trigger Socratic transformation
- **NEW**: Research transformed questions

### Phase 3: Critique (from v2)
- Falsifiability test
- Simplification test
- Weak branch flagging
- Contradiction surfacing

### Phase 4: Connect (from v2)
- Isomorphic patterns
- Tension mapping
- Convergence detection
- Gap identification

### Phase 5: Synthesize (from v2)
- Multi-pass integration
- Confidence quantification
- Tension preservation

### Phase 6: Audit (from v2)
- Blind spot check
- Expertise curse check
- Pre-mortem on synthesis
- Generativity verification

---

## Output Structure

```markdown
# [Final Question Researched]

## Question Evolution
| Stage | Question | Change |
|-------|----------|--------|
| Original | [as given] | — |
| After Socratic | [improved] | [what changed and why] |

## Executive Summary
[Core answer in 2-3 paragraphs]

## Detailed Synthesis
[Full synthesis with confidence tags]

## Confidence Map
### High Confidence
- [Finding 1]

### Medium Confidence
- [Finding 2]

### Low Confidence / Speculation
- [Finding 3]

## Key Tensions
[Unresolved disagreements]

## Question Improvements Made
| Original Sub-Q | Improved Sub-Q | Why |
|----------------|----------------|-----|
| [original] | [improved] | [reasoning] |

## Transformed Weak Leaves
| Weak Question | Transformed To | Result |
|---------------|----------------|--------|
| [weak] | [transformed] | [what we learned] |

## Acknowledged Blind Spots
[What we might be missing]

## Generative Questions
[New questions this research opens]

## Methodology Note
[How this was researched — including Socratic enhancements]
```

---

## When to Use v3

**Use v3 when:**
- Question quality is uncertain
- Previous research on this topic was unsatisfying
- Stakeholders disagree on what to ask
- You have time for depth over speed
- Question seems simple but might hide complexity
- You want the most rigorous version of Recursive Research

**Use v1 when:**
- Speed matters most
- Question is clearly well-formed
- Exploratory/brainstorming mode

**Use v2 when:**
- Need validation but not question transformation
- Question is well-formed but answers need checking
- Moderate rigor, moderate speed

---

## Comparison: v1 vs v2 vs v3

| Aspect | v1 | v2 | v3 |
|--------|----|----|-----|
| Root question | Accepted | Prepared | Socratically improved |
| Decomposition | Simple | MECE + relationships | MECE + assumption-challenged |
| Weak leaves | Accept or re-research | Re-research with critique | Transform via Socratic |
| Quality gates | 0 | 3 (Critique, Connect, Audit) | 4 (+ Socratic at every level) |
| Philosophy | Extract | Extract + Validate | Extract + Validate + Transform |
| Cost | Low | Medium (~3-4x v1) | Higher (~5-6x v1) |
| Best for | Exploration | Important decisions | Uncertain questions |

---

## The Core Insight

> **The quality of research is bounded by the quality of questions. v3 improves questions continuously.**

v1 and v2 assume questions are good enough. v3 makes no such assumption — it improves questions at every opportunity:
- Before starting (root improvement)
- During decomposition (assumption checks)
- When stuck (weak leaf transformation)

---

## Implementation Notes

**Complexity**: Higher than v2
- Socratic improvement adds overhead at multiple points
- But often REDUCES total work by improving questions early
- Weak leaf transformation can be more efficient than brute re-research

**Cost optimization:**
- Use opus for Socratic improvement (requires judgment)
- Use haiku for exploration (volume)
- Only transform leaves that are genuinely weak (don't over-apply)

**Key insight**: Spending 20% more on question improvement can save 50% on research by avoiding dead ends.

---

**The one-sentence summary:**

> **v3 applies Socratic question-improvement throughout the research process — because better questions lead to better answers with less wasted effort.**
