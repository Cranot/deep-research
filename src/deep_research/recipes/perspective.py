"""
Perspective Expander and Evaluator (Enhanced).

A configurable first step that:
1. Queries multiple models in parallel for their perspectives on a question
2. Collects and consolidates all perspectives
3. Uses a picker model to select which perspectives to explore
4. Optionally runs blind spot detection to find missing perspectives
5. Supports recursive perspective depth
6. Caches perspectives for similar questions
7. Matches models to perspective types based on their strengths

This expands the breadth of exploration by leveraging diverse model viewpoints
before diving into recursive research.
"""

import asyncio
import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from ..exceptions import AgentError
from ..logging import get_logger
from ..models import ModelSpec
from ..providers import get_provider_for_model
from ..providers.base import ProviderOptions
from ..settings import settings

if TYPE_CHECKING:
    pass


# =============================================================================
# Prompts
# =============================================================================

PERSPECTIVE_PROMPT = """You are generating diverse perspectives for exploring a research question.

For the question below, identify 3-5 distinct PERSPECTIVES or FRAMES through which this question could be explored. Each perspective should:
- Represent a different disciplinary lens, stakeholder viewpoint, or analytical framework
- Be fundamentally different from the others (not just variations)
- Open up unique angles that other perspectives might miss

Format each perspective on its own line starting with "P: " followed by a brief label and description.

Example:
P: Historical lens - How has this evolved over time? What precedents exist?
P: Economic lens - What are the costs, incentives, and resource implications?
P: Psychological lens - How do individual cognition and biases affect this?

Be creative and thorough. Think about what experts from different fields would emphasize."""

PERSPECTIVE_PICKER_PROMPT = """You are evaluating perspectives gathered from multiple AI models for a research question.

Original Question: {QUESTION}

The following perspectives were gathered from different models:

{PERSPECTIVES}

Your task:
1. Identify the most valuable and diverse perspectives from this collection
2. Remove duplicates or near-duplicates (keep the best formulation)
3. Ensure the final set covers fundamentally different angles
4. Aim for {MIN_COUNT}-{MAX_COUNT} high-quality, distinct perspectives

Output the selected perspectives, each on its own line starting with "P: ".
For each, briefly explain why it was selected (in parentheses).

Example:
P: Economic lens - Cost-benefit analysis and incentive structures (Selected: unique quantitative angle)
P: Cultural lens - How norms and values shape perceptions (Selected: complements psychological view)"""

BLIND_SPOT_PROMPT = """You are a blind spot detector for research perspectives.

Original Question: {QUESTION}

The following perspectives have been selected for exploration:

{PERSPECTIVES}

Your critical task: Identify what IMPORTANT perspectives are MISSING from this list.

Think about:
- What expert viewpoints are not represented?
- What stakeholders have been overlooked?
- What analytical frameworks are absent?
- What contrarian or minority views should be considered?
- What temporal, cultural, or scale considerations are missing?

For each missing perspective, output on its own line starting with "P: " followed by label and description.
Only output perspectives that are genuinely important and distinct from those already selected.
If you believe the current set is comprehensive, output: "NO_BLIND_SPOTS_DETECTED"
"""

SUB_PERSPECTIVE_PROMPT = """You are expanding a perspective into more specific sub-perspectives.

Original Question: {QUESTION}

Parent Perspective: {PARENT_PERSPECTIVE}

Break this perspective down into 2-4 more specific sub-angles that would deepen the exploration.
Each sub-perspective should:
- Be a specific aspect of the parent perspective
- Add granularity without losing connection to the parent
- Be actionable for research

Format each on its own line starting with "P: " followed by label and description.
"""


# =============================================================================
# Perspective Library - Domain Templates
# =============================================================================

PERSPECTIVE_LIBRARY = {
    "business": [
        ("Strategic", "Long-term positioning, competitive advantage, market dynamics"),
        ("Financial", "Revenue, costs, profitability, investment implications"),
        ("Operational", "Processes, efficiency, scalability, execution challenges"),
        ("Organizational", "Culture, structure, talent, leadership implications"),
        ("Customer", "User needs, experience, satisfaction, retention"),
        ("Regulatory", "Compliance, legal constraints, policy implications"),
    ],
    "technical": [
        ("Architecture", "System design, components, interfaces, scalability patterns"),
        ("Performance", "Speed, efficiency, resource utilization, optimization"),
        ("Security", "Vulnerabilities, threats, protection mechanisms, risk"),
        ("Maintainability", "Code quality, documentation, technical debt, extensibility"),
        ("Reliability", "Fault tolerance, recovery, availability, consistency"),
        ("Integration", "APIs, compatibility, interoperability, migration"),
    ],
    "research": [
        ("Theoretical", "Underlying principles, models, frameworks, paradigms"),
        ("Methodological", "Research approaches, data collection, analysis techniques"),
        ("Empirical", "Evidence, experiments, observations, measurements"),
        ("Historical", "Evolution, precedents, context, trends over time"),
        ("Comparative", "Cross-domain parallels, contrasts, analogies"),
        ("Practical", "Applications, implementations, real-world implications"),
    ],
    "social": [
        ("Psychological", "Individual cognition, behavior, motivation, biases"),
        ("Sociological", "Group dynamics, norms, institutions, structures"),
        ("Cultural", "Values, beliefs, traditions, meaning-making"),
        ("Political", "Power, governance, policy, stakeholder interests"),
        ("Ethical", "Values, rights, justice, moral implications"),
        ("Economic", "Incentives, resources, distribution, markets"),
    ],
    "philosophical": [
        ("Ontological", "Nature of being, what exists, categories of reality"),
        ("Epistemological", "Knowledge, truth, justification, certainty"),
        ("Ethical", "Right and wrong, values, duties, consequences"),
        ("Logical", "Reasoning, arguments, validity, contradictions"),
        ("Aesthetic", "Beauty, art, experience, perception"),
        ("Phenomenological", "Lived experience, consciousness, meaning"),
    ],
}

# Model-perspective type matching based on model strengths
DEFAULT_MODEL_PERSPECTIVE_MATCHING = {
    "philosophical": "opus",  # Deep reasoning
    "ontological": "opus",
    "epistemological": "opus",
    "ethical": "opus",
    "technical": "gemini:flash",  # Good at technical details
    "architecture": "gemini:flash",
    "performance": "gemini:flash",
    "computational": "gemini:flash",
    "synthesis": "kimi:kimi",  # Good at combining viewpoints
    "comparative": "kimi:kimi",
    "integration": "kimi:kimi",
    "practical": "haiku",  # Fast, concrete
    "operational": "haiku",
    "empirical": "haiku",
}


# =============================================================================
# Data Models
# =============================================================================


@dataclass
class Perspective:
    """A single perspective on the research question."""

    label: str
    description: str
    source_model: str | None = None
    selected: bool = False
    selection_reason: str | None = None
    parent: "Perspective | None" = None
    children: list["Perspective"] = field(default_factory=list)
    matched_model: str | None = None  # Model best suited to research this
    from_blind_spot: bool = False  # Was this discovered by blind spot detection
    depth: int = 0  # Depth in perspective hierarchy

    def __str__(self) -> str:
        return f"{self.label} - {self.description}"

    @classmethod
    def parse(
        cls, line: str, source_model: str | None = None, depth: int = 0
    ) -> "Perspective | None":
        """Parse a P: line into a Perspective."""
        line = line.strip()
        if not line.startswith("P: "):
            return None

        content = line[3:].strip()

        # Try to split on " - " for label and description
        if " - " in content:
            parts = content.split(" - ", 1)
            return cls(
                label=parts[0].strip(),
                description=parts[1].strip(),
                source_model=source_model,
                depth=depth,
            )
        else:
            # Just use the whole thing as description
            return cls(
                label="Perspective",
                description=content,
                source_model=source_model,
                depth=depth,
            )

    def to_dict(self) -> dict:
        """Convert to dictionary for caching."""
        return {
            "label": self.label,
            "description": self.description,
            "source_model": self.source_model,
            "selected": self.selected,
            "selection_reason": self.selection_reason,
            "matched_model": self.matched_model,
            "from_blind_spot": self.from_blind_spot,
            "depth": self.depth,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Perspective":
        """Create from dictionary (cache loading)."""
        return cls(
            label=data["label"],
            description=data["description"],
            source_model=data.get("source_model"),
            selected=data.get("selected", False),
            selection_reason=data.get("selection_reason"),
            matched_model=data.get("matched_model"),
            from_blind_spot=data.get("from_blind_spot", False),
            depth=data.get("depth", 0),
        )


@dataclass
class PerspectiveResult:
    """Result of perspective expansion."""

    question: str
    all_perspectives: list[Perspective] = field(default_factory=list)
    selected_perspectives: list[Perspective] = field(default_factory=list)
    blind_spot_perspectives: list[Perspective] = field(default_factory=list)
    model_contributions: dict[str, list[Perspective]] = field(default_factory=dict)
    picker_model: str | None = None
    duration_ms: int | None = None
    from_cache: bool = False
    perspective_depth: int = 1
    domain_detected: str | None = None

    def get_all_selected(self) -> list[Perspective]:
        """Get all selected perspectives including blind spots."""
        return self.selected_perspectives + self.blind_spot_perspectives


# =============================================================================
# Perspective Cache
# =============================================================================


class PerspectiveCache:
    """Cache for perspective expansion results."""

    def __init__(self, cache_dir: Path | None = None):
        self.cache_dir = cache_dir or settings.cache_dir / "perspectives"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _question_hash(self, question: str) -> str:
        """Create a hash for the question."""
        normalized = question.lower().strip()
        # Remove common words for better matching
        normalized = re.sub(r"\b(what|how|why|when|where|who|is|are|the|a|an)\b", "", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return hashlib.md5(normalized.encode()).hexdigest()[:16]

    def _cache_file(self, question: str) -> Path:
        """Get cache file path for question."""
        return self.cache_dir / f"{self._question_hash(question)}.json"

    def get(self, question: str) -> PerspectiveResult | None:
        """Get cached perspectives for a question."""
        if not settings.perspective_cache_enabled:
            return None

        cache_file = self._cache_file(question)
        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Reconstruct the result
            result = PerspectiveResult(
                question=data["question"],
                picker_model=data.get("picker_model"),
                duration_ms=data.get("duration_ms"),
                from_cache=True,
                perspective_depth=data.get("perspective_depth", 1),
                domain_detected=data.get("domain_detected"),
            )

            result.all_perspectives = [
                Perspective.from_dict(p) for p in data.get("all_perspectives", [])
            ]
            result.selected_perspectives = [
                Perspective.from_dict(p) for p in data.get("selected_perspectives", [])
            ]
            result.blind_spot_perspectives = [
                Perspective.from_dict(p) for p in data.get("blind_spot_perspectives", [])
            ]

            return result

        except (json.JSONDecodeError, KeyError):
            return None

    def set(self, question: str, result: PerspectiveResult) -> None:
        """Cache perspectives for a question."""
        if not settings.perspective_cache_enabled:
            return

        cache_file = self._cache_file(question)

        data = {
            "question": result.question,
            "picker_model": result.picker_model,
            "duration_ms": result.duration_ms,
            "perspective_depth": result.perspective_depth,
            "domain_detected": result.domain_detected,
            "cached_at": datetime.now().isoformat(),
            "all_perspectives": [p.to_dict() for p in result.all_perspectives],
            "selected_perspectives": [p.to_dict() for p in result.selected_perspectives],
            "blind_spot_perspectives": [p.to_dict() for p in result.blind_spot_perspectives],
        }

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def clear(self) -> int:
        """Clear all cached perspectives."""
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
            count += 1
        return count


# =============================================================================
# Domain Detector
# =============================================================================

DOMAIN_KEYWORDS = {
    "business": [
        "startup",
        "company",
        "market",
        "revenue",
        "profit",
        "customer",
        "business",
        "enterprise",
        "sales",
        "growth",
    ],
    "technical": [
        "software",
        "code",
        "algorithm",
        "system",
        "architecture",
        "api",
        "database",
        "performance",
        "security",
        "programming",
    ],
    "research": [
        "study",
        "research",
        "hypothesis",
        "experiment",
        "data",
        "analysis",
        "methodology",
        "evidence",
        "theory",
        "findings",
    ],
    "social": [
        "people",
        "society",
        "culture",
        "behavior",
        "community",
        "relationship",
        "group",
        "social",
        "human",
        "psychological",
    ],
    "philosophical": [
        "meaning",
        "truth",
        "existence",
        "ethics",
        "moral",
        "consciousness",
        "reality",
        "knowledge",
        "belief",
        "value",
    ],
}


def detect_domain(question: str) -> str | None:
    """Detect the most likely domain for a question."""
    question_lower = question.lower()
    scores = {}

    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in question_lower)
        if score > 0:
            scores[domain] = score

    if scores:
        return max(scores, key=scores.get)
    return None


# =============================================================================
# Model-Perspective Matcher
# =============================================================================


def match_model_to_perspective(perspective: Perspective) -> str:
    """Determine the best model to research a perspective."""
    # Check user-configured matching first
    user_matching = settings.get_perspective_model_matching()

    label_lower = perspective.label.lower()

    # Check user config
    for key, model in user_matching.items():
        if key in label_lower:
            return model

    # Check default matching
    for key, model in DEFAULT_MODEL_PERSPECTIVE_MATCHING.items():
        if key in label_lower:
            return model

    # Default to researcher model
    return settings.default_researcher


# =============================================================================
# Perspective Expander (Enhanced)
# =============================================================================


@dataclass
class PerspectiveExpander:
    """
    Enhanced Perspective Expander with:
    - Caching
    - Recursive depth
    - Blind spot detection
    - Model-perspective matching
    - Domain-aware templates

    Usage:
        expander = PerspectiveExpander(
            models=[
                ModelSpec.parse("opus"),
                ModelSpec.parse("gemini:flash"),
                ModelSpec.parse("kimi:kimi"),
            ],
            picker=ModelSpec.parse("sonnet"),
        )
        result = await expander.expand("What makes startups successful?")
    """

    models: list[ModelSpec]
    picker: ModelSpec
    output_dir: Path | None = None
    depth: int = 1  # Perspective depth (1 = flat, 2+ = recursive)
    min_perspectives: int = 5
    max_perspectives: int = 8
    enable_blind_spot_check: bool = True
    enable_caching: bool = True
    enable_model_matching: bool = True
    use_domain_templates: bool = True

    def __post_init__(self):
        self._cache = PerspectiveCache()

    async def _get_perspectives_from_model(
        self,
        question: str,
        model: ModelSpec,
        depth: int = 0,
        parent: Perspective | None = None,
    ) -> tuple[ModelSpec, list[Perspective], str | None]:
        """
        Query a single model for perspectives.

        Returns: (model, perspectives, error)
        """
        logger = get_logger()

        try:
            provider = get_provider_for_model(model)

            # Use sub-perspective prompt if this is a recursive call
            if parent:
                prompt = SUB_PERSPECTIVE_PROMPT.format(
                    QUESTION=question,
                    PARENT_PERSPECTIVE=f"{parent.label} - {parent.description}",
                )
            else:
                prompt = PERSPECTIVE_PROMPT

            options = ProviderOptions(system_prompt=prompt)
            response = await provider.generate(question, model.model, options)

            if not response or not response.strip():
                return model, [], "Empty response"

            # Parse P: lines
            perspectives = []
            for line in response.strip().split("\n"):
                p = Perspective.parse(line, source_model=str(model), depth=depth)
                if p:
                    p.parent = parent
                    perspectives.append(p)

            logger.debug(f"[PerspectiveExpander] {model} returned {len(perspectives)} perspectives")

            return model, perspectives, None

        except Exception as e:
            logger.warning(f"[PerspectiveExpander] {model} failed: {e}")
            return model, [], str(e)

    async def _pick_perspectives(
        self,
        question: str,
        all_perspectives: list[Perspective],
    ) -> list[Perspective]:
        """Use the picker model to select the best perspectives."""
        logger = get_logger()

        # Build perspectives string grouped by source
        perspectives_by_source: dict[str, list[Perspective]] = {}
        for p in all_perspectives:
            source = p.source_model or "unknown"
            if source not in perspectives_by_source:
                perspectives_by_source[source] = []
            perspectives_by_source[source].append(p)

        perspectives_str = ""
        for source, perps in perspectives_by_source.items():
            perspectives_str += f"\n## From {source}:\n"
            for p in perps:
                perspectives_str += f"P: {p}\n"

        # Build prompt with configurable counts
        prompt = PERSPECTIVE_PICKER_PROMPT.format(
            QUESTION=question,
            PERSPECTIVES=perspectives_str,
            MIN_COUNT=self.min_perspectives,
            MAX_COUNT=self.max_perspectives,
        )

        provider = get_provider_for_model(self.picker)
        response = await provider.generate(
            "Select the best perspectives.",
            self.picker.model,
            ProviderOptions(system_prompt=prompt),
        )

        if not response or not response.strip():
            logger.warning("[PerspectiveExpander] Picker returned empty response")
            return all_perspectives[: self.max_perspectives]

        # Parse selected perspectives
        selected = []
        for line in response.strip().split("\n"):
            p = Perspective.parse(line, source_model=str(self.picker))
            if p:
                p.selected = True
                # Try to extract selection reason from parentheses
                if "(" in p.description and p.description.endswith(")"):
                    parts = p.description.rsplit("(", 1)
                    p.description = parts[0].strip()
                    p.selection_reason = parts[1].rstrip(")")
                selected.append(p)

        logger.debug(f"[PerspectiveExpander] Picker selected {len(selected)} perspectives")

        return selected

    async def _detect_blind_spots(
        self,
        question: str,
        selected: list[Perspective],
    ) -> list[Perspective]:
        """Run blind spot detection to find missing perspectives."""
        logger = get_logger()

        if not self.enable_blind_spot_check:
            return []

        perspectives_str = "\n".join(f"- {p.label}: {p.description}" for p in selected)

        prompt = BLIND_SPOT_PROMPT.format(
            QUESTION=question,
            PERSPECTIVES=perspectives_str,
        )

        provider = get_provider_for_model(self.picker)
        response = await provider.generate(
            "Detect blind spots in the perspective set.",
            self.picker.model,
            ProviderOptions(system_prompt=prompt),
        )

        if not response or "NO_BLIND_SPOTS_DETECTED" in response:
            logger.debug("[PerspectiveExpander] No blind spots detected")
            return []

        # Parse blind spot perspectives
        blind_spots = []
        for line in response.strip().split("\n"):
            p = Perspective.parse(line, source_model=str(self.picker))
            if p:
                p.from_blind_spot = True
                p.selected = True
                blind_spots.append(p)

        logger.info(f"[PerspectiveExpander] Detected {len(blind_spots)} blind spot perspectives")

        return blind_spots

    async def _expand_perspective_depth(
        self,
        question: str,
        perspectives: list[Perspective],
        current_depth: int,
    ) -> list[Perspective]:
        """Recursively expand perspectives to the configured depth."""
        if current_depth >= self.depth:
            return perspectives

        logger = get_logger()
        logger.debug(f"[PerspectiveExpander] Expanding perspectives at depth {current_depth + 1}")

        expanded = []
        for p in perspectives:
            # Get sub-perspectives for this perspective
            tasks = [
                self._get_perspectives_from_model(
                    question,
                    model,
                    depth=current_depth + 1,
                    parent=p,
                )
                for model in self.models[:2]  # Use fewer models for sub-perspectives
            ]
            results = await asyncio.gather(*tasks, return_exceptions=False)

            for model, children, error in results:
                if children:
                    p.children.extend(children)

            expanded.append(p)

        return expanded

    def _add_domain_templates(
        self,
        question: str,
        perspectives: list[Perspective],
    ) -> list[Perspective]:
        """Add domain-specific template perspectives if missing."""
        if not self.use_domain_templates:
            return perspectives

        domain = detect_domain(question)
        if not domain or domain not in PERSPECTIVE_LIBRARY:
            return perspectives

        templates = PERSPECTIVE_LIBRARY[domain]
        existing_labels = {p.label.lower() for p in perspectives}

        added = []
        for label, description in templates:
            if label.lower() not in existing_labels:
                p = Perspective(
                    label=label,
                    description=description,
                    source_model="template",
                )
                added.append(p)

        return perspectives + added

    def _assign_model_matching(self, perspectives: list[Perspective]) -> None:
        """Assign best-fit models to each perspective."""
        if not self.enable_model_matching:
            return

        for p in perspectives:
            p.matched_model = match_model_to_perspective(p)

    def _write_output_file(self, result: PerspectiveResult) -> Path | None:
        """Write perspective expansion results to file."""
        if not self.output_dir:
            return None

        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_file = self.output_dir / "PERSPECTIVES.md"

        content = f"""# Perspective Expansion: {result.question}

> Generated {datetime.now().strftime("%Y-%m-%d %H:%M")} | \
Models: {len(self.models)} | Picker: {result.picker_model} | \
Depth: {result.perspective_depth}{" | FROM CACHE" if result.from_cache else ""}

"""
        if result.domain_detected:
            content += f"> Domain Detected: {result.domain_detected}\n"

        content += "\n---\n\n## Selected Perspectives\n\n"

        for i, p in enumerate(result.selected_perspectives, 1):
            content += f"### {i}. {p.label}\n\n"
            content += f"{p.description}\n\n"
            if p.selection_reason:
                content += f"*Selection reason: {p.selection_reason}*\n\n"
            if p.matched_model:
                content += f"*Matched model: {p.matched_model}*\n\n"

            # Add children if any
            if p.children:
                content += "**Sub-perspectives:**\n"
                for child in p.children:
                    content += f"- {child.label}: {child.description}\n"
                content += "\n"

        if result.blind_spot_perspectives:
            content += "\n---\n\n## Blind Spot Perspectives (Discovered)\n\n"
            for i, p in enumerate(result.blind_spot_perspectives, 1):
                content += f"### {i}. {p.label}\n\n"
                content += f"{p.description}\n\n"
                if p.matched_model:
                    content += f"*Matched model: {p.matched_model}*\n\n"

        content += "\n---\n\n## All Gathered Perspectives\n\n"

        for model_str, perspectives in result.model_contributions.items():
            content += f"### From {model_str} ({len(perspectives)} perspectives)\n\n"
            for p in perspectives:
                content += f"- **{p.label}**: {p.description}\n"
            content += "\n"

        output_file.write_text(content, encoding="utf-8")
        return output_file

    async def expand(self, question: str) -> PerspectiveResult:
        """
        Expand the question into multiple perspectives.

        Process:
        1. Check cache for similar questions
        2. Query all models in parallel for perspectives
        3. Add domain-specific templates if applicable
        4. Use picker model to select the best ones
        5. Run blind spot detection
        6. Recursively expand to configured depth
        7. Assign model matching
        8. Cache results

        Returns:
            PerspectiveResult with all and selected perspectives
        """
        logger = get_logger()
        start_time = datetime.now()

        # Check cache first
        if self.enable_caching:
            cached = self._cache.get(question)
            if cached:
                logger.info("[PerspectiveExpander] Using cached perspectives")
                if self.output_dir:
                    self._write_output_file(cached)
                return cached

        logger.info(
            f"[PerspectiveExpander] Starting expansion with {len(self.models)} models, "
            f"depth={self.depth}"
        )

        # Detect domain
        domain = detect_domain(question)
        if domain:
            logger.debug(f"[PerspectiveExpander] Detected domain: {domain}")

        # Phase 1: Query all models in parallel
        tasks = [
            self._get_perspectives_from_model(question, model, depth=0) for model in self.models
        ]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        # Collect all perspectives
        all_perspectives: list[Perspective] = []
        model_contributions: dict[str, list[Perspective]] = {}

        for model, perspectives, error in results:
            model_str = str(model)
            model_contributions[model_str] = perspectives
            if perspectives:
                all_perspectives.extend(perspectives)
            if error:
                logger.warning(f"[PerspectiveExpander] {model_str}: {error}")

        logger.info(f"[PerspectiveExpander] Gathered {len(all_perspectives)} total perspectives")

        # Add domain templates
        all_perspectives = self._add_domain_templates(question, all_perspectives)

        if not all_perspectives:
            raise AgentError(
                "No perspectives gathered from any model",
                agent_id="perspective-expander",
                question=question,
            )

        # Phase 2: Pick the best perspectives
        selected = await self._pick_perspectives(question, all_perspectives)

        # Phase 3: Blind spot detection
        blind_spots = await self._detect_blind_spots(question, selected)

        # Phase 4: Recursive expansion if depth > 1
        if self.depth > 1:
            selected = await self._expand_perspective_depth(question, selected, 1)
            if blind_spots:
                blind_spots = await self._expand_perspective_depth(question, blind_spots, 1)

        # Phase 5: Model matching
        self._assign_model_matching(selected)
        self._assign_model_matching(blind_spots)

        end_time = datetime.now()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        result = PerspectiveResult(
            question=question,
            all_perspectives=all_perspectives,
            selected_perspectives=selected,
            blind_spot_perspectives=blind_spots,
            model_contributions=model_contributions,
            picker_model=str(self.picker),
            duration_ms=duration_ms,
            from_cache=False,
            perspective_depth=self.depth,
            domain_detected=domain,
        )

        # Cache the result
        if self.enable_caching:
            self._cache.set(question, result)

        # Write output file
        output_file = self._write_output_file(result)
        if output_file:
            logger.info(f"[PerspectiveExpander] Output written to {output_file}")

        total_selected = len(selected) + len(blind_spots)
        logger.info(
            f"[PerspectiveExpander] Complete: {total_selected} perspectives selected "
            f"({len(blind_spots)} from blind spots) from {len(all_perspectives)} total "
            f"in {duration_ms}ms"
        )

        return result

    def perspectives_to_research_config(
        self,
        question: str,
        perspectives: list[Perspective],
    ) -> list[tuple[str, ModelSpec | None]]:
        """
        Convert perspectives into research questions with optional model assignments.

        Returns list of (framed_question, matched_model) tuples.
        """
        result = []
        for p in perspectives:
            framed_q = f"[{p.label}] {question}\n\nAnalyze from this perspective: {p.description}"
            matched = ModelSpec.parse(p.matched_model) if p.matched_model else None
            result.append((framed_q, matched))
        return result


# =============================================================================
# Factory Functions
# =============================================================================


def create_default_expander(
    output_dir: Path | None = None,
) -> PerspectiveExpander:
    """
    Create a default perspective expander using settings.

    Uses settings for:
    - perspective_models
    - perspective_picker
    - perspective_depth
    - perspective_min_count
    - perspective_max_count
    - perspective_blind_spot_check
    - perspective_cache_enabled
    """
    models = [ModelSpec.parse(m) for m in settings.get_perspective_models_list()]
    picker = ModelSpec.parse(settings.perspective_picker)

    return PerspectiveExpander(
        models=models,
        picker=picker,
        output_dir=output_dir,
        depth=settings.perspective_depth,
        min_perspectives=settings.perspective_min_count,
        max_perspectives=settings.perspective_max_count,
        enable_blind_spot_check=settings.perspective_blind_spot_check,
        enable_caching=settings.perspective_cache_enabled,
    )


def create_all_models_expander(
    output_dir: Path | None = None,
) -> PerspectiveExpander:
    """
    Create an expander that uses all available models.

    Uses every provider to maximize perspective diversity.
    """
    return PerspectiveExpander(
        models=[
            ModelSpec.parse("opus"),
            ModelSpec.parse("sonnet"),
            ModelSpec.parse("haiku"),
            ModelSpec.parse("gemini:pro"),
            ModelSpec.parse("gemini:flash"),
            ModelSpec.parse("kimi:kimi"),
            ModelSpec.parse("openrouter:grok"),
        ],
        picker=ModelSpec.parse("sonnet"),
        output_dir=output_dir,
        depth=settings.perspective_depth,
        min_perspectives=settings.perspective_min_count,
        max_perspectives=settings.perspective_max_count,
        enable_blind_spot_check=settings.perspective_blind_spot_check,
        enable_caching=settings.perspective_cache_enabled,
    )


def get_perspective_cache() -> PerspectiveCache:
    """Get the perspective cache instance."""
    return PerspectiveCache()
