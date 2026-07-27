# Recursive Research v2 — With Critic and Audit

*Enhanced with adversarial validation, cross-branch integration, and blind spot detection.*

**Status**: Design complete, implementation pending

## Philosophy

**v1**: "Explore, then synthesize" — trusts outputs
**v2**: "Explore, challenge, connect, synthesize, audit" — verifies outputs

The core insight from 156 research recipes: **you can't see your own blind spots from inside**. v2 adds adversarial checkpoints at every junction.

## The Complete Flow

```
QUESTION
    ↓
┌─────────────────────────────────────┐
│  PHASE 0: PREPARE                   │
│  - Pre-mortem the question          │
│  - Surface assumptions              │
│  - Check generativity               │
│  - Identify question type           │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  PHASE 1: DECOMPOSE                 │
│  - MECE breakdown                   │
│  - Relationship mapping             │
│  - Contrarian injection             │
│  - Essence preservation check       │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  PHASE 2: EXPLORE (parallel)        │
│  - Multi-lens exploration           │
│  - Ensemble at leaves               │
│  - Adaptive depth (signal-based)    │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  PHASE 3: CRITIQUE ← NEW            │
│  - Falsifiability test              │
│  - Simplification test              │
│  - Weak branch flagging             │
│  - Contradiction surfacing          │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  PHASE 4: CONNECT ← NEW             │
│  - Isomorphic patterns              │
│  - Tension mapping                  │
│  - Convergence detection            │
│  - Gap identification               │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  PHASE 5: SYNTHESIZE                │
│  - Multi-pass integration           │
│  - Confidence quantification        │
│  - Tension preservation             │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  PHASE 6: AUDIT ← NEW               │
│  - Blind spot check                 │
│  - Expertise curse check            │
│  - Pre-mortem on synthesis          │
│  - Generativity verification        │
└─────────────────────────────────────┘
    ↓
FINAL OUTPUT
(with confidence map + tensions + blind spots + new questions)
```

---

## Phase Details

### Phase 0: Question Preparation

Before decomposition, interrogate the question itself.

**Apply:**
- **Pre-mortem**: "If this research completely fails, why?" Surface risks before starting
- **Assumption excavation**: What does this question take for granted?
- **Generativity check**: Is this question opening inquiry or seeking a known answer?
- **Type identification**:
  - Empirical (facts) — needs evidence
  - Conceptual (definitions) — needs clarity
  - Normative (values) — needs perspective diversity
  - Procedural (how-to) — needs practical grounding

**The sauce**: Most research fails because the question was poorly formed. Five minutes here saves hours of wasted exploration.

**Prompt sketch:**
```
Before exploring this question, analyze it:

1. PRE-MORTEM: If research on this question fails completely, what are the likely reasons?
2. ASSUMPTIONS: What does this question take for granted that might be wrong?
3. GENERATIVITY: Does this question open inquiry (good) or seek a known answer (reframe)?
4. TYPE: Is this empirical, conceptual, normative, or procedural? How does that affect approach?

Based on this analysis, either:
- Proceed with the question as-is
- Suggest a reframed question that's more productive
- Flag specific risks to watch for during research
```

---

### Phase 1: Decomposition with Quality Gates

Not all sub-questions are equal. Before spawning children:

**Apply:**
- **MECE check**: Mutually exclusive? Collectively exhaustive? Overlapping = redundancy. Gaps = blind spots.
- **Relationship mapping**:
  - Prerequisite (must answer first)
  - Parallel (independent)
  - Contradictory (tension with siblings)
  - Refinement (zoom-in)
- **Contrarian injection**: For every 5-7 "obvious" questions, add 1-2 that challenge the frame
- **Essence preservation check**: Do sub-questions combined answer the original? Or did we drift?

**The sauce**: HOW you break down determines WHAT you can discover. Bad decomposition guarantees blind spots.

**Prompt sketch:**
```
Decompose this question into research angles. For each angle:

1. State the sub-question (Q: format)
2. Tag relationship type: [PREREQ] [PARALLEL] [TENSION] [REFINEMENT]
3. Rate independence from siblings (High/Medium/Low)

Requirements:
- Ensure MECE: no overlaps, no gaps
- Include 1-2 contrarian questions that challenge the question's assumptions
- After listing, verify: do these sub-questions fully cover the original? What's missing?

Format:
Q: [sub-question] [RELATIONSHIP_TAG] [Independence: X]
```

---

### Phase 2: Parallel Exploration with Diversity

v1 does this well, but v2 adds intentional diversity:

**Apply:**
- **Lens rotation**: Don't just ask "What's the answer?" Use multiple lenses:
  - Primary researcher: Answer directly
  - Skeptic lens: What's wrong with the obvious answer?
  - Analogist lens: Where else does this pattern appear?
- **Ensemble at leaves**: 2-4 models answer same question, then merge (Inverted-U: more isn't better)
- **Adaptive depth signals**: Continue or stop based on signals, not fixed depth:
  - Repetition (same insights reworded) → STOP
  - Circular references (branches citing each other) → STOP
  - Diminishing specificity (answers getting vaguer) → STOP
  - High signal density (new insights per paragraph) → CONTINUE
  - Unresolved tensions identified → CONTINUE

**The sauce**: Branch Exhaustion research revealed "Mined Out vs Dormant" distinction. A branch might seem empty because it needs a different approach, not because there's nothing there.

**Prompt additions:**
```
# For skeptic lens:
Before answering, consider: What's wrong with the obvious answer to this question?
What would a thoughtful critic say? Then provide your answer incorporating this critique.

# For analogist lens:
Where else in different domains does this pattern appear?
What can we learn from analogous situations? Then answer using these insights.

# For depth decision:
After answering, assess:
- Are there unexplored sub-angles worth pursuing? (If yes, list them)
- Or is this branch exhausted? (If yes, explain why: repetition, circularity, or diminishing returns)
```

---

### Phase 3: The Critic Pass (NEW)

**The biggest addition.** Before synthesis, dedicated adversarial review.

**Apply:**
- **Falsifiability test**: "What would prove this wrong?" If nothing could, flag as unfalsifiable
- **Simplification test**: Can each finding be stated in plain language? Collapses when simplified = verbal camouflage
- **Weak branch identification**: Which branches returned thin, vague, or circular content? Mark them
- **Contradiction surfacing**: Which branches disagree? Don't resolve — the tension is data
- **Evidence weighting**: Multiple independent sources vs single assertions

**Output**: Quality-annotated research tree. Each branch tagged: `[STRONG]` `[MODERATE]` `[WEAK]` `[CONTRADICTED]`

**The sauce**: Insight Validation research proved fluency ≠ truth. The Critic is the "friendly enemy" — identifies which findings are load-bearing vs decorative.

**Prompt:**
```
You are a research critic. Review these findings adversarially but fairly.

For each major finding:
1. FALSIFIABILITY: What would prove this wrong? If nothing could, mark [UNFALSIFIABLE]
2. SIMPLIFICATION: State it in one plain sentence. If it collapses, mark [CAMOUFLAGE]
3. EVIDENCE: Is this from multiple sources, single source, or assertion? Tag accordingly
4. STRENGTH: Rate as [STRONG] [MODERATE] [WEAK]

Then:
- List contradictions between branches (don't resolve, just surface)
- Identify the weakest 20% of branches that might be excluded or re-researched
- Note which findings are load-bearing for the overall answer vs decorative
```

---

### Phase 4: Cross-Branch Integration (NEW)

Before synthesizing within original frame, look for emergent patterns:

**Apply:**
- **Isomorphic translation**: Do branches from different domains show same underlying structure? Reveals deep principles
- **Tension mapping**: Where do branches create productive tensions? These are synthesis gold
- **Convergence detection**: Did independent branches arrive at same conclusion? Dramatically increases confidence
- **Gap identification**: Given all branches, what's conspicuously absent? What did NO branch address?

**The sauce**: v1 treats branches as independent answers to aggregate. v2 treats them as perspectives on shared reality, where RELATIONSHIPS between branches reveal as much as branches themselves.

**Prompt:**
```
Analyze connections across all research branches:

1. ISOMORPHIC PATTERNS: Do any branches from different domains show the same underlying structure or principle?

2. PRODUCTIVE TENSIONS: Which branches disagree in ways that could lead to deeper insight if reconciled?

3. CONVERGENCE: Did independent branches reach the same conclusion? List these high-confidence findings.

4. GAPS: What important aspect did NO branch address? What's conspicuously missing?

5. EMERGENT THEMES: What patterns emerge from viewing all branches together that weren't visible in any single branch?
```

---

### Phase 5: Synthesis with Uncertainty Quantification

Now synthesize, but with explicit confidence:

**Apply:**
- **Multi-pass synthesis**:
  1. First pass: Integrate findings straightforwardly
  2. Critic pass: Challenge the integration
  3. Revision pass: Incorporate challenges
- **Confidence tagging**:
  - `[HIGH]`: Multiple independent sources converge, survives critic, verifiable
  - `[MEDIUM]`: Single strong source, partial convergence, theoretical but unfalsifiable
  - `[LOW/SPECULATION]`: Single assertion, contradicted, or extrapolation beyond evidence
- **Tension preservation**: Don't force false resolution. If branches genuinely disagree, say so explicitly

**The sauce**: Synthesis Quality research identified "false coherence" failure mode — making things seem more resolved than they are. Uncertainty quantification is intellectual honesty.

**Prompt:**
```
Synthesize the research into a coherent answer.

PROCESS:
1. Create initial synthesis integrating key findings
2. Then critique your synthesis: What's it missing? Where is it overconfident?
3. Revise to address the critique

REQUIREMENTS:
- Tag each major claim with confidence: [HIGH] [MEDIUM] [LOW]
- Where branches disagree, preserve the tension: "Position A argues X, while Position B argues Y"
- Don't force false resolution — genuine disagreement is valuable information
- Distinguish between what the evidence shows vs what you're inferring

OUTPUT STRUCTURE:
## Core Answer
[The main synthesis]

## Confidence Map
- High confidence: [list]
- Medium confidence: [list]
- Low confidence/speculation: [list]

## Unresolved Tensions
[Genuine disagreements worth noting]
```

---

### Phase 6: Blind Spot Audit (NEW)

Final phase asks: **"What are we not seeing?"**

**Apply:**
- **Circular Detection Paradox awareness**: We can't see our own blind spots directly. So ask:
  - What perspectives were NOT represented?
  - What would a disagreer say we missed?
  - Where did we feel defensive during research? (Emotional signal mapping)
- **Expertise Curse check**: Did we assume background knowledge that isn't obvious?
- **Pre-mortem on synthesis**: "If this synthesis is completely wrong in 5 years, why?"
- **Generativity check**: Does synthesis OPEN new questions (good) or feel like closed answer (concerning)?

**The sauce**: Blind Spot Detection research proved external override is only reliable method. Simulate external perspective if you can't get real one.

**Prompt:**
```
Audit this synthesis for blind spots:

1. MISSING PERSPECTIVES: What viewpoints, disciplines, or stakeholder groups were not represented in this research?

2. DISAGREEMENT SIMULATION: If someone strongly disagreed with this synthesis, what would they say was missed or wrong?

3. EMOTIONAL SIGNALS: During the research, were there points of defensiveness, dismissal, or discomfort? These often point to blind spots.

4. EXPERTISE CURSE: Does this synthesis assume background knowledge that a smart outsider wouldn't have?

5. PRE-MORTEM: If this synthesis is proven completely wrong in 5 years, what's the most likely reason?

6. GENERATIVITY: Does this synthesis open new questions (healthy) or feel like a closed, final answer (concerning)?

List the top 3-5 blind spots or limitations that should accompany this research.
```

---

## Output Structure

The final deliverable should include:

```markdown
# [Question]

## Executive Summary
[Core answer in 2-3 paragraphs, readable standalone]

## Detailed Synthesis
[Full synthesis with inline confidence tags]

## Confidence Map
### High Confidence
- [Finding 1]
- [Finding 2]

### Medium Confidence
- [Finding 3]

### Low Confidence / Speculation
- [Finding 4]

## Key Tensions
[Unresolved disagreements worth preserving]

## Acknowledged Blind Spots
[What we know we might be missing]

## Generative Questions
[New questions this research opens]

## Methodology Note
[How this was researched — for reproducibility]
```

---

## Comparison: v1 vs v2

| Aspect | v1 | v2 |
|--------|----|----|
| Question quality | Assumed good | Explicitly tested (Phase 0) |
| Decomposition | Flat list | Relationship-mapped, MECE-checked |
| Exploration | Single perspective | Multi-lens, ensemble |
| Depth control | Fixed | Adaptive (signal-based) |
| Quality gate | None | Critic pass before synthesis |
| Cross-branch | Independent | Pattern detection, tension mapping |
| Synthesis | Single pass | Multi-pass with adversarial challenge |
| Confidence | Implicit | Explicit quantification |
| Blind spots | Ignored | Explicit audit phase |
| Output | Answer only | Answer + confidence + tensions + new questions |

---

## When to Use v2

**Use v2 when:**
- High-stakes decisions depend on the research
- Being wrong is costly
- Question is complex with multiple valid framings
- Domain has known blind spot risks
- You need to defend the conclusion to skeptics
- Output will inform policy, strategy, or significant investment

**Use v1 when:**
- Exploratory/brainstorming mode
- Speed matters more than completeness
- Initial scoping of a problem space
- Low-stakes questions
- Time/cost constraints

---

## Implementation Notes

**Complexity**: v2 adds ~3-4x the agent calls of v1 due to:
- Critic pass (separate agent)
- Cross-branch integration (separate agent)
- Blind spot audit (separate agent)
- Multi-pass synthesis

**Cost optimization**:
- Use opus for Phase 0, 3, 4, 6 (judgment-heavy)
- Use haiku/flash for Phase 2 leaves (volume)
- Consider skipping Phase 4 for simpler questions

**Parallelization opportunities**:
- Phase 2 (exploration) fully parallel
- Phase 3 (critic) can run per-branch in parallel
- Phases 0, 4, 5, 6 are sequential

---

## Research Sources

This recipe synthesizes insights from:

| Recipe Category | Key Contribution |
|-----------------|------------------|
| Decomposition Quality (Part IX) | MECE, relationship mapping |
| Recursive Thinking (Part X) | Adaptive depth, stack awareness |
| Prompt Engineering (Part XI) | Specificity-autonomy balance |
| Insight Validation (Part XII) | Falsifiability, simplification tests |
| Question Generativity (Part XIII) | Pre-mortem, assumption surfacing |
| Branch Exhaustion (Part XIV) | Adaptive depth signals |
| Multi-Perspective Synthesis (Part XV) | Ensemble, tension mapping |
| Blind Spot Detection (Part XVI) | Audit phase, external override |

---

## The One-Sentence Summary

**v2 = v1 + "trust but verify" at every junction.**

v1 trusts the exploration and synthesizes. v2 challenges the exploration, looks for what's missing, synthesizes with explicit uncertainty, then challenges the synthesis itself.
