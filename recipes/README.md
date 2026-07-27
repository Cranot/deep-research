# Deep Research Recipes

Implementation recipes for the deep-research tool.

## Recipes

| Recipe | Status | Philosophy | Metaphor |
|--------|--------|------------|----------|
| **Recursive Research** | v1 implemented, v2-v3 design | Extract answers | Mining |
| **The Emergence Engine** | Design only | Cultivate emergence through collision | Gardening |
| **The Inverse Engine** | Design only | Derive success from failure | Sculpture |
| **The Adversarial Engine** | Design only | Truth from combat | Courtroom |
| **The Socratic Engine** | Design only | Transform questions | Alchemy |

## Files

```
recipes/
├── README.md                                        # This file
├── recursive-research-v1.md                         # v1: Simple recursive
├── recursive-research-v1.sh                         # v1 script (reference)
├── recursive-research-v2-with-critic-and-audit.md   # v2: Validated recursive
├── recursive-research-v3-socratic-enhanced.md       # v3: Question-improving recursive
├── the-emergence-engine.md                          # Collision-based emergence
├── the-inverse-engine.md                            # Failure inversion
├── the-adversarial-engine.md                        # Combat-based truth testing
└── the-socratic-engine.md                           # Question transformation
```

## Quick Comparison

| Aspect | Recursive Research | Emergence | Inverse | Adversarial | Socratic |
|--------|-------------------|-----------|---------|-------------|----------|
| Core idea | Explore → Synthesize | Collide perspectives | Research failure | Combat to test | Improve questions |
| Input | Question | Question | Question | Proposition | Question |
| Output | Answer | Answer + Tensions | Answer (from failures) | Verdict + Dissent | Better Question |
| Unique strength | Speed | Depth | Concreteness | Stress-testing | Question quality |
| Cost | Low-Medium | High | Medium | Medium-High | Medium |
| Best for | Exploration | Paradigm questions | Practical decisions | Binary debates | Unclear questions |

## The Five Philosophies

### Recursive Research: Mining
> Dig for answers. Extract what's there. Aggregate findings.

**v1**: Simple — Explore, Spawn, Synthesize
**v2**: Validated — Add Critic, Connect, Audit phases
**v3**: Socratic — Improve questions at every level

### The Emergence Engine: Gardening
> Create conditions for insight to grow. Collide perspectives. Preserve tensions.

Multi-frame entry, collision phase, steelmanning, isomorphic hunt, negative space, temporal stack, outsider review.

### The Inverse Engine: Sculpture
> Carve away what's false. Research failure. Derive success from what remains.

Invert question → Research failure modes → Map failures → Invert to success factors → Validate.

### The Adversarial Engine: Courtroom
> Truth is what survives the strongest attack.

Proposition → Team Advocate vs Team Adversary → Cross-examination → Verdict + Dissent.

### The Socratic Engine: Alchemy
> Transform questions, not just answer them.

Excavate assumptions → Challenge → Find deeper question → Reconstruct → Answer emerges.

## Flows

### Recursive Research (v1/v2/v3)
```
v1: Question → Explore → Spawn → Synthesize → Answer

v2: Question → Prepare → Decompose → Explore → Critique → Connect → Synthesize → Audit → Answer

v3: Question → [SOCRATIC] → Prepare → Decompose [+assumptions] → Explore [+transform weak]
           → Critique → Connect → Synthesize → Audit → Answer
```

### The Emergence Engine
```
Question → Multi-Frame → Explore (parallel) → Collide → Steelman → Isomorphic Hunt
        → Negative Space → Temporal Stack → Synthesize → Outsider → Audit → Output
```

### The Inverse Engine
```
Question → Invert → Enumerate Failures → Deep Research → Failure Map
        → Inversion Transform → Validation → Completeness Audit → Synthesis
```

### The Adversarial Engine
```
Question → Proposition → Team Assignment → Case Building (parallel)
        → Opening Arguments → Cross-Examination → Rebuttal → Closing
        → Judge Verdict → Dissent → Final Ruling
```

### The Socratic Engine
```
Question → Assumption Excavation → Challenge Assumptions → Deeper Question
        → Recurse (until bedrock) → Bedrock Detection → Question Reconstruction
        → Answer Emergence → Output (Better Question + maybe Answer)
```

## When to Use Each

| Recipe | Best For |
|--------|----------|
| **Recursive Research v1** | Exploration, brainstorming, speed |
| **Recursive Research v2** | Important decisions, defending conclusions |
| **Recursive Research v3** | Uncertain questions, maximum rigor |
| **Emergence Engine** | Paradigm questions, novel territory, strategic decisions |
| **Inverse Engine** | Practical decisions, avoiding disaster, actionable output |
| **Adversarial Engine** | Binary debates, stress-testing positions, high stakes |
| **Socratic Engine** | Unclear questions, flawed questions, as first step |

## Recipe Selection Guide

```
START
  │
  ├─ Is the question clear and well-formed?
  │   ├─ NO → Use SOCRATIC ENGINE first
  │   └─ YES ↓
  │
  ├─ Can it be converted to a binary proposition?
  │   ├─ YES → Consider ADVERSARIAL ENGINE
  │   └─ NO ↓
  │
  ├─ Is failure more concrete than success?
  │   ├─ YES → Use INVERSE ENGINE
  │   └─ NO ↓
  │
  ├─ Is this a paradigm-level question?
  │   ├─ YES → Use EMERGENCE ENGINE
  │   └─ NO ↓
  │
  ├─ How important is validation?
  │   ├─ Critical → Use RECURSIVE RESEARCH v2/v3
  │   └─ Less critical → Use RECURSIVE RESEARCH v1
  │
  └─ END
```

## Combining Recipes

Recipes can be combined:

| Combination | When |
|-------------|------|
| Socratic → Any | Start with question improvement, then research |
| Inverse → Adversarial | Research failures, then debate the inversion |
| Emergence → Adversarial | Generate multiple positions, then have them fight |
| Any → Socratic | If stuck, improve the question and restart |

## Core Insights

**Recursive Research**: Every question contains hidden angles. Explore the full tree.

**Emergence Engine**: The best insights don't come from extraction. They emerge from collision.

**Inverse Engine**: Success is contextual and slippery. Failure is universal and concrete.

**Adversarial Engine**: A position that survives its strongest attack is a position you can trust.

**Socratic Engine**: The quality of answers is bounded by the quality of questions.
