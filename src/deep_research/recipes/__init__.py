"""
Research recipes - different methodologies for exploring questions.

Each recipe implements a different philosophy for transforming questions into answers:
- Recursive Research: Mining (extract answers through recursive exploration)
- Socratic Engine: Alchemy (transform questions to make answers emerge)
- Inverse Engine: Sculpture (derive success from failure research)
- Adversarial Engine: Courtroom (truth from structured debate)
- Emergence Engine: Gardening (cultivate insight through perspective collision)
- Perspective Expander: Prism (refract question through multiple model viewpoints)
"""

from .base import Recipe
from .perspective import (
    DEFAULT_MODEL_PERSPECTIVE_MATCHING,
    PERSPECTIVE_LIBRARY,
    Perspective,
    PerspectiveCache,
    PerspectiveExpander,
    PerspectiveResult,
    create_all_models_expander,
    create_default_expander,
    detect_domain,
    get_perspective_cache,
    match_model_to_perspective,
)
from .socratic import SocraticEngine

__all__ = [
    "Recipe",
    "SocraticEngine",
    # Perspective expansion
    "PerspectiveExpander",
    "PerspectiveResult",
    "PerspectiveCache",
    "Perspective",
    "create_default_expander",
    "create_all_models_expander",
    "get_perspective_cache",
    "detect_domain",
    "match_model_to_perspective",
    "PERSPECTIVE_LIBRARY",
    "DEFAULT_MODEL_PERSPECTIVE_MATCHING",
]
