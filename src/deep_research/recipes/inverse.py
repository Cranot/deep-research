"""
The Inverse Engine - Failure Alchemy.

Research failure to derive success.
Failure is concrete; success is slippery.

Most advice fails because it studies success directly.
Survivors are visible; the dead are silent.
"""

import asyncio

from pydantic import BaseModel, Field
from rich.console import Console

from ..providers import get_provider_for_model
from .base import Recipe, RecipeContext, RecipeOutput

console = Console(stderr=True)


# =============================================================================
# Prompts
# =============================================================================

INVERT_PROMPT = """Invert this question to focus on FAILURE:

ORIGINAL: {question}

Reframe the question to ask about failure instead of success.
Examples:
- "How do I become successful?" → "What causes people to fail?"
- "What makes a good API?" → "What makes APIs frustrating to use?"
- "How do I learn faster?" → "What prevents people from learning?"

The inverted question should:
1. Be specific about failure modes, not vague
2. Focus on concrete, observable failures
3. Be answerable through research

Provide the inverted question on a line starting with "INVERTED:"."""

ENUMERATE_PROMPT = """List the major failure modes for this question:

QUESTION: {question}

Enumerate 5-7 distinct, concrete ways this fails.
Focus on:
- Common failures (happen frequently)
- Catastrophic failures (cause total breakdown)
- Hidden failures (not obvious until too late)
- Systemic failures (built into the structure)

Format each as:
F: [failure mode] - [brief description]"""

RESEARCH_FAILURE_PROMPT = """Research this specific failure mode:

FAILURE: {failure}
CONTEXT: {context}

Explain:
1. WHY does this failure occur? (root causes)
2. HOW does it manifest? (symptoms and signs)
3. WHO is most susceptible? (risk factors)
4. WHEN does it typically happen? (timing/triggers)
5. WHAT makes it hard to prevent? (structural barriers)

Be concrete and specific. Use examples where helpful."""

INVERSION_PROMPT = """Transform failure insights into success principles:

ORIGINAL QUESTION: {original}
INVERTED QUESTION: {inverted}

FAILURE RESEARCH:
{failures}

For each failure mode, derive the INVERSE principle for success.
The logic: If X causes failure, then avoiding/reversing X contributes to success.

Format as:
FAILURE: [failure mode]
SUCCESS PRINCIPLE: [what to do instead]
CONFIDENCE: HIGH/MEDIUM/LOW (based on how directly the inversion applies)

Then provide a synthesis of all success principles."""

VALIDATE_PROMPT = """Validate these derived success principles:

ORIGINAL QUESTION: {original}

DERIVED PRINCIPLES:
{principles}

Check each principle:
1. Is this ACTIONABLE? (specific enough to implement)
2. Is this SUFFICIENT? (does avoiding failure guarantee success?)
3. Are there GAPS? (failures we didn't consider)
4. Are there CONFLICTS? (principles that contradict each other)

Identify any weaknesses in our inversion logic.
Suggest any missing failure modes we should have considered.

Provide validation summary on a line starting with "VALID:"
followed by YES (solid), PARTIAL (has gaps), or NO (flawed)."""


# =============================================================================
# Data Models
# =============================================================================


class FailureMode(BaseModel):
    """A specific way something fails."""

    description: str
    research: str | None = None
    success_principle: str | None = None
    confidence: str = "MEDIUM"


class InverseOutput(RecipeOutput):
    """Output from the Inverse Engine."""

    inverted_question: str
    failure_modes: list[FailureMode] = Field(default_factory=list)
    success_principles: list[str] = Field(default_factory=list)
    validation_status: str = "PARTIAL"
    gaps_identified: list[str] = Field(default_factory=list)


# =============================================================================
# Implementation
# =============================================================================


class InverseEngine(Recipe):
    """
    The Inverse Engine derives success by researching failure.

    Phases:
    1. Inversion - Flip the question to focus on failure
    2. Enumeration - List concrete failure modes
    3. Research - Deep dive into each failure
    4. Transformation - Derive success principles from failures
    5. Validation - Check for gaps and conflicts
    6. Synthesis - Combine into actionable guidance
    """

    @property
    def name(self) -> str:
        return "inverse"

    @property
    def philosophy(self) -> str:
        return "Research failure to derive success"

    async def run(
        self,
        question: str,
        context: RecipeContext,
    ) -> InverseOutput:
        """Execute the Inverse Engine on a question."""
        console.print(f"\n[bold magenta]Inverse Engine[/bold magenta]: {question[:60]}...")

        model = context.config.orchestrator
        provider = get_provider_for_model(model)

        # Phase 1: Invert the question
        console.print("[dim]  Inverting question...[/dim]")
        invert_result = await provider.generate(
            INVERT_PROMPT.format(question=question),
            model.model,
        )
        inverted = (
            self._parse_inverted(invert_result)
            or f"What causes {question.lower().replace('how do i ', '').replace('what makes ', '')} to fail?"
        )
        console.print(f"[dim]  Inverted: {inverted[:50]}...[/dim]")

        # Phase 2: Enumerate failure modes
        console.print("[dim]  Enumerating failures...[/dim]")
        enumerate_result = await provider.generate(
            ENUMERATE_PROMPT.format(question=inverted),
            model.model,
        )
        failure_modes = self._parse_failures(enumerate_result)
        console.print(f"[dim]  Found {len(failure_modes)} failure modes[/dim]")

        # Phase 3: Research each failure in parallel
        console.print("[dim]  Researching failures...[/dim]")
        total = len(failure_modes)
        completed = 0

        async def research_failure(fm: FailureMode) -> None:
            nonlocal completed
            result = await provider.generate(
                RESEARCH_FAILURE_PROMPT.format(
                    failure=fm.description,
                    context=question,
                ),
                model.model,
            )
            fm.research = result
            completed += 1
            console.print(f"[dim]  Researched {completed}/{total}: {fm.description[:40]}...[/dim]")

        await asyncio.gather(*[research_failure(fm) for fm in failure_modes])

        # Phase 4: Transform failures into success principles
        console.print("[dim]  Deriving success principles...[/dim]")
        failures_text = "\n\n".join(
            f"FAILURE: {fm.description}\nRESEARCH: {fm.research[:500]}..." for fm in failure_modes
        )
        inversion_result = await provider.generate(
            INVERSION_PROMPT.format(
                original=question,
                inverted=inverted,
                failures=failures_text,
            ),
            model.model,
        )
        self._parse_principles(inversion_result, failure_modes)

        # Phase 5: Validate
        console.print("[dim]  Validating principles...[/dim]")
        principles_text = "\n".join(
            f"- {fm.success_principle} (from: {fm.description[:30]}...)"
            for fm in failure_modes
            if fm.success_principle
        )
        validate_result = await provider.generate(
            VALIDATE_PROMPT.format(
                original=question,
                principles=principles_text,
            ),
            model.model,
        )
        validation_status, gaps = self._parse_validation(validate_result)
        console.print(f"[dim]  Validation: {validation_status}[/dim]")

        # Build output
        final_output = self._build_output(
            original=question,
            inverted=inverted,
            failure_modes=failure_modes,
            validation_status=validation_status,
            gaps=gaps,
            inversion_result=inversion_result,
        )

        return InverseOutput(
            original_question=question,
            final_output=final_output,
            inverted_question=inverted,
            failure_modes=failure_modes,
            success_principles=[
                fm.success_principle for fm in failure_modes if fm.success_principle
            ],
            validation_status=validation_status,
            gaps_identified=gaps,
            metadata={
                "failure_count": len(failure_modes),
                "validation": validation_status,
            },
        )

    def _parse_inverted(self, output: str) -> str | None:
        """Parse inverted question from output."""
        for line in output.split("\n"):
            if line.strip().startswith("INVERTED:"):
                return line.split(":", 1)[1].strip()
        return None

    def _parse_failures(self, output: str) -> list[FailureMode]:
        """Parse failure modes from enumeration output."""
        failures = []
        for line in output.strip().split("\n"):
            line = line.strip()
            if line.startswith("F:"):
                text = line[2:].strip()
                if text:
                    failures.append(FailureMode(description=text))
        return failures[:7]  # Limit to 7

    def _parse_principles(self, output: str, failure_modes: list[FailureMode]) -> None:
        """Parse success principles and attach to failure modes."""
        current_failure = None
        for line in output.split("\n"):
            line = line.strip()
            if line.startswith("FAILURE:"):
                failure_text = line.split(":", 1)[1].strip().lower()
                # Find matching failure mode
                for fm in failure_modes:
                    if failure_text[:30] in fm.description.lower():
                        current_failure = fm
                        break
            elif line.startswith("SUCCESS PRINCIPLE:") and current_failure:
                current_failure.success_principle = line.split(":", 1)[1].strip()
            elif line.startswith("CONFIDENCE:") and current_failure:
                current_failure.confidence = line.split(":", 1)[1].strip()

    def _parse_validation(self, output: str) -> tuple[str, list[str]]:
        """Parse validation result."""
        status = "PARTIAL"
        gaps = []

        for line in output.split("\n"):
            line = line.strip()
            if line.startswith("VALID:"):
                value = line.split(":", 1)[1].strip().upper()
                if "YES" in value:
                    status = "YES"
                elif "NO" in value:
                    status = "NO"
                else:
                    status = "PARTIAL"

        # Extract gap mentions (simple heuristic)
        if "gap" in output.lower() or "missing" in output.lower():
            for line in output.split("\n"):
                if "gap" in line.lower() or "missing" in line.lower():
                    gaps.append(line.strip()[:100])

        return status, gaps[:5]

    def _build_output(
        self,
        original: str,
        inverted: str,
        failure_modes: list[FailureMode],
        validation_status: str,
        gaps: list[str],
        inversion_result: str,
    ) -> str:
        """Build the final markdown output."""
        output = f"""# Inverse Analysis

## Original Question
{original}

## Inverted Question
{inverted}

## Failure Modes Researched

"""
        for i, fm in enumerate(failure_modes, 1):
            confidence_icon = {"HIGH": "●", "MEDIUM": "◐", "LOW": "○"}.get(fm.confidence, "◐")
            output += f"""### {i}. {fm.description}

**Research Summary:**
{(fm.research or "No research")[:500]}...

**Success Principle:** {fm.success_principle or "Not derived"}
**Confidence:** {confidence_icon} {fm.confidence}

---

"""

        # Add synthesis section
        output += f"""## Synthesis: From Failure to Success

{inversion_result}

## Validation

**Status:** {validation_status}

"""
        if gaps:
            output += "**Gaps Identified:**\n"
            for gap in gaps:
                output += f"- {gap}\n"

        output += """
## How to Use This

1. **Avoid the failures** - Each failure mode is a pitfall to sidestep
2. **Apply the principles** - The inverted insights are your guide
3. **Mind the gaps** - Where validation is PARTIAL, do more research
4. **Success ≠ avoiding failure** - This is necessary but not sufficient
"""

        return output
