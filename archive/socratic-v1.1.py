"""
The Socratic Engine - Question Alchemy.

Transform questions, not just answer them.
The quality of answers is bounded by the quality of questions.

Most research fails not from bad answers, but from bad questions.
"""

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field
from rich.console import Console

from ..models import ModelSpec
from ..providers import get_provider_for_model
from .base import Recipe, RecipeContext, RecipeOutput

console = Console(stderr=True)


# =============================================================================
# Prompts
# =============================================================================

EXCAVATE_PROMPT = """Excavate the 5-7 MOST CRITICAL hidden assumptions in this question:

QUESTION: {question}

Consider these dimensions:
- What does it assume EXISTS or is TRUE?
- What does it assume is DESIRABLE or POSSIBLE?
- What TERMS are undefined or FRAMING is imposed?

Focus on assumptions that, if wrong, would completely change the answer.
Skip trivial assumptions (like "language exists" or "numbers exist").

List exactly 5-7 assumptions, ranked by importance.
Format each as:
A: [assumption]"""

CHALLENGE_PROMPT = """Challenge this assumption:

ASSUMPTION: {assumption}

1. IS THIS TRUE? What evidence supports or contradicts it?
2. WHEN IS IT FALSE? Under what conditions does this assumption break?
3. WHO BENEFITS? Who gains from this assumption being accepted?
4. WHAT IF OPPOSITE? What would it mean if the opposite were true?
5. WHY ASSUMED? Where does this assumption come from?

Rate this assumption:
- SOLID: Well-grounded, keep it
- QUESTIONABLE: Might be wrong, examine further
- FLAWED: Likely wrong, remove or replace

Provide your rating on a line starting with "RATING:"."""

DEEPER_PROMPT = """Find the deeper question beneath this one:

SURFACE QUESTION: {question}

CHALLENGED ASSUMPTIONS:
{assumptions}

Given the questionable assumptions, what DEEPER question lies beneath?

Ask:
1. WHY is this question being asked? What's the real concern?
2. WHAT WOULD CHANGE if we knew the answer? What decision does this enable?
3. WHAT'S BENEATH? If we removed the flawed assumptions, what question remains?

The deeper question is often more useful than the surface question.

Provide the deeper question on a line starting with "DEEPER:"."""

BEDROCK_PROMPT = """Have we reached bedrock?

CURRENT QUESTION: {question}

Check:
1. Is this DEFINITIONAL? (about meaning of terms)
2. Is this EMPIRICAL? (answerable by data)
3. Is this about VALUES? (what we care about)
4. Is this about CONSTRAINTS? (what's fixed)
5. Are we CIRCLING? (coming back to earlier questions)

If any are true, we've likely hit bedrock. If not, descend further.

What type of bedrock is this? What does that tell us?

On a line starting with "BEDROCK:", write YES or NO.
If YES, on a line starting with "TYPE:", write the type (DEFINITIONAL, EMPIRICAL, VALUES, CONSTRAINTS)."""

RECONSTRUCT_PROMPT = """Reconstruct a better question:

ORIGINAL: {original}
BEDROCK REACHED: {bedrock}
FLAWED ASSUMPTIONS REMOVED: {flawed}
KEY INSIGHTS: {insights}

Build a NEW question that:
1. Doesn't contain the flawed assumptions
2. Incorporates the bedrock insights
3. Is specific enough to answer
4. Is at the right level (not too surface, not too abstract)

The reconstructed question should make the original question obsolete.

Provide the reconstructed question on a line starting with "RECONSTRUCTED:"."""

EMERGENCE_PROMPT = """Does the reconstructed question make the answer obvious?

RECONSTRUCTED QUESTION: {question}

1. Is the answer now CLEAR? If so, what is it?
2. Is the answer now SIMPLER than expected? Why?
3. Did the question reveal the answer was WRONG QUESTION? What now?
4. If answer still not obvious, what RESEARCH is needed?

On a line starting with "OBVIOUS:", write YES or NO.
If YES, provide the answer on lines starting with "ANSWER:"."""


# =============================================================================
# Data Models
# =============================================================================

class AssumptionStatus(str, Enum):
    SOLID = "solid"
    QUESTIONABLE = "questionable"
    FLAWED = "flawed"


class BedrockType(str, Enum):
    DEFINITIONAL = "definitional"
    EMPIRICAL = "empirical"
    VALUES = "values"
    CONSTRAINTS = "constraints"
    NONE = "none"


class Assumption(BaseModel):
    """An assumption extracted from a question."""
    text: str
    status: AssumptionStatus = AssumptionStatus.QUESTIONABLE
    challenge_result: str | None = None


class DescentLevel(BaseModel):
    """One level of the Socratic descent."""
    question: str
    assumptions: list[Assumption] = Field(default_factory=list)
    deeper_question: str | None = None
    is_bedrock: bool = False
    bedrock_type: BedrockType = BedrockType.NONE


class SocraticOutput(RecipeOutput):
    """Output from the Socratic Engine."""
    descent: list[DescentLevel] = Field(default_factory=list)
    reconstructed_question: str | None = None
    answer_emerged: bool = False
    emergent_answer: str | None = None
    recommended_recipe: str | None = None


# =============================================================================
# Implementation
# =============================================================================

class SocraticEngine(Recipe):
    """
    The Socratic Engine transforms questions through assumption-challenging.

    Phases:
    1. Assumption Excavation - surface hidden assumptions
    2. Assumption Challenging - challenge each assumption
    3. Deeper Question - find the question beneath
    4. Recursive Descent - repeat until bedrock
    5. Bedrock Detection - recognize foundational level
    6. Question Reconstruction - build better question
    7. Answer Emergence - check if answer is now obvious
    """

    MAX_DESCENT_DEPTH = 5  # Prevent infinite recursion

    @property
    def name(self) -> str:
        return "socratic"

    @property
    def philosophy(self) -> str:
        return "Transform questions through recursive assumption-challenging"

    async def run(
        self,
        question: str,
        context: RecipeContext,
    ) -> SocraticOutput:
        """Execute the Socratic Engine on a question."""
        console.print(f"\n[bold blue]Socratic Engine[/bold blue]: {question[:60]}...")

        # Get the model for Socratic analysis (use orchestrator for judgment tasks)
        model = context.config.orchestrator
        provider = get_provider_for_model(model)

        descent: list[DescentLevel] = []
        current_question = question
        all_insights: list[str] = []
        flawed_assumptions: list[str] = []

        # Recursive descent until bedrock
        for depth in range(self.MAX_DESCENT_DEPTH):
            console.print(f"\n[dim]Level {depth + 1}: {current_question[:60]}...[/dim]")

            level = DescentLevel(question=current_question)

            # Phase 1: Excavate assumptions
            console.print("[dim]  Excavating assumptions...[/dim]")
            excavate_result = await provider.generate(
                EXCAVATE_PROMPT.format(question=current_question),
                model.model,
            )
            all_assumptions = self._parse_assumptions(excavate_result)
            # Limit to top 7 most critical assumptions to avoid N+1 query explosion
            assumptions = all_assumptions[:7]
            level.assumptions = assumptions
            console.print(f"[dim]  Found {len(all_assumptions)} assumptions, using top {len(assumptions)}[/dim]")

            # Phase 2: Challenge assumptions in parallel
            total = len(assumptions)
            completed = 0

            async def challenge_one(assumption: Assumption) -> None:
                nonlocal completed
                challenge_result = await provider.generate(
                    CHALLENGE_PROMPT.format(assumption=assumption.text),
                    model.model,
                )
                assumption.challenge_result = challenge_result
                assumption.status = self._parse_rating(challenge_result)
                completed += 1
                console.print(f"[dim]  Challenged {completed}/{total}: {assumption.text[:40]}...[/dim]")

            await asyncio.gather(*[challenge_one(a) for a in assumptions])

            # Collect flawed assumptions after parallel challenges
            for assumption in assumptions:
                if assumption.status == AssumptionStatus.FLAWED:
                    flawed_assumptions.append(assumption.text)

            questionable_count = sum(
                1 for a in assumptions
                if a.status in (AssumptionStatus.QUESTIONABLE, AssumptionStatus.FLAWED)
            )
            console.print(f"[dim]  {questionable_count} questionable/flawed assumptions[/dim]")

            # Phase 3: Check for bedrock
            console.print("[dim]  Checking for bedrock...[/dim]")
            bedrock_result = await provider.generate(
                BEDROCK_PROMPT.format(question=current_question),
                model.model,
            )
            is_bedrock, bedrock_type = self._parse_bedrock(bedrock_result)
            level.is_bedrock = is_bedrock
            level.bedrock_type = bedrock_type

            descent.append(level)

            if is_bedrock:
                console.print(f"[dim]  Bedrock reached: {bedrock_type.value}[/dim]")
                all_insights.append(f"Bedrock ({bedrock_type.value}): {current_question}")
                break

            # Phase 4: Find deeper question
            console.print("[dim]  Finding deeper question...[/dim]")
            assumptions_text = "\n".join(
                f"- {a.text} ({a.status.value})"
                for a in assumptions
            )
            deeper_result = await provider.generate(
                DEEPER_PROMPT.format(
                    question=current_question,
                    assumptions=assumptions_text,
                ),
                model.model,
            )
            deeper_question = self._parse_deeper(deeper_result)
            level.deeper_question = deeper_question

            if deeper_question and deeper_question != current_question:
                current_question = deeper_question
                all_insights.append(f"Level {depth + 1}: {deeper_question}")
            else:
                # Couldn't go deeper, treat as bedrock
                level.is_bedrock = True
                console.print("[dim]  No deeper question found, treating as bedrock[/dim]")
                break

        # Phase 5: Reconstruct the question
        console.print("\n[dim]Reconstructing question...[/dim]")
        final_level = descent[-1]
        reconstruct_result = await provider.generate(
            RECONSTRUCT_PROMPT.format(
                original=question,
                bedrock=final_level.question,
                flawed=", ".join(flawed_assumptions) or "None identified",
                insights="\n".join(all_insights) or "None",
            ),
            model.model,
        )
        reconstructed = self._parse_reconstructed(reconstruct_result)
        console.print(f"[dim]Reconstructed: {reconstructed[:60]}...[/dim]")

        # Phase 6: Check for answer emergence
        console.print("[dim]Checking for answer emergence...[/dim]")
        emergence_result = await provider.generate(
            EMERGENCE_PROMPT.format(question=reconstructed or question),
            model.model,
        )
        answer_emerged, emergent_answer = self._parse_emergence(emergence_result)

        if answer_emerged:
            console.print("[green]Answer emerged from the question![/green]")
        else:
            console.print("[dim]Answer not obvious, further research recommended[/dim]")

        # Build final output
        final_output = self._build_output(
            original=question,
            descent=descent,
            reconstructed=reconstructed,
            answer_emerged=answer_emerged,
            emergent_answer=emergent_answer,
            flawed_assumptions=flawed_assumptions,
            insights=all_insights,
        )

        return SocraticOutput(
            original_question=question,
            final_output=final_output,
            descent=descent,
            reconstructed_question=reconstructed,
            answer_emerged=answer_emerged,
            emergent_answer=emergent_answer,
            recommended_recipe="recursive_research" if not answer_emerged else None,
            metadata={
                "depth": len(descent),
                "flawed_assumptions": flawed_assumptions,
                "bedrock_type": final_level.bedrock_type.value,
            },
        )

    def _parse_assumptions(self, output: str) -> list[Assumption]:
        """Parse assumptions from excavation output."""
        assumptions = []
        for line in output.strip().split("\n"):
            line = line.strip()
            if line.startswith("A:"):
                text = line[2:].strip()
                if text:
                    assumptions.append(Assumption(text=text))
        return assumptions

    def _parse_rating(self, output: str) -> AssumptionStatus:
        """Parse assumption rating from challenge output."""
        output_lower = output.lower()
        for line in output.split("\n"):
            if line.strip().lower().startswith("rating:"):
                rating_text = line.split(":", 1)[1].strip().lower()
                if "flawed" in rating_text:
                    return AssumptionStatus.FLAWED
                elif "solid" in rating_text:
                    return AssumptionStatus.SOLID
                elif "questionable" in rating_text:
                    return AssumptionStatus.QUESTIONABLE
        # Default based on content
        if "flawed" in output_lower:
            return AssumptionStatus.FLAWED
        elif "solid" in output_lower:
            return AssumptionStatus.SOLID
        return AssumptionStatus.QUESTIONABLE

    def _parse_bedrock(self, output: str) -> tuple[bool, BedrockType]:
        """Parse bedrock detection from output."""
        is_bedrock = False
        bedrock_type = BedrockType.NONE

        for line in output.split("\n"):
            line = line.strip().lower()
            if line.startswith("bedrock:"):
                value = line.split(":", 1)[1].strip()
                is_bedrock = "yes" in value
            elif line.startswith("type:"):
                value = line.split(":", 1)[1].strip().upper()
                try:
                    bedrock_type = BedrockType(value.lower())
                except ValueError:
                    pass

        return is_bedrock, bedrock_type

    def _parse_deeper(self, output: str) -> str | None:
        """Parse deeper question from output."""
        for line in output.split("\n"):
            if line.strip().startswith("DEEPER:"):
                return line.split(":", 1)[1].strip()
        return None

    def _parse_reconstructed(self, output: str) -> str | None:
        """Parse reconstructed question from output."""
        for line in output.split("\n"):
            if line.strip().startswith("RECONSTRUCTED:"):
                return line.split(":", 1)[1].strip()
        return None

    def _parse_emergence(self, output: str) -> tuple[bool, str | None]:
        """Parse answer emergence from output."""
        is_obvious = False
        answer = None

        lines = output.split("\n")
        collecting_answer = False
        answer_lines = []

        for line in lines:
            stripped = line.strip()
            if stripped.lower().startswith("obvious:"):
                value = stripped.split(":", 1)[1].strip().lower()
                is_obvious = "yes" in value
            elif stripped.startswith("ANSWER:"):
                collecting_answer = True
                answer_part = stripped.split(":", 1)[1].strip()
                if answer_part:
                    answer_lines.append(answer_part)
            elif collecting_answer:
                answer_lines.append(line)

        if answer_lines:
            answer = "\n".join(answer_lines).strip()

        return is_obvious, answer

    def _build_output(
        self,
        original: str,
        descent: list[DescentLevel],
        reconstructed: str | None,
        answer_emerged: bool,
        emergent_answer: str | None,
        flawed_assumptions: list[str],
        insights: list[str],
    ) -> str:
        """Build the final markdown output."""
        output = f"""# Socratic Analysis

## Original Question
{original}

## Assumption Analysis
"""

        # Add assumption list (cleaner than table)
        all_assumptions = []
        for level in descent:
            all_assumptions.extend(level.assumptions)

        if all_assumptions:
            for a in all_assumptions:
                status_icon = {"solid": "✓", "questionable": "?", "flawed": "✗"}.get(a.status.value, "•")
                output += f"\n- [{status_icon}] **{a.status.value.upper()}**: {a.text}\n"

        # Add descent
        output += "\n## The Descent\n"
        for i, level in enumerate(descent, 1):
            level_type = "Bedrock" if level.is_bedrock else f"Level {i}"
            output += f"\n### {level_type}\n"
            output += f"**Question:** {level.question}\n"
            if level.is_bedrock:
                output += f"**Type:** {level.bedrock_type.value}\n"
            if level.deeper_question:
                output += f"**Deeper:** {level.deeper_question}\n"

        # Add reconstructed question
        if reconstructed:
            output += f"""
## Reconstructed Question
{reconstructed}

### Why It's Better
- Removes: {', '.join(flawed_assumptions) if flawed_assumptions else 'No flawed assumptions identified'}
- Insights: {', '.join(insights) if insights else 'None'}
"""

        # Add answer or recommendation
        if answer_emerged and emergent_answer:
            output += f"""
## Emergent Answer
The reconstructed question made the answer clear:

{emergent_answer}
"""
        else:
            output += """
## Remaining Research
The answer is not yet obvious. Recommended next step:
- Use **Recursive Research** on the reconstructed question
- The improved question should yield clearer results
"""

        return output
