"""
Base provider abstraction.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ProviderOptions:
    """Options for provider calls."""

    system_prompt: str | None = None
    max_tokens: int | None = None
    temperature: float | None = None
    web_search: bool = False


class Provider(ABC):
    """Abstract base class for LLM providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (claude, gemini)."""
        ...

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: str,
        options: ProviderOptions | None = None,
    ) -> str:
        """
        Generate a response from the LLM.

        Args:
            prompt: The user prompt/question
            model: Model name (opus, haiku, flash, pro)
            options: Optional generation options

        Returns:
            Generated text response
        """
        ...

    async def explore(self, question: str, model: str) -> str:
        """Explore a question for research angles."""
        options = ProviderOptions(
            system_prompt=EXPLORE_PROMPT,
        )
        return await self.generate(question, model, options)

    async def answer(self, question: str, model: str) -> str:
        """Answer a question directly (leaf node)."""
        options = ProviderOptions(
            system_prompt=LEAF_PROMPT,
        )
        return await self.generate(question, model, options)

    async def synthesize(
        self,
        question: str,
        results: str,
        model: str,
    ) -> str:
        """Synthesize research results into coherent answer."""
        prompt = SYNTHESIZE_PROMPT.format(
            QUESTION=question,
            RESULTS=results,
        )
        return await self.generate(
            "Synthesize the research above.",
            model,
            ProviderOptions(system_prompt=prompt),
        )

    async def merge(
        self,
        question: str,
        responses: str,
        model: str,
    ) -> str:
        """Merge multiple model responses (ensemble mode)."""
        prompt = MERGE_PROMPT.format(
            QUESTION=question,
            RESPONSES=responses,
        )
        return await self.generate(
            "Merge the responses above into a unified answer.",
            model,
            ProviderOptions(system_prompt=prompt),
        )


# =============================================================================
# Prompts (same as bash version)
# =============================================================================

EXPLORE_PROMPT = """You are a research agent. Given a question, identify all important angles worth exploring.

Think deeply:
- What would experts consider?
- What is non-obvious or often missed?
- What tensions or tradeoffs exist?

List each angle as a focused research question on its own line starting with "Q: "

Be thorough. Do not stop at obvious angles."""

LEAF_PROMPT = """You are a focused research agent. Answer the question directly and thoroughly.
Be comprehensive but concise. Provide concrete examples where helpful."""

SYNTHESIZE_PROMPT = """Synthesize the following research into a coherent, insightful answer.

Original question: {QUESTION}

Research findings:

{RESULTS}

Draw connections between findings, highlight tensions, and provide a nuanced perspective."""

MERGE_PROMPT = """You are combining multiple AI responses to the same question.
Extract the best insights from each, resolve any conflicts, and produce a single comprehensive answer.

Question: {QUESTION}

{RESPONSES}

Provide a unified, high-quality answer that captures the best of each response."""
