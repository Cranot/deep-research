"""
Base recipe abstraction.

A Recipe is a methodology for transforming a question into an answer.
Each recipe has its own philosophy and flow.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from ..models import ResearchConfig


class RecipeOutput(BaseModel):
    """Base output for all recipes."""

    original_question: str
    final_output: str
    metadata: dict[str, Any] = {}


@dataclass
class RecipeContext:
    """Context passed to recipe execution."""

    config: ResearchConfig
    output_dir: Path

    @property
    def agents_dir(self) -> Path:
        return self.output_dir / "agents"


class Recipe(ABC):
    """
    Abstract base class for research recipes.

    Each recipe implements a different methodology:
    - Socratic: Transform questions through assumption challenging
    - Inverse: Research failure to derive success
    - Adversarial: Debate to stress-test positions
    - Emergence: Collide perspectives to cultivate insight
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Recipe name (socratic, inverse, adversarial, emergence)."""
        ...

    @property
    @abstractmethod
    def philosophy(self) -> str:
        """One-line philosophy of this recipe."""
        ...

    @abstractmethod
    async def run(
        self,
        question: str,
        context: RecipeContext,
    ) -> RecipeOutput:
        """
        Execute the recipe on a question.

        Args:
            question: The research question
            context: Execution context with config and paths

        Returns:
            RecipeOutput with the transformed/answered question
        """
        ...
