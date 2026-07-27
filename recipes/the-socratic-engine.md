# The Socratic Engine (Question Alchemy)

*Transform questions, not just answer them. The quality of answers is bounded by the quality of questions.*

**Status**: Design complete, implementation pending

---

## The Core Philosophy

> **Most research fails not from bad answers, but from bad questions.**

All other recipes take the question as given and find answers. But what if the question itself is flawed? No amount of brilliant research can produce a good answer to a bad question.

The Socratic Engine doesn't answer questions. It IMPROVES them. Often, the right question makes the answer obvious.

---

## Why Question Quality Matters

| Question Quality | Research Outcome |
|------------------|------------------|
| Bad question | Best case: good answer to wrong question |
| Mediocre question | Partial insight, missing the core |
| Good question | Clear path to useful answer |
| Great question | Answer often becomes obvious |

**The insight**: Time spent improving the question often saves more time than it costs. A 10x better question can make research 10x easier.

---

## What Makes Questions Bad?

| Problem | Example | What's Wrong |
|---------|---------|--------------|
| **Hidden assumptions** | "How do I become successful?" | Assumes success is defined, achievable, desirable |
| **False dichotomy** | "Should we use React or Vue?" | Assumes only two options |
| **Loaded framing** | "Why is X so terrible?" | Presupposes conclusion |
| **Wrong level** | "What color should the button be?" | Surface question hiding deeper issue |
| **Vague terms** | "How do I be happy?" | Key term undefined |
| **Wrong question entirely** | "How do I get more done?" | When real question is "what should I stop doing?" |

---

## Architecture: The Descent

```
                    ┌─────────────────┐
                    │ SURFACE QUESTION│
                    │   (as given)    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   ASSUMPTION    │
                    │   EXCAVATION    │  ← What does this assume?
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
    ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
    │  ASSUMPTION   │ │  ASSUMPTION   │ │  ASSUMPTION   │
    │      A        │ │      B        │ │      C        │
    └───────┬───────┘ └───────┬───────┘ └───────┬───────┘
            │                │                │
            ▼                ▼                ▼
    ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
    │   CHALLENGE   │ │   CHALLENGE   │ │   CHALLENGE   │
    │  ASSUMPTION   │ │  ASSUMPTION   │ │  ASSUMPTION   │
    └───────┬───────┘ └───────┬───────┘ └───────┬───────┘
            │                │                │
            └────────────────┼────────────────┘
                             │
                    ┌────────▼────────┐
                    │    DEEPER       │
                    │   QUESTION      │  ← What lies beneath?
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │    RECURSE      │  ← Repeat until bedrock
                    │   (if needed)   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │    BEDROCK      │  ← Foundational level
                    │   DETECTION     │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │    QUESTION     │
                    │ RECONSTRUCTION  │  ← Build better question
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │     ANSWER      │
                    │   EMERGENCE     │  ← Often now obvious
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │     OUTPUT      │
                    │ Better Question │
                    │  + Answer (?)   │
                    └─────────────────┘
```

---

## Phase Details

### Phase 1: Assumption Excavation

**Surface the hidden assumptions in the question.**

Every question contains assumptions. Most are invisible to the asker.

**Prompt:**
```
Excavate the hidden assumptions in this question:

QUESTION: [question]

List ALL assumptions this question makes:
1. What does it assume EXISTS?
2. What does it assume is TRUE?
3. What does it assume is DESIRABLE?
4. What does it assume is POSSIBLE?
5. What TERMS does it leave undefined?
6. What OPTIONS does it exclude?
7. What FRAMING does it impose?

Be thorough. The most dangerous assumptions are the ones that seem obvious.
```

**Example:**
```
Question: "How do I become more productive?"

Assumptions:
1. Productivity is measurable
2. More productivity is desirable
3. The questioner isn't already optimally productive
4. Productivity is within the questioner's control
5. "Productive" means the same thing to everyone
6. Productivity is the right goal (vs effectiveness, fulfillment, etc.)
7. Individual productivity matters (vs systemic factors)
```

---

### Phase 2: Assumption Challenging

**Challenge each assumption with Socratic questions.**

Not all assumptions are wrong. But all should be examined.

**For each assumption, ask:**

| Challenge | Purpose |
|-----------|---------|
| Is this necessarily true? | Test validity |
| Under what conditions would this be false? | Find boundaries |
| Who benefits from this assumption? | Detect bias |
| What if the opposite were true? | Inversion test |
| Why do we assume this? | Trace origin |
| What evidence supports this? | Ground in reality |

**Prompt:**
```
Challenge each assumption:

ASSUMPTION: [assumption]

1. IS THIS TRUE? What evidence supports or contradicts it?
2. WHEN IS IT FALSE? Under what conditions does this assumption break?
3. WHO BENEFITS? Who gains from this assumption being accepted?
4. WHAT IF OPPOSITE? What would it mean if the opposite were true?
5. WHY ASSUMED? Where does this assumption come from?

Rate each assumption:
- SOLID: Well-grounded, keep it
- QUESTIONABLE: Might be wrong, examine further
- FLAWED: Likely wrong, remove or replace
```

---

### Phase 3: The Deeper Question

**Find the question beneath the question.**

Surface questions often hide deeper ones:

| Surface Question | Deeper Question | Even Deeper |
|------------------|-----------------|-------------|
| How do I become successful? | What do I actually want? | What would make life meaningful? |
| Should we use React or Vue? | What are our actual requirements? | What problem are we solving? |
| How do I get more done? | What should I stop doing? | What actually matters? |

**Prompt:**
```
Find the deeper question beneath this one:

SURFACE QUESTION: [question]
CHALLENGED ASSUMPTIONS: [from phase 2]

Given the questionable assumptions, what DEEPER question lies beneath?

Ask:
1. WHY is this question being asked? What's the real concern?
2. WHAT WOULD CHANGE if we knew the answer? What decision does this enable?
3. WHAT'S BENEATH? If we removed the flawed assumptions, what question remains?

The deeper question is often more useful than the surface question.
```

---

### Phase 4: Recursive Descent

**Keep going deeper until you hit bedrock.**

Apply phases 1-3 to the deeper question. Then again. Continue until:
- You hit definitional questions (what IS X?)
- You hit empirical questions (can we measure X?)
- You hit value questions (what do we actually want?)
- You start going in circles

**Depth limit**: Usually 3-5 levels. Beyond that, you're likely overthinking.

---

### Phase 5: Bedrock Detection

**Recognize when you've hit foundational level.**

Bedrock indicators:

| Type | Characteristic | Example |
|------|----------------|---------|
| **Definitional** | Question about meaning of terms | "What do we mean by 'success'?" |
| **Empirical** | Question answerable by measurement | "What's our current conversion rate?" |
| **Value** | Question about what matters | "What do we actually care about?" |
| **Constraint** | Question about fixed limitations | "What can't we change?" |

**Prompt:**
```
Have we reached bedrock?

CURRENT QUESTION: [deepest question reached]

Check:
1. Is this DEFINITIONAL? (about meaning of terms)
2. Is this EMPIRICAL? (answerable by data)
3. Is this about VALUES? (what we care about)
4. Is this about CONSTRAINTS? (what's fixed)
5. Are we CIRCLING? (coming back to earlier questions)

If any are true, we've likely hit bedrock. If not, descend further.

What type of bedrock is this? What does that tell us?
```

---

### Phase 6: Question Reconstruction

**Build the better question from bedrock up.**

Now that you understand the foundations, construct a question that:
- Removes flawed assumptions
- Incorporates insights from the descent
- Is at the right level of abstraction
- Is actually answerable

**Prompt:**
```
Reconstruct a better question:

ORIGINAL: [original question]
BEDROCK REACHED: [foundational question/insight]
FLAWED ASSUMPTIONS REMOVED: [list]
KEY INSIGHTS: [from the descent]

Build a NEW question that:
1. Doesn't contain the flawed assumptions
2. Incorporates the bedrock insights
3. Is specific enough to answer
4. Is at the right level (not too surface, not too abstract)

The reconstructed question should make the original question obsolete.
```

**Example:**
```
Original: "How do I become more productive?"

Reconstructed: "Given that I value deep work and creative output over
busyness metrics, what changes to my environment and schedule would
create more protected time for focused work?"
```

---

### Phase 7: Answer Emergence

**Check if the answer is now obvious.**

Often, the reconstructed question makes the answer clear:

| Reconstructed Question | Emergent Answer |
|------------------------|-----------------|
| "What changes create protected time for focused work?" | Block mornings, disable notifications, say no to meetings |
| "What problem are we actually solving?" | Oh, we don't need a framework, we need a conversation |
| "What do we actually care about?" | Not productivity — fulfillment |

**Prompt:**
```
Does the reconstructed question make the answer obvious?

RECONSTRUCTED QUESTION: [question]

1. Is the answer now CLEAR? If so, what is it?
2. Is the answer now SIMPLER than expected? Why?
3. Did the question reveal the answer was WRONG QUESTION? What now?
4. If answer still not obvious, what RESEARCH is needed? Which recipe?
```

---

### Phase 8: Remaining Research

**If the answer isn't obvious, determine what to research.**

The Socratic Engine's job is question improvement, not necessarily answering. If research is still needed:

1. You now have a BETTER question to research
2. Recommend which recipe to use
3. The research will be more efficient because the question is clearer

---

## Output Structure

```markdown
# Original Question
[As given]

## Assumption Excavation
| Assumption | Status | Notes |
|------------|--------|-------|
| [assumption] | Solid/Questionable/Flawed | [reasoning] |

## The Descent

### Level 1: Surface
Question: [original]
Key Issue: [what's wrong with this level]

### Level 2: Deeper
Question: [deeper question]
Key Issue: [what's wrong with this level]

### Level 3: Bedrock
Question: [foundational question]
Type: [definitional/empirical/value/constraint]

## Reconstructed Question
[The better question]

### Why It's Better
- Removes: [flawed assumptions removed]
- Adds: [insights incorporated]
- Level: [why this is the right level]

## Emergent Answer
[If the answer is now obvious]

OR

## Remaining Research
- Question to research: [reconstructed question]
- Recommended recipe: [which recipe and why]
- Expected difficulty: [easier/same/harder than original]

## Meta-Insight
[What did the descent reveal about the original question?]
```

---

## When to Use This Recipe

**Use The Socratic Engine when:**
- You suspect the question itself is flawed
- Direct research has been unsatisfying
- Stakeholders disagree on what the question is
- Question seems simple but answers don't satisfy
- You're stuck and don't know why
- As a FIRST STEP before other recipes
- For philosophical or values-laden questions

**Don't use when:**
- Question is clearly well-formed
- Speed matters more than depth
- Question is purely empirical/factual
- You need to explore, not refine

---

## The Socratic Method

This recipe is named for Socrates' method of inquiry:

1. **Claim ignorance**: Start without assuming you know the answer
2. **Ask questions**: Probe assumptions through questioning
3. **Expose contradictions**: Find where assumptions conflict
4. **Seek definitions**: Clarify vague terms
5. **Follow the argument**: Go where logic leads, not where you want

The goal isn't to answer but to UNDERSTAND what's really being asked.

---

## Comparison With Other Recipes

| Aspect | Other Recipes | Socratic Engine |
|--------|--------------|-----------------|
| Input | Question (accepted) | Question (examined) |
| Process | Find answer | Improve question |
| Output | Answer | Better question (+ maybe answer) |
| Assumption handling | Surface them | Challenge them |
| Depth | Into answers | Into questions |
| Success | Good answer | Right question |

---

## The Core Insight

> **A great question answered poorly beats a poor question answered brilliantly.**

The Socratic Engine ensures you're asking the right question before spending resources answering it. Often, the right question makes the answer obvious — no further research needed.

---

## Implementation Notes

**Complexity**: Medium
- Sequential descent (can't parallelize the core)
- Usually 3-5 levels deep
- Final phase may hand off to other recipes

**Cost optimization:**
- Use opus for assumption challenging (requires judgment)
- Use haiku for excavation (more mechanical)
- Stop descent when bedrock detected (don't over-recurse)

**Key challenges:**
- Knowing when to stop descending
- Avoiding analysis paralysis
- Distinguishing "deeper" from "different"
- Reconstructing a question that's actually better

---

**The one-sentence summary:**

> **The Socratic Engine improves questions through recursive assumption-challenging — because the right question often makes the answer obvious.**
