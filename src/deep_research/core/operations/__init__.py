"""
Concrete operation implementations for the MasterChef.

These operations connect the abstract framework to actual LLM calls
through the provider system.
"""

from .answer import AnswerOperation
from .base import register_all_operations
from .decompose import DecomposeOperation
from .detect import DetectOperation
from .ground import GroundOperation
from .synthesize import SynthesizeOperation

__all__ = [
    "DecomposeOperation",
    "AnswerOperation",
    "SynthesizeOperation",
    "DetectOperation",
    "GroundOperation",
    "register_all_operations",
]
