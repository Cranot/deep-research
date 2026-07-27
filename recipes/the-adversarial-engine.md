# The Adversarial Engine (Trial by Combat)

*Truth is what survives the strongest attack. Structured combat between opposing positions.*

**Status**: Design complete, implementation pending

---

## The Core Philosophy

> **Truth emerges from combat, not exploration.**

All other recipes are exploratory — perspectives that merge or collide but aren't MOTIVATED to destroy each other.

In the Adversarial Engine, the opponent's entire job is to find every flaw in your position. This creates pressure that exploration can't match.

This is how real truth-finding works:
- **Courts**: Prosecution vs Defense
- **Science**: Author vs Peer Reviewers
- **Philosophy**: Thesis vs Antithesis → Synthesis
- **Democracy**: Opposing parties debate

---

## Why Adversarial Works

| Aspect | Exploratory Recipes | Adversarial Engine |
|--------|--------------------|--------------------|
| **Motivation** | Find truth | WIN the argument |
| **Flaw detection** | Incidental | Primary goal |
| **Weak points** | May be missed | Actively hunted |
| **Steel-manning** | Optional phase | Built into defense |
| **Minority views** | Often lost | Preserved as dissent |

**The insight**: When someone is trying to destroy your position, you're forced to make it stronger. When you're trying to destroy theirs, you find flaws they can't see.

---

## Architecture: The Arena

```
                    ┌─────────────────┐
                    │   PROPOSITION   │
                    │  (from question)│
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                              ▼
      ┌───────────────┐              ┌───────────────┐
      │    TEAM       │              │    TEAM       │
      │   ADVOCATE    │              │   ADVERSARY   │
      │  (prove it)   │              │  (disprove)   │
      └───────┬───────┘              └───────┬───────┘
              │                              │
              ▼                              ▼
      ┌───────────────┐              ┌───────────────┐
      │ CASE BUILDING │              │ CASE BUILDING │
      │  (parallel)   │              │  (parallel)   │
      └───────┬───────┘              └───────┬───────┘
              │                              │
              └──────────────┬───────────────┘
                             │
                    ┌────────▼────────┐
                    │    OPENING      │
                    │   ARGUMENTS     │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │     CROSS-      │
                    │  EXAMINATION    │  ← Each attacks the other
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │    REBUTTAL     │  ← Defense and counter
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │    CLOSING      │
                    │   ARGUMENTS     │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │     JUDGE       │  ← Independent evaluation
                    │    VERDICT      │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                              ▼
      ┌───────────────┐              ┌───────────────┐
      │   MAJORITY    │              │    DISSENT    │
      │   OPINION     │              │   (preserved) │
      └───────────────┘              └───────────────┘
                             │
                    ┌────────▼────────┐
                    │  FINAL RULING   │
                    │ (both included) │
                    └─────────────────┘
```

---

## Phase Details

### Phase 0: Proposition Formation

**Convert the question into a debatable claim.**

Questions can't be attacked/defended directly. Propositions can.

| Question | Proposition |
|----------|-------------|
| What makes startups successful? | "The primary determinant of startup success is founder-market fit" |
| Is remote work effective? | "Remote work produces equal or better outcomes than in-office work" |
| Should we use microservices? | "Microservices architecture is superior to monolith for our use case" |

**Requirements for good propositions:**
- Specific enough to attack/defend
- Not trivially true or false
- Has genuine support on both sides
- Consequential if wrong

**Prompt:**
```
Convert this question into a debatable proposition:

Question: [QUESTION]

Your proposition must:
1. Be a clear, specific claim (not a question)
2. Be attackable AND defensible
3. Have real stakes if wrong
4. Not be trivially true or false

Also identify:
- What's at stake if this proposition is wrong?
- Who would naturally advocate FOR this?
- Who would naturally advocate AGAINST this?
```

---

### Phase 1: Team Assignment

**Assign perspectives to each team.**

Each team gets 2-3 perspectives that would naturally support their side:

**Team Advocate** (prove the proposition):
- Perspectives with evidence/incentive to support
- Domain experts who believe this
- Those who benefit if true

**Team Adversary** (disprove the proposition):
- Perspectives with evidence/incentive to oppose
- Domain experts who disagree
- Those who lose if true
- Devil's advocates

**Prompt:**
```
Assign perspectives to each team:

PROPOSITION: [proposition]

TEAM ADVOCATE (will argue FOR):
Assign 2-3 perspectives that would genuinely support this proposition.
For each: name the perspective, explain why they'd support it, what evidence they'd use.

TEAM ADVERSARY (will argue AGAINST):
Assign 2-3 perspectives that would genuinely oppose this proposition.
For each: name the perspective, explain why they'd oppose it, what evidence they'd use.

Ensure both teams have strong, credible positions — not strawmen.
```

---

### Phase 2: Case Building (Parallel)

**Each team researches independently to build their strongest case.**

Teams work in parallel, unaware of each other's arguments. This prevents reactive positioning and forces independent strength.

**For each team:**
1. Research evidence supporting their position
2. Identify their strongest arguments
3. Anticipate likely counterarguments
4. Prepare responses to anticipated attacks
5. Find the "smoking gun" — their single most compelling point

**Prompt (Advocate):**
```
You are TEAM ADVOCATE. Build the strongest possible case FOR this proposition:

PROPOSITION: [proposition]
YOUR PERSPECTIVES: [assigned perspectives]

Research and construct:
1. CORE ARGUMENTS: Your 3-5 strongest arguments with evidence
2. SMOKING GUN: Your single most compelling point
3. ANTICIPATED ATTACKS: What will the opposition likely argue?
4. PREEMPTIVE DEFENSE: How will you counter those attacks?
5. BURDEN OF PROOF: What must you prove to win?

Build the strongest case possible. Your goal is to WIN.
```

**Prompt (Adversary):**
```
You are TEAM ADVERSARY. Build the strongest possible case AGAINST this proposition:

PROPOSITION: [proposition]
YOUR PERSPECTIVES: [assigned perspectives]

Research and construct:
1. CORE ARGUMENTS: Your 3-5 strongest arguments with evidence
2. SMOKING GUN: Your single most devastating point
3. ANTICIPATED DEFENSE: What will the advocates likely argue?
4. ATTACK VECTORS: How will you dismantle those arguments?
5. BURDEN OF PROOF: What must you prove to win?

Build the strongest case possible. Your goal is to WIN.
```

---

### Phase 3: Opening Arguments

**Each team presents their case.**

No interaction yet — just presentation of strongest arguments.

**Structure:**
```
TEAM ADVOCATE OPENING:
1. Statement of position
2. Preview of key arguments
3. Presentation of evidence
4. The smoking gun
5. Why this matters

TEAM ADVERSARY OPENING:
1. Statement of position
2. Preview of key arguments
3. Presentation of evidence
4. The smoking gun
5. Why this matters
```

---

### Phase 4: Cross-Examination

**The magic phase. Each team attacks the other's weakest points.**

This is where truth emerges. Each side:
1. Identifies the weakest points in opponent's case
2. Attacks with evidence and logic
3. Forces opponent to defend or concede

**Prompt (Advocate cross-examines Adversary):**
```
You are TEAM ADVOCATE. Cross-examine TEAM ADVERSARY's case.

THEIR ARGUMENTS: [adversary's opening]

For each of their arguments:
1. Identify the WEAKEST POINT
2. ATTACK it with evidence, logic, or counterexample
3. Ask pointed questions that expose flaws
4. Highlight contradictions or unsupported claims

Be aggressive but fair. Your goal is to dismantle their case.
```

**Prompt (Adversary cross-examines Advocate):**
```
You are TEAM ADVERSARY. Cross-examine TEAM ADVOCATE's case.

THEIR ARGUMENTS: [advocate's opening]

For each of their arguments:
1. Identify the WEAKEST POINT
2. ATTACK it with evidence, logic, or counterexample
3. Ask pointed questions that expose flaws
4. Highlight contradictions or unsupported claims

Be aggressive but fair. Your goal is to dismantle their case.
```

---

### Phase 5: Rebuttal

**Each team defends against attacks and counter-attacks.**

**Prompt:**
```
You are [TEAM]. Respond to the cross-examination.

ATTACKS ON YOUR CASE: [cross-examination results]

For each attack:
1. CONCEDE if the point is valid (intellectual honesty)
2. DEFEND if you can counter the attack
3. COUNTER-ATTACK if their attack reveals a weakness in THEIR position

Update your case strength assessment. What survives? What's weakened?
```

---

### Phase 6: Closing Arguments

**Final synthesis of each position.**

Each team:
1. Summarizes what survived the exchange
2. Acknowledges what they conceded
3. Explains why their remaining case is sufficient
4. Makes final appeal

---

### Phase 7: The Verdict

**Independent judge evaluates both cases.**

The judge has seen everything but participated in neither team.

**Prompt:**
```
You are an INDEPENDENT JUDGE. Render a verdict.

PROPOSITION: [proposition]

ADVOCATE'S CASE: [final position]
ADVERSARY'S CASE: [final position]

Evaluate:
1. Which side had stronger evidence?
2. Which side had better logic?
3. Which side made more concessions?
4. Which side's "smoking gun" was more compelling?
5. What were the decisive factors?

VERDICT: [FOR/AGAINST/PARTIAL] the proposition

REASONING: [detailed explanation]

CONFIDENCE: [how confident in this verdict]
```

---

### Phase 8: The Dissent

**CRUCIAL: The losing side writes a formal dissent.**

This preserves the minority view that might be vindicated later.

**Prompt:**
```
You lost the verdict. Write a formal DISSENT.

VERDICT AGAINST YOU: [verdict and reasoning]

Your dissent must:
1. Acknowledge what the verdict got right
2. Explain what the verdict MISSED or got wrong
3. Identify conditions under which you'd be vindicated
4. Preserve the strongest version of your argument for the record

This dissent will be preserved alongside the majority opinion.
```

---

### Phase 9: Final Ruling

**Synthesize majority opinion AND dissent into final output.**

The ruling includes BOTH views because:
- The minority might be right
- Future evidence might change things
- Nuance matters

---

## Output Structure

```markdown
# [Proposition]

## Verdict: [FOR / AGAINST / PARTIAL]

**Confidence**: [High/Medium/Low]

## The Case

### Winning Arguments
[What decided the verdict]

### Key Evidence
[Most compelling evidence on winning side]

### What the Losing Side Got Right
[Acknowledged strengths of the opposition]

## Majority Opinion
[Full reasoning for the verdict]

## Dissent
[The losing side's preserved objection]

## Conditions for Reversal
[What new evidence or arguments would overturn this verdict]

## Open Questions
[What remains unresolved]
```

---

## When to Use This Recipe

**Use The Adversarial Engine when:**
- Question can be converted to binary/near-binary proposition
- High stakes — being wrong is costly
- You need to stress-test a position before committing
- Conventional wisdom might be wrong
- You want to understand BOTH sides deeply
- Decision requires defending to skeptics

**Don't use when:**
- Question is genuinely open-ended (many valid answers)
- You need exploration, not judgment
- The question isn't mature enough for debate
- You need speed over rigor

---

## Comparison With Other Recipes

| Aspect | Other Recipes | Adversarial Engine |
|--------|--------------|-------------------|
| Structure | Pipeline/tree/network | Arena/combat |
| Perspectives | Collaborate/merge | Fight to win |
| Goal | Find truth | Test truth under attack |
| Output | Answer | Verdict + dissent |
| Minority view | Often lost | Formally preserved |
| Validation | Quality gates | Survives strongest attack |

---

## The Core Insight

> **A position that survives its strongest attack is a position you can trust.**

Other recipes find answers. The Adversarial Engine TESTS answers. Use it when you need to know if your conclusion can withstand assault.

---

## Implementation Notes

**Complexity**: Medium-high
- Parallel case building (2 teams)
- Multiple exchange rounds
- Independent judge
- Dissent writing

**Cost optimization:**
- Use opus for judge (requires judgment)
- Use sonnet/haiku for team arguments (can parallelize)
- Cross-examination can be parallelized

**Key challenges:**
- Proposition must be well-formed
- Teams must be genuinely strong (not strawmen)
- Judge must be truly independent (separate context)

---

**The one-sentence summary:**

> **The Adversarial Engine stress-tests positions through structured combat — because truth that survives attack is truth you can trust.**
