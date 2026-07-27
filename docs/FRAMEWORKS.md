# Research Frameworks Reference

*These frameworks were derived from deep research runs and inform how the tool works.*

---

## Synthesis Quality Framework

*Derived from "What techniques improve AI research synthesis quality?" research*

### Five Quality Dimensions

| Dimension | Definition | Key Question |
|-----------|------------|--------------|
| **Accuracy** | Correct representation of findings | Is it true? |
| **Comprehensiveness** | Coverage of all relevant aspects | Is anything missing? |
| **Coherence** | Logical consistency and flow | Does it hang together? |
| **Actionability** | Practical utility | What do I do with this? |
| **Novelty Detection** | Identifies emerging trends | What's new here? |

**Context-sensitive weighting**: Clinical decisions prioritize accuracy → actionability. Research agendas prioritize novelty → comprehensiveness. Executive summaries prioritize actionability → coherence.

### NLP Extraction Pipeline

The foundation for structured synthesis:

```
Named Entity Recognition (NER)
    ↓ Identifies: who, what, where
Relation Extraction (RE)
    ↓ Establishes: how entities connect
Argument Mining (AM)
    ↓ Extracts: claims, premises, conclusions
```

Each layer builds on the previous. Errors propagate - NER mistakes cascade into flawed relations.

### Multi-Agent Architecture

The optimal synthesis pipeline:

```
Researcher Agent → Gathers diverse information
        ↓
Critic Agent → Evaluates, identifies errors, challenges claims
        ↓
Synthesizer Agent → Integrates into coherent output
        ↓
[Iteration Loop if quality insufficient]
```

**Key insight**: Current deep-research uses Researcher → Synthesizer. Adding a **Critic** role between them catches errors before synthesis.

### Five Tensions in Research Synthesis

Every synthesis navigates these tradeoffs:

| Tension | Challenge | Resolution |
|---------|-----------|------------|
| **Automation vs Human Judgment** | AI scales; humans understand context | Hybrid systems, strategic human checkpoints |
| **Comprehensiveness vs Signal-to-Noise** | More sources = more coverage but dilution | Quality weighting, relevance ranking |
| **Recency vs Foundation** | New findings may contradict established knowledge | Evaluate evidence strength regardless of date |
| **Transparency vs Usability** | Full provenance = complexity | Layered presentation with drill-down |
| **Standardization vs Flexibility** | Schemas enable integration but miss novelty | Extensible frameworks |

### What Pure Automation Misses

The research consistently found: **pure automation is insufficient** for high-quality synthesis.

Human roles that AI cannot replace:
- Contextual judgment for ambiguous cases
- Bias detection requiring cultural awareness
- Ethical oversight and appropriate use
- Domain expertise for subtle errors
- Reformulation when question is ill-posed

**The pattern**: AI handles bulk processing and flags uncertain cases → humans focus on high-value judgment tasks.

### Best Practices Checklist

Based on integrated research findings, high-quality AI research synthesis should incorporate:

**Technical Infrastructure:**
- [ ] Multi-source ingestion (formal literature, code repos, grey literature)
- [ ] Layered NLP extraction (NER → RE → Argument Mining) with error handling
- [ ] Knowledge graph construction using domain ontologies
- [ ] RAG architectures grounding generation in retrieved evidence
- [ ] Long-context models combined with semantic chunking

**Methodological Rigor:**
- [ ] Adapted systematic review protocols (PRISMA-trAIce) with transparent AI disclosure
- [ ] Evidence weighting by methodology, sample size, source credibility
- [ ] Bias detection (publication bias, citation bias, hype cycles)
- [ ] Uncertainty quantification with calibrated confidence estimates
- [ ] Reproducibility requirements with comprehensive documentation

**Human-AI Collaboration:**
- [ ] Strategic human-in-the-loop for ambiguity, bias detection, quality assurance
- [ ] Domain expert auditing with feedback loops for continuous improvement
- [ ] Interactive refinement allowing iterative improvement of queries and outputs

**Quality Assurance:**
- [ ] Multi-dimensional evaluation (accuracy, comprehensiveness, coherence, actionability, novelty)
- [ ] Hybrid assessment combining automated metrics with expert evaluation
- [ ] Provenance tracking enabling verification and contestability
- [ ] Continuous updating with automated validation gates

**The key insight**: Quality emerges from process integrity—not just sophisticated algorithms, but rigorous methodology, appropriate human oversight, and transparent accountability.

---

## Recursive Thinking Framework

*Derived from "What is deep recursive thinking and why is it useful?" research*

### The Three Pillars

Every recursive process—whether computational or cognitive—has three elements:

| Element | Definition | Human Constraint |
|---------|------------|------------------|
| **Base Case** | Simplest solvable version | Must be recognizable |
| **Recursive Step** | How to reduce to simpler version | Must preserve problem structure |
| **Stack Depth** | Nested levels held simultaneously | ~3-5 (working memory limit) |

### Why Recursion Suits Complex Questions

| Characteristic | Why Linear Methods Fail | How Recursion Helps |
|----------------|------------------------|---------------------|
| **Interdependency** | Isolated analysis insufficient | Traces connections across levels |
| **Non-linearity** | Proportional relationships don't hold | Captures feedback loops |
| **Emergence** | Whole exceeds sum of parts | Synthesis phase allows emergence |
| **Multi-scale** | Problems manifest across scales | Hierarchical decomposition |
| **Uncertainty** | Incomplete data | Iterative refinement |

### The Fundamental Trade-off

> "The depth of recursive analysis is gated by the limits of working memory."

**Depth → Accuracy but → Cognitive Load**

The brain's call stack is ~4 levels deep. Computers handle thousands. This is why:
- **Trust the recursion**: Don't trace all paths mentally; trust sub-problems solve correctly
- **Externalize aggressively**: Notes, diagrams, intermediate summaries
- **Know when to stop**: Base case must be recognizable

### When Recursion Becomes Counterproductive

| Warning Sign | Symptom | Resolution |
|--------------|---------|------------|
| **Analysis Paralysis** | No clear base case → infinite regress | Define "good enough" |
| **Over-Abstraction** | Lost in meta-levels | Reconnect to concrete problem |
| **Simple Problem Overkill** | Recursion where iteration suffices | Use simpler method |
| **Cognitive Overflow** | "Where was I?" moments | Externalize, limit depth |

### The Deep Research Connection

Deep Research IS recursion applied to understanding:
- **Question** = Problem to solve
- **Sub-questions** = Recursive decomposition
- **Leaf answers** = Base cases
- **Synthesis** = Combining sub-solutions

The "expand or answer" rule at each node is exactly the recursive step: keep decomposing until base case (atomic question), then combine results upward.

---

## Prompt Engineering Framework

*Derived from "What makes good prompts for AI research agents?" research (50 findings)*

### The Specificity-Autonomy Spectrum

Every prompt sits somewhere on this spectrum:

```
HIGH SPECIFICITY ←————————————→ HIGH AUTONOMY
├─ Critical tasks           ├─ Exploratory research
├─ Clear success criteria   ├─ Advanced agents
├─ Simpler models          ├─ Creative problems
└─ Enforced workflows      └─ Large dynamic toolsets
```

**Calibration questions:**
1. What's the cost of errors? (High → more specific)
2. Is the problem well-defined? (Yes → more specific)
3. How capable is the agent? (High → more autonomy)
4. Is innovation needed? (Yes → more autonomy)

### Effectiveness Hierarchy

```
1. GOAL STATEMENTS (most effective)
   "Generate a 500-word analysis of..."

2. COMMANDS (highly effective)
   "Summarize the following in three bullet points..."

3. QUESTIONS (effective when combined)
   "What are the key factors affecting...?"
```

**Best practice**: Combine elements—goal for direction, commands for structure, questions for specifics.

### Key Prompt Patterns

| Pattern | When to Use | Effect |
|---------|-------------|--------|
| **Layered Prompting** | Complex tasks | Start high-level, add constraints progressively |
| **Few-Shot Examples** | Format/style matters | Show 1-3 input→output pairs |
| **Negative Examples** | Common pitfalls exist | Show what NOT to do |
| **Success Criteria Embedding** | Quality critical | Build self-evaluation into prompt |
| **Uncertainty Protocol** | Ambiguous inputs | Define how to handle unknowns |
| **Source Weighting** | Multiple sources | Specify hierarchy when conflicts arise |

### Handling Uncertainty

```
1. ACKNOWLEDGE: "If uncertain, state your uncertainty and why"
2. CLARIFY: "If gaps exist, specify what information is needed"
3. ASSUME EXPLICITLY: "If proceeding requires assumptions, list them"
4. IDENTIFY CONFLICTS: "Highlight discrepancies between sources"
5. PROPOSE ALTERNATIVES: "Present multiple interpretations when data allows"
```

### The Prompt Quality Checklist

**Foundation:**
- [ ] Clear goal statement (not just questions)
- [ ] Appropriate length (comprehensive but not overwhelming)
- [ ] Well-structured format
- [ ] Explicit scope boundaries

**Context & Constraints:**
- [ ] Necessary domain context provided
- [ ] Temporal context specified (current vs historical)
- [ ] Resource constraints stated

**Guidance:**
- [ ] Research strategy indicated (depth vs breadth)
- [ ] Source weighting if relevant
- [ ] Uncertainty handling instructions

**Output Quality:**
- [ ] Success criteria embedded
- [ ] Output format precisely specified
- [ ] Examples provided (positive and/or negative)
- [ ] Confidence requirements stated

---

## Insight Validation Framework

*Derived from "What distinguishes genuine insight from sophisticated-sounding nonsense?" research (Dec 2025)*

### The Core Insight

> **Genuine insight earns its profundity through specificity, testability, predictive power, and the ability to be decomposed, applied, and communicated. Pseudo-profundity borrows the *appearance* of these properties through complexity, jargon, abstraction, and ambiguity—but collapses under scrutiny.**

### The Seven Detection Tests

| Test | Core Question | Red Flag |
|------|---------------|----------|
| **Falsifiability** | What would prove this false? | Nothing could |
| **Prediction** | What does this let me predict? | No predictions = no content |
| **Decomposition** | Can this break into verifiable parts? | Resists breakdown |
| **"So What?"** | What are the concrete implications? | Unable to specify |
| **Simplification** | Can this be stated simply? | Collapses when tried |
| **Steelmanning** | Does it survive strongest criticism? | Falls to obvious objections |
| **Specificity** | Is this precise enough to be wrong? | Strategically vague |

### Insight vs Nonsense (Quick Reference)

| Dimension | Genuine Insight | Sophisticated Nonsense |
|-----------|-----------------|------------------------|
| **Testability** | Falsifiable, makes predictions | Unfalsifiable, immune to evidence |
| **Specificity** | Concrete, precise claims | Vague, strategically ambiguous |
| **Decomposition** | Breaks into verifiable sub-claims | Resists analysis, holistic hand-waving |
| **Generativity** | Opens new questions | Self-contained, circular |
| **Simplification** | Survives distillation | Collapses under scrutiny |
| **Applicability** | Leads to concrete actions | No clear implications |

### The Psychology of Being Fooled

| Bias | Mechanism | Exploitation |
|------|-----------|--------------|
| **Complexity Bias** | Difficult = profound | Obscure language signals depth |
| **Authority Bias** | Experts must be right | Credentials override content |
| **Effort Justification** | Hard work = valuable result | Struggle to parse = must be worth it |
| **Apophenia** | Pattern-seeking finds meaning everywhere | Elaborate but spurious frameworks |
| **Barnum Effect** | Vague = personally meaningful | Horoscope-style universality |
| **Fluency Heuristic** | Easy processing = true | Smooth delivery overrides substance |

### Practical Wisdom

1. **Demand predictions**: What does this let me anticipate?
2. **Seek specificity**: Vagueness is a hiding place for emptiness
3. **Test decomposition**: Can this be broken into verifiable parts?
4. **Apply "so what?"**: What concrete difference does this make?
5. **Beware effort justification**: Difficulty understanding ≠ profundity
6. **Check context-dependence**: Does this hold in the specific situation?
7. **Maintain epistemic humility**: Today's nonsense might be tomorrow's breakthrough

---

## Question Generativity Framework

*Derived from "What makes some questions more generative than others?" research (Dec 2025)*

### Anatomy of Generative Questions

| Feature | Dead-End Questions | Generative Questions |
|---------|-------------------|---------------------|
| **Scope** | Narrow, constrained | Bounded but flexible |
| **Abstraction** | Too concrete or too abstract | Intermediate "sweet spot" |
| **Ambiguity** | None or accidental | Productive, intentional |
| **Cognitive Load** | Too easy or overwhelming | Within Zone of Proximal Development |
| **Structure Focus** | Surface symptoms | Deep patterns |
| **Assumptions** | Embedded invisibly | Surfaced explicitly |

### The Eight Generativity Patterns

| Pattern | Core Idea |
|---------|-----------|
| **Goldilocks Abstraction** | Find intermediate level—specific enough to be tractable, abstract enough to explore |
| **Productive Ambiguity** | Deliberate openness that stimulates creativity, not confusion |
| **ZPD Calibration** | Match question difficulty to questioner's development zone |
| **Deep Structure Probe** | Reveal underlying patterns, not just surface symptoms |
| **Assumption Exposure** | Surface unstated premises governing current thinking |
| **Contingency Revelation** | Show current realities as choices, not inevitabilities |
| **Cognitive Process Activation** | Design questions to activate specific thinking processes |
| **Exploration-Exploitation Balance** | Know when to use generative vs precise questions |

### Linguistic Markers

**Generative Framings:**
- "How might we..." - Opens possibility space
- "What would happen if..." - Activates counterfactual thinking
- "Why does..." - Probes causality
- "What's the relationship between..." - Seeks connections

**Dead-End Framings:**
- "What is the..." - Seeks single answer
- "When did..." - Factual recall only
- "Is it true that..." - Yes/no constraint

---

## Branch Exhaustion Framework

*Derived from "What signals indicate a research branch is exhausted versus worth exploring deeper?" research (Dec 2025)*

### Mined Out vs Dormant

| State | Definition | Signal | Response |
|-------|------------|--------|----------|
| **Mined Out** | Complete investigation; fundamental limits reached | Can explain *why* approach cannot work | Abandon with documented learnings |
| **Dormant** | Paused due to situational constraints | Blocked by tools, not understanding | Shelve with explicit revival criteria |

Many branches that appear exhausted are actually dormant—waiting for new methods, interdisciplinary connections, or paradigm shifts.

### The Four Exhaustion Mechanisms

| Type | Signal | Response |
|------|--------|----------|
| **Diminishing Returns** | Each insight requires exponentially more effort | Accept plateau or invest heavily |
| **Saturation** | ≤5% new information from additional work | Declare sufficiency, move to synthesis |
| **Paradigm Limits** | Anomalies accumulating that framework can't accommodate | Seek paradigm shift |
| **Methodological** | Hit limits of what current tools can measure | Wait for or develop new tools |

**Key insight**: Type 3 (Paradigm Limits) is most dangerous to misdiagnose—it *looks* like exhaustion but signals the branch is rich; you just need a different framework.

### Depth Indicators (Signs Work Remains)

- **Unresolved contradictions** — Findings that don't fit together
- **Unexplained anomalies** — Observations outside theoretical expectations
- **Competing frameworks** — Multiple legitimate paradigms coexisting
- **Contextual sensitivity** — Findings vary significantly by context
- **Recurrent reformulation** — Same problem revisited by successive generations

### Error Asymmetry

| Error | Cost |
|-------|------|
| **Abandon rich branch** (False Negative) | Unbounded—lose option value permanently, never know what was missed |
| **Continue exhausted branch** (False Positive) | Bounded—can always cut losses later |

**Decision Rule**: Set *higher* thresholds for abandonment evidence. When uncertain, reduce investment rather than exit.

---

## Multi-Perspective Synthesis Framework

*Derived from "What makes multi-perspective synthesis stronger than single-perspective?" research (Dec 2025)*

### The Inverted-U Principle

Perspective diversity follows a curvilinear relationship with performance:

| Zone | Effect |
|------|--------|
| **Too Little** | Blind spots, groupthink, shared assumptions unchallenged |
| **Optimal** | Assumptions challenged, errors caught, novel solutions emerge |
| **Too Much** | Coordination collapse, incoherence, decision paralysis |

The goal isn't maximum diversity—it's *matched* diversity for the task.

### The Five Value-Creation Mechanisms

| Mechanism | How It Works |
|-----------|--------------|
| **Bias Cancellation** | Uncorrelated errors cancel out |
| **Assumption Challenging** | What one takes as given, another questions |
| **Schema Restructuring** | Reorganizing knowledge, not just adding to it |
| **Solution Space Expansion** | Revealing possibilities you'd never consider |
| **Observer-Dependence Detection** | Convergence across independent observers → objectivity |

If none of these mechanisms operate, you're aggregating opinions, not generating insight.

### The Seven Failure Modes

| Mode | Symptom | Fix |
|------|---------|-----|
| Cognitive Overload | Decision paralysis | Reduce perspectives or stage integration |
| Wrong Reasoning Wins | Output worse than single best | Evaluate reasoning quality, not confidence |
| Bias Amplification | Dominated by loudest voice | Structure the process; weight by evidence |
| Abstraction Mismatch | Talking past each other | Explicitly bridge levels |
| False Balance | All views treated as equal | Weight by evidence and reasoning |
| Perspective Paralysis | Never finishing | Set decision criteria in advance |
| Averaging Away Signal | Middle ground no one holds | Preserve disagreement structure |

### The Independence Requirement

> "The most dangerous situation is when triangulation appears most successful—when multiple perspectives beautifully converge. This is precisely when shared blind spots are hardest to detect."

True confidence comes from convergence *despite structural incentives to diverge*.

---

## Blind Spot Detection Framework

*Derived from "How do experts identify blind spots in their own reasoning?" research (Dec 2025)*

### The Core Paradox

> "The cognitive systems that create blind spots are the same systems we must use to detect them. You cannot use biased reasoning to identify bias in that reasoning—it's logically circular."

This explains why individual reflection alone is fundamentally insufficient.

### What Actually Works

| Level | Technique | Why It Works |
|-------|-----------|--------------|
| **Individual** | Emotional signals as data | Defensiveness = flare marking blind spot |
| **Individual** | Pre-mortem analysis | Bypasses optimism bias by assuming failure |
| **Individual** | Rumsfeld Matrix | Distinguishes known unknowns from unknown unknowns |
| **Interpersonal** | Genuine disagreement | Different frameworks surface invisible assumptions |
| **Interpersonal** | Intellectual sparring partners | True conviction challenges, not role-played |
| **Structural** | System-level design | Assumes blind spots will occur; builds around them |

### The Expertise Paradox

The training that creates expertise also creates blind spots:

| Curse | Mechanism | Counter |
|-------|-----------|---------|
| Automatization | Knowledge becomes implicit | Explain to novices |
| Paradigm lock-in | Training defines valid questions | Cross-field engagement |
| Success confirmation | Past success → confidence | List what would falsify |
| Status protection | Expertise tied to identity | Separate ego from ideas |

### The Goal: Navigation, Not Elimination

> "Blind spots are structural features of being a situated knower. The goal isn't elimination but developing wisdom about navigating with them."

Build systems, relationships, and habits that surface what individual reflection cannot see.
