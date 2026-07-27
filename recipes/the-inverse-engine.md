# The Inverse Engine (Via Negativa)

*Research failure to discover success. Map what's false to reveal what's true.*

**Status**: Design complete, implementation pending

---

## The Core Philosophy

> **"All I want to know is where I'm going to die, so I'll never go there."** — Charlie Munger

Other recipes ask "What's true?" directly. But success is contextual, slippery, hard to pin down.

**Failure is universal.** Failure modes repeat. Failure is concrete, observable, researchable.

**The Inverse Engine doesn't research the question. It researches the ANTI-question. Then inverts the findings.**

---

## Why Inversion Works

| Aspect | Researching Success | Researching Failure |
|--------|---------------------|---------------------|
| **Specificity** | Vague, contextual | Concrete, observable |
| **Universality** | Success patterns vary by context | Failure patterns repeat |
| **Verifiability** | Hard to prove what caused success | Easy to identify what caused failure |
| **Survivorship bias** | We only see winners | We can study losers |
| **Completeness** | Success has infinite forms | Failure modes are enumerable |

**The insight**: It's easier to map all the ways to fail than all the ways to succeed. Success is what's LEFT when you avoid all failure modes.

---

## Architecture: Mirror World

```
                    ┌─────────────────┐
                    │    QUESTION     │
                    │ "What makes X   │
                    │   succeed?"     │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │     INVERT      │
                    │ "What makes X   │
                    │    FAIL?"       │
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
    ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
    │ FAILURE MODE  │ │ FAILURE MODE  │ │ FAILURE MODE  │
    │     ALPHA     │ │     BETA      │ │    GAMMA      │
    └───────┬───────┘ └───────┬───────┘ └───────┬───────┘
            │                │                │
            ▼                ▼                ▼
    ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
    │   EXPLORE     │ │   EXPLORE     │ │   EXPLORE     │
    │   (deep)      │ │   (deep)      │ │   (deep)      │
    └───────┬───────┘ └───────┬───────┘ └───────┬───────┘
            │                │                │
            └────────────────┼────────────────┘
                             │
                    ┌────────▼────────┐
                    │  FAILURE MAP    │  ← Comprehensive failure taxonomy
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │    INVERSION    │  ← Flip each failure to success factor
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   VALIDATION    │  ← Do inversions match known successes?
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  COMPLETENESS   │  ← What failures did we miss?
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   SYNTHESIS     │  ← Answer = Avoid all failure modes
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │     OUTPUT      │
                    │ Success = ¬Failure │
                    └─────────────────┘
```

---

## Phase Details

### Phase 0: The Inversion

**Transform the question into its negative mirror.**

| Original Question | Inverted Question |
|-------------------|-------------------|
| What makes startups successful? | What makes startups fail? |
| How do I write well? | What makes writing bad? |
| What creates lasting relationships? | What destroys relationships? |
| What makes good decisions? | What leads to bad decisions? |

**Prompt:**
```
Transform this question into its inverse:

Original: [QUESTION]

Your inverted question should:
1. Focus on FAILURE, not success
2. Be equally specific as the original
3. Cover the same scope but from the negative perspective

Also identify:
- Why might the inverse be EASIER to research?
- What failure data exists that success data doesn't?
```

---

### Phase 1: Failure Mode Enumeration

**Map the taxonomy of failure.**

Don't just list failures — CATEGORIZE them:

| Category | Description | Examples |
|----------|-------------|----------|
| **Structural** | Built-in flaws | Bad architecture, wrong foundation |
| **Operational** | Execution failures | Poor implementation, resource misallocation |
| **Environmental** | External killers | Market shifts, competition, regulation |
| **Human** | People failures | Wrong team, bad leadership, misaligned incentives |
| **Temporal** | Timing failures | Too early, too late, wrong sequence |
| **Epistemic** | Knowledge failures | Wrong assumptions, missing information |

**Prompt:**
```
Enumerate all significant failure modes for: [INVERTED QUESTION]

For each failure mode:
1. Name it precisely
2. Categorize it (structural/operational/environmental/human/temporal/epistemic)
3. Describe HOW it causes failure
4. Rate its frequency (common/occasional/rare)
5. Rate its severity (fatal/serious/minor)

Be exhaustive. The goal is a complete taxonomy of ways this can fail.
```

---

### Phase 2: Deep Failure Research

**Each major failure mode gets full exploration.**

Use recursive mechanics but focused on ONE failure mode:
- What triggers this failure?
- What are the warning signs?
- What makes it worse?
- What famous examples exist?
- What patterns repeat?

**Critical**: Don't just describe failure. Understand its MECHANISM.

---

### Phase 3: The Failure Map

**Synthesize into a comprehensive failure taxonomy.**

Output structure:
```
FAILURE MAP: [Domain]

FATAL FAILURES (any one kills success):
├── F1: [failure mode] — [mechanism]
├── F2: [failure mode] — [mechanism]
└── F3: [failure mode] — [mechanism]

SERIOUS FAILURES (significantly harm success):
├── F4: [failure mode] — [mechanism]
└── F5: [failure mode] — [mechanism]

MINOR FAILURES (reduce success):
├── F6: [failure mode] — [mechanism]
└── F7: [failure mode] — [mechanism]

INTERACTION EFFECTS:
├── F1 + F4 → [compound failure]
└── F2 + F5 → [compound failure]
```

---

### Phase 4: The Inversion Transform

**Flip each failure mode to derive success factors.**

| Failure Mode | Inversion | Success Factor |
|--------------|-----------|----------------|
| Startups fail from running out of money | ¬ | Maintain sufficient runway |
| Relationships die from contempt | ¬ | Cultivate respect |
| Decisions fail from confirmation bias | ¬ | Actively seek disconfirming evidence |
| Writing fails from unclear structure | ¬ | Build clear logical architecture |

**The magic**: Each failure mode, when inverted, produces a CONCRETE, ACTIONABLE success factor.

**Prompt:**
```
For each failure mode in the failure map, derive the success factor by inversion:

FAILURE: [description]
INVERSION: What would be true if this failure were absent?
SUCCESS FACTOR: [concrete, actionable positive statement]
CONFIDENCE: How confident are we that avoiding this failure contributes to success?

Note any inversions that feel incomplete — where avoiding failure isn't sufficient for success.
```

---

### Phase 5: Validation Against Known Successes

**Do our derived success factors match reality?**

This is the crucial test:
1. List known successes in this domain
2. Check: did they avoid our enumerated failures?
3. Check: do they embody our derived success factors?
4. If not, WHY? What did we miss?

**Prompt:**
```
Validate the derived success factors against known successes:

SUCCESS FACTORS (derived from failure inversion):
[list]

KNOWN SUCCESSES TO CHECK:
[list of examples]

For each known success:
1. Did it avoid the enumerated failure modes?
2. Does it embody the derived success factors?
3. If mismatches exist, what does that reveal?

Identify:
- Factors that are VALIDATED (successes have them, failures don't)
- Factors that are QUESTIONABLE (some successes lack them)
- MISSING factors (successes have something we didn't derive)
```

---

### Phase 6: Completeness Audit

**What failures did we miss?**

Sources of missing failures:
- Survivorship bias (we don't see the quiet deaths)
- Category blindness (we didn't think to look there)
- Novel failures (new ways to fail we haven't seen yet)
- Compound failures (interactions we missed)

**Prompt:**
```
Audit the failure map for completeness:

1. SURVIVORSHIP BIAS: What failures might we miss because the victims are invisible?
2. CATEGORY BLINDNESS: What categories of failure might we have overlooked entirely?
3. NOVEL FAILURES: What new failure modes might emerge that don't exist yet?
4. COMPOUND FAILURES: What interactions between failure modes create emergent failures?
5. THE MISSING KNOWN: Are there famous failures that don't fit our taxonomy? What category are they?

For each gap found, add to the failure map and derive the corresponding success factor.
```

---

### Phase 7: Synthesis

**The answer emerges from the inverse.**

Structure:
```markdown
# [Original Question]

## The Via Negativa Answer

Success in [domain] is primarily about AVOIDING failure modes, not achieving positive factors.

The [N] critical failure modes to avoid:
1. [Failure] → Avoid by: [derived success factor]
2. [Failure] → Avoid by: [derived success factor]
...

## Confidence Map

HIGH CONFIDENCE (validated against known successes):
- [factor]
- [factor]

MEDIUM CONFIDENCE (logical but limited validation):
- [factor]

LOWER CONFIDENCE (derived but questionable):
- [factor]

## The Necessary Minimum

To succeed, you MUST avoid:
- [fatal failure 1]
- [fatal failure 2]
- [fatal failure 3]

## The Sufficient Maximum

Avoiding all enumerated failures is necessary. Is it sufficient?
[Analysis of whether failure avoidance is enough, or positive factors also required]

## What We Might Be Missing

[Completeness audit findings]
```

---

## Output Structure

```markdown
# [Question]

## The Inverse Insight

> [One sentence: what the failure research revealed]

## Failure Taxonomy

### Fatal Failures
[Table of failure modes that kill success]

### Serious Failures
[Table of failure modes that significantly harm]

### Minor Failures
[Table of failure modes with limited impact]

## Derived Success Factors

[Each failure inverted to success factor with confidence rating]

## Validation Results

[How well do derived factors match known successes?]

## The Via Negativa Answer

[Core synthesis: success = avoiding failure]

## Completeness Assessment

[What might we have missed?]

## Actionable Output

### Do:
[Positive actions derived from failure avoidance]

### Don't:
[The failure modes stated as warnings]

## Next Questions

[What the failure research opened up]
```

---

## Comparison With Other Recipes

| Aspect | Recursive Research | Emergence Engine | Inverse Engine |
|--------|-------------------|------------------|----------------|
| Philosophy | Extract | Emerge from collision | Derive from inversion |
| Metaphor | Mining | Gardening | Sculpture |
| Question handling | Direct | Multi-frame | Inversion |
| Research focus | Positive | Collision | Negative |
| Derives answer from | Aggregation | Emergence | Inversion of failures |
| Unique strength | Speed/simplicity | Depth/emergence | Concreteness/actionability |
| Best for | Exploration | Paradigm questions | Practical decisions |

---

## When to Use This Recipe

**Use The Inverse Engine when:**
- Success is vague but failure is concrete
- You need ACTIONABLE output (do/don't)
- Survivorship bias might be distorting direct research
- The question is about avoiding disaster, not achieving greatness
- Practical decisions where failure is costly
- You want a checklist of what NOT to do

**Use other recipes when:**
- Success has clear positive patterns
- You need deep understanding, not just avoidance rules
- The question is generative/creative (inversion may limit)
- Failure modes are genuinely unknown

---

## The Core Insight

> **Success is contextual and slippery. Failure is universal and concrete.**

By researching what makes things FAIL, we:
1. Get more concrete, verifiable data
2. Avoid survivorship bias
3. Discover universal patterns (failure modes repeat)
4. Derive actionable success factors through inversion
5. Validate by checking if successful examples avoided enumerated failures

**This recipe doesn't find success. It carves away failure until success is what remains.**

---

## Research Sources

This recipe draws from:

| Source | Contribution |
|--------|--------------|
| Charlie Munger | "Invert, always invert" |
| Nassim Taleb | Via Negativa (subtract to improve) |
| Pre-mortem technique | Research failure before it happens |
| Negative theology | Define by what something is NOT |
| Engineering failure analysis | FMEA (Failure Mode Effects Analysis) |

---

## Implementation Notes

**Complexity**: Medium
- Initial inversion (simple)
- Failure enumeration (can be parallelized)
- Deep failure research (parallel per failure mode)
- Inversion transform (simple)
- Validation (requires examples)

**Cost optimization:**
- Use haiku/flash for failure enumeration
- Use opus for inversion transform and validation
- Parallelize failure mode exploration

**Key challenges:**
- Good inversion requires understanding the domain
- Some questions don't invert cleanly
- Pure failure avoidance may miss positive factors (necessary but not sufficient)

---

**The one-sentence summary:**

> **The Inverse Engine researches why things FAIL, then derives success by inversion — because failure is universal, concrete, and researchable in ways success isn't.**
