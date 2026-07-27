"""
Orchestrator - manages parallel agent execution.

The core of deep-research: spawns agents, manages concurrency, collects results.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

from .exceptions import (
    AgentError,
    APIRateLimitError,
    APITimeoutError,
    ChildFailureError,
    DeepResearchError,
    EmptyResponseError,
    ProviderError,
)
from .logging import ResearchLogger, init_logger
from .models import (
    AgentConfig,
    AgentState,
    AgentStatus,
    ExplorationResult,
    ModelSpec,
    ResearchConfig,
)
from .providers import get_provider_for_model
from .recipes.perspective import (
    PerspectiveExpander,
    PerspectiveResult,
    create_all_models_expander,
    create_default_expander,
)
from .validation import validate_research_config

# Default retry settings
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0  # seconds
RETRY_BACKOFF_MULTIPLIER = 2.0


@dataclass
class Orchestrator:
    """
    Manages the recursive research process.

    Handles:
    - Agent numbering and tracking
    - Parallel execution with concurrency limits
    - Result collection and synthesis
    - Agent file output
    - Error handling with retries
    """

    config: ResearchConfig
    max_retries: int = DEFAULT_MAX_RETRIES
    retry_delay: float = DEFAULT_RETRY_DELAY
    continue_on_child_failure: bool = True  # Don't crash entire tree on child failure

    _counter: int = field(default=0, init=False)
    _agents: dict[str, AgentState] = field(default_factory=dict, init=False)
    _semaphore: asyncio.Semaphore = field(init=False)
    _logger: ResearchLogger = field(init=False)
    _perspective_result: PerspectiveResult | None = field(default=None, init=False)

    def __post_init__(self):
        self._semaphore = asyncio.Semaphore(self.config.max_parallel)
        # Ensure output directories exist
        self.agents_dir.mkdir(parents=True, exist_ok=True)
        # Initialize logger
        self._logger = init_logger(
            output_dir=self.config.output_dir,
            verbose=False,
        )

    @property
    def use_perspective_expansion(self) -> bool:
        """Check if perspective expansion is enabled."""
        return bool(self.config.perspective_models) or self.config.use_all_perspective_models

    def _create_perspective_expander(self) -> PerspectiveExpander:
        """Create the perspective expander based on config."""
        if self.config.use_all_perspective_models:
            expander = create_all_models_expander(output_dir=self.config.output_dir)
            # Apply config overrides
            expander.depth = self.config.perspective_depth
            expander.enable_blind_spot_check = self.config.perspective_enable_blind_spot
            expander.enable_caching = self.config.perspective_enable_cache
        elif self.config.perspective_models:
            picker = self.config.perspective_picker or ModelSpec.parse("sonnet")
            expander = PerspectiveExpander(
                models=self.config.perspective_models,
                picker=picker,
                output_dir=self.config.output_dir,
                depth=self.config.perspective_depth,
                enable_blind_spot_check=self.config.perspective_enable_blind_spot,
                enable_caching=self.config.perspective_enable_cache,
            )
        else:
            expander = create_default_expander(output_dir=self.config.output_dir)
            # Apply config overrides
            expander.depth = self.config.perspective_depth
            expander.enable_blind_spot_check = self.config.perspective_enable_blind_spot
            expander.enable_caching = self.config.perspective_enable_cache

        return expander

    async def _run_perspective_expansion(self) -> PerspectiveResult:
        """Run perspective expansion as the first phase."""
        self._logger.info("[Orchestrator] Running perspective expansion...")

        expander = self._create_perspective_expander()
        result = await expander.expand(self.config.question)

        self._perspective_result = result

        self._logger.info(
            f"[Orchestrator] Perspective expansion complete: "
            f"{len(result.selected_perspectives)} perspectives selected"
        )

        return result

    @property
    def agents_dir(self) -> Path:
        return self.config.output_dir / "agents"

    def _next_agent_num(self) -> int:
        """Get next agent number (thread-safe via GIL)."""
        self._counter += 1
        return self._counter

    def _create_agent_config(
        self,
        question: str,
        model: ModelSpec,
        depth: int,
    ) -> AgentConfig:
        """Create configuration for a new agent."""
        return AgentConfig(
            question=question,
            model=model,
            depth=depth,
            max_depth=self.config.max_depth,
            agent_num=self._next_agent_num(),
        )

    def _write_agent_file(self, state: AgentState) -> None:
        """Write agent state to markdown file."""
        config = state.config
        agent_file = self.agents_dir / f"{config.agent_id}-{config.model.model}.md"

        content = f"""# Agent {config.agent_id} ({config.model})
**Status: {state.status.value.upper()}**

## Question
{config.question}
"""

        if state.exploration_output:
            content += f"""
## Exploration
{state.exploration_output}
"""

        if state.child_results:
            content += "\n## Children Results\n"
            for i, (q, r) in enumerate(zip(state.child_questions, state.child_results), 1):
                content += f"""
### Research {i}: {q}

{r}

---
"""

        if state.synthesis:
            content += f"""
## Synthesis
{state.synthesis}
"""

        if state.response:
            content += f"""
## Response
{state.response}
"""

        if state.error:
            content += f"""
## Error
{state.error}
"""

        try:
            agent_file.write_text(content, encoding="utf-8")
        except IOError as e:
            self._logger.warning(f"Failed to write agent file: {e}")

    async def _retry_with_backoff(
        self,
        operation: str,
        func: Callable,
        *args,
        **kwargs,
    ) -> str:
        """
        Execute a function with exponential backoff retry.

        Args:
            operation: Name of operation for logging
            func: Async function to call
            *args, **kwargs: Arguments for func

        Returns:
            Result from func

        Raises:
            The last exception if all retries fail
        """
        last_error: Exception | None = None
        delay = self.retry_delay

        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except APITimeoutError as e:
                last_error = e
                self._logger.warning(
                    f"{operation} timed out (attempt {attempt + 1}/{self.max_retries})"
                )
            except APIRateLimitError as e:
                last_error = e
                # Use retry_after if provided
                wait_time = e.retry_after or delay
                self._logger.warning(
                    f"{operation} rate limited, waiting {wait_time}s "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )
                await asyncio.sleep(wait_time)
                continue
            except ProviderError:
                # Don't retry non-transient provider errors
                raise

            if attempt < self.max_retries - 1:
                self._logger.debug(f"Retrying {operation} in {delay}s...")
                await asyncio.sleep(delay)
                delay *= RETRY_BACKOFF_MULTIPLIER

        # All retries exhausted
        if last_error:
            raise last_error
        raise RuntimeError(f"Retry logic error for {operation}")

    async def _process_leaf(self, state: AgentState) -> str:
        """Process a leaf agent (answers directly)."""
        config = state.config
        state.status = AgentStatus.ANSWERING
        self._write_agent_file(state)

        self._logger.agent_answering(config.agent_id)

        # Check for ensemble mode
        leaf_models = self.config.leaf_models or [config.model]

        if len(leaf_models) == 1:
            # Single model - direct answer
            model = leaf_models[0]
            provider = get_provider_for_model(model)

            response = await self._retry_with_backoff(
                f"answer ({model})",
                provider.answer,
                config.question,
                model.model,
            )

            if not response or not response.strip():
                raise EmptyResponseError(
                    provider.name,
                    model.model,
                    config.question,
                )

            state.response = response
        else:
            # Ensemble mode - multiple models answer, then merge
            self._logger.agent_ensemble(config.agent_id, len(leaf_models))

            # Run all models in parallel
            async def get_model_response(
                model: ModelSpec,
            ) -> tuple[ModelSpec, str | None, str | None]:
                """Get response from a model, return (model, response, error)."""
                try:
                    provider = get_provider_for_model(model)
                    resp = await self._retry_with_backoff(
                        f"ensemble answer ({model})",
                        provider.answer,
                        config.question,
                        model.model,
                    )
                    return model, resp, None
                except Exception as e:
                    self._logger.warning(f"Ensemble model {model} failed: {e}")
                    return model, None, str(e)

            results = await asyncio.gather(
                *[get_model_response(m) for m in leaf_models],
                return_exceptions=False,
            )

            # Build responses string, skipping failed models
            responses_str = ""
            successful_count = 0
            for model, resp, error in results:
                if resp and resp.strip():
                    responses_str += f"\n### Response from {model}:\n{resp}\n"
                    successful_count += 1
                elif error:
                    responses_str += f"\n### Response from {model}:\n[ERROR: {error}]\n"

            if successful_count == 0:
                raise AgentError(
                    "All ensemble models failed",
                    config.agent_id,
                    config.question,
                )

            # Merge using merger model
            merger = self.config.merger or self.config.orchestrator
            provider = get_provider_for_model(merger)
            response = await self._retry_with_backoff(
                f"merge ({merger})",
                provider.merge,
                config.question,
                responses_str,
                merger.model,
            )
            state.response = response

        state.status = AgentStatus.COMPLETE
        state.end_time = datetime.now()
        self._write_agent_file(state)

        self._logger.agent_complete(config.agent_id, state.duration_ms)
        return state.response

    async def _process_explorer(self, state: AgentState) -> str:
        """Process an explorer agent (spawns children, synthesizes)."""
        config = state.config
        provider = get_provider_for_model(config.model)

        # Phase 1: Explore
        state.status = AgentStatus.EXPLORING
        self._write_agent_file(state)

        self._logger.agent_exploring(config.agent_id)

        exploration_output = await self._retry_with_backoff(
            f"explore ({config.model})",
            provider.explore,
            config.question,
            config.model.model,
        )
        state.exploration_output = exploration_output

        # Parse Q: lines
        result = ExplorationResult.from_output(exploration_output)
        questions = [q.question for q in result.questions]

        self._logger.agent_found_questions(config.agent_id, len(questions))

        if not questions:
            # No sub-questions - treat as leaf
            state.response = exploration_output
            state.status = AgentStatus.COMPLETE
            state.end_time = datetime.now()
            self._write_agent_file(state)
            self._logger.agent_complete(config.agent_id, state.duration_ms)
            return exploration_output

        state.child_questions = questions
        state.status = AgentStatus.WAITING_FOR_CHILDREN
        self._write_agent_file(state)

        # Phase 2: Spawn children (parallel with concurrency limit)
        self._logger.agent_spawning(config.agent_id, len(questions), self.config.max_parallel)

        async def process_child(q: str, idx: int) -> tuple[str, str | None, str | None]:
            """Process a child, returning (question, result, error)."""
            self._logger.agent_child_start(config.agent_id, idx + 1, len(questions), q)
            try:
                async with self._semaphore:
                    result = await self.process_question(
                        question=q,
                        model=self.config.researcher,
                        depth=config.depth + 1,
                    )
                    return q, result, None
            except Exception as e:
                if self.continue_on_child_failure:
                    self._logger.warning(f"Child {idx + 1} failed, continuing: {e}")
                    return q, None, str(e)
                else:
                    raise

        child_tasks = [process_child(q, i) for i, q in enumerate(questions)]
        child_results = await asyncio.gather(*child_tasks, return_exceptions=False)

        # Process results, tracking failures
        successful_results: list[str] = []
        failed_children: list[str] = []

        for q, result, error in child_results:
            if result is not None:
                state.child_results.append(result)
                successful_results.append(result)
            else:
                state.child_results.append(f"[FAILED: {error}]")
                failed_children.append(q[:50])

        if failed_children:
            self._logger.warning(
                f"[{config.agent_id}] {len(failed_children)}/{len(questions)} children failed"
            )

        # Check if we have enough results to synthesize
        if not successful_results:
            raise ChildFailureError(
                "All child agents failed",
                config.agent_id,
                failed_children,
                len(questions),
            )

        self._logger.agent_children_complete(config.agent_id)

        # Phase 3: Synthesize
        state.status = AgentStatus.SYNTHESIZING
        self._write_agent_file(state)

        self._logger.agent_synthesizing(config.agent_id)

        # Build results string
        results_str = ""
        for i, (q, r) in enumerate(zip(questions, state.child_results), 1):
            results_str += f"\n### Research {i}: {q}\n\n{r}\n\n---"

        # Build full research output (like bash script did)
        # This preserves ALL content - exploration reasoning + children answers
        full_output = f"""## Exploration

{state.exploration_output}

## Research Findings

{results_str}
"""

        # Only synthesize if explicitly requested (future: --summarize flag)
        # For now, skip the extra synthesis call - the exploration already contains
        # the orchestrator's reasoning and the children contain the answers
        state.synthesis = None  # No separate synthesis
        state.status = AgentStatus.COMPLETE
        state.end_time = datetime.now()
        self._write_agent_file(state)

        self._logger.agent_complete(config.agent_id, state.duration_ms)
        return full_output

    async def process_question(
        self,
        question: str,
        model: ModelSpec,
        depth: int = 0,
    ) -> str:
        """
        Process a question recursively.

        If at leaf depth, answers directly.
        Otherwise, explores for angles, spawns children, synthesizes.
        """
        config = self._create_agent_config(question, model, depth)
        state = AgentState(config=config, start_time=datetime.now())
        self._agents[config.agent_id] = state

        self._logger.agent_start(
            config.agent_id,
            question,
            str(model),
            depth,
        )

        try:
            if config.is_leaf:
                return await self._process_leaf(state)
            else:
                return await self._process_explorer(state)
        except (KeyboardInterrupt, asyncio.CancelledError):
            # Don't catch interrupts - let them propagate
            state.status = AgentStatus.FAILED
            state.error = "Cancelled"
            state.end_time = datetime.now()
            self._write_agent_file(state)
            raise
        except DeepResearchError as e:
            # Our custom errors - log and propagate
            state.status = AgentStatus.FAILED
            state.error = str(e)
            state.end_time = datetime.now()
            self._write_agent_file(state)
            self._logger.agent_failed(config.agent_id, str(e), question)
            raise
        except Exception as e:
            # Unexpected errors - wrap in AgentError
            state.status = AgentStatus.FAILED
            state.error = f"{type(e).__name__}: {str(e)}"
            state.end_time = datetime.now()
            self._write_agent_file(state)
            self._logger.agent_failed(config.agent_id, str(e), question)
            raise AgentError(str(e), config.agent_id, question, e)

    async def _run_with_perspectives(self) -> str:
        """
        Run research with perspective expansion as the first phase.

        1. Run perspective expansion to get diverse viewpoints
        2. Use selected perspectives as initial exploration angles
        3. Research each perspective in parallel
        4. Synthesize all perspective research into final answer
        """
        # Phase 1: Perspective expansion
        perspective_result = await self._run_perspective_expansion()

        if not perspective_result.selected_perspectives:
            self._logger.warning(
                "[Orchestrator] No perspectives selected, falling back to standard research"
            )
            return await self.process_question(
                question=self.config.question,
                model=self.config.orchestrator,
                depth=0,
            )

        # Phase 2: Research each perspective in parallel
        self._logger.info(
            f"[Orchestrator] Researching {len(perspective_result.selected_perspectives)} perspectives..."
        )

        # Create the orchestrator state for tracking
        config = self._create_agent_config(
            self.config.question,
            self.config.orchestrator,
            depth=0,
        )
        state = AgentState(config=config, start_time=datetime.now())
        self._agents[config.agent_id] = state

        # Build exploration output from perspectives (including blind spots)
        all_perspectives = perspective_result.get_all_selected()
        exploration_lines = ["# Perspectives identified:\n"]
        for p in all_perspectives:
            blind_spot_marker = " [BLIND SPOT]" if p.from_blind_spot else ""
            model_info = f" (model: {p.matched_model})" if p.matched_model else ""
            exploration_lines.append(
                f"Q: [{p.label}{blind_spot_marker}] {self.config.question} - Focus on: {p.description}{model_info}"
            )

        state.exploration_output = "\n".join(exploration_lines)
        state.status = AgentStatus.WAITING_FOR_CHILDREN

        # Extract questions from perspectives (all_perspectives already includes blind spots)
        questions = []
        perspective_models: list[ModelSpec] = []

        for p in all_perspectives:
            framed_q = (
                f"[{p.label}] {self.config.question}\n\n"
                f"Analyze from this perspective: {p.description}"
            )
            questions.append(framed_q)
            # Use matched model if available, otherwise default researcher
            if p.matched_model:
                perspective_models.append(ModelSpec.parse(p.matched_model))
            else:
                perspective_models.append(self.config.researcher)

        state.child_questions = questions
        self._write_agent_file(state)

        self._logger.agent_spawning(config.agent_id, len(questions), self.config.max_parallel)

        # Spawn child researchers for each perspective using matched models
        async def process_perspective(
            q: str, model: ModelSpec, idx: int
        ) -> tuple[str, str | None, str | None]:
            """Process a perspective research, returning (question, result, error)."""
            self._logger.agent_child_start(config.agent_id, idx + 1, len(questions), q[:80] + "...")
            try:
                async with self._semaphore:
                    result = await self.process_question(
                        question=q,
                        model=model,  # Use matched model for this perspective
                        depth=1,  # Perspectives are at depth 1
                    )
                    return q, result, None
            except Exception as e:
                if self.continue_on_child_failure:
                    self._logger.warning(f"Perspective research {idx + 1} failed: {e}")
                    return q, None, str(e)
                else:
                    raise

        child_tasks = [
            process_perspective(q, m, i)
            for i, (q, m) in enumerate(zip(questions, perspective_models))
        ]
        child_results = await asyncio.gather(*child_tasks, return_exceptions=False)

        # Collect results
        successful_results: list[str] = []
        for q, result, error in child_results:
            if result is not None:
                state.child_results.append(result)
                successful_results.append(result)
            else:
                state.child_results.append(f"[FAILED: {error}]")

        if not successful_results:
            raise AgentError(
                "All perspective research failed",
                config.agent_id,
                self.config.question,
            )

        self._logger.agent_children_complete(config.agent_id)

        # Phase 3: Synthesize all perspective research
        state.status = AgentStatus.SYNTHESIZING
        self._write_agent_file(state)

        self._logger.agent_synthesizing(config.agent_id)

        # Build results string with perspective labels
        results_str = ""
        for i, (q, r) in enumerate(zip(questions, state.child_results), 1):
            # Extract perspective label from all_perspectives (includes blind spots)
            if i <= len(all_perspectives):
                p = all_perspectives[i - 1]
                perspective_label = p.label
                if p.from_blind_spot:
                    perspective_label += " (blind spot)"
            else:
                perspective_label = f"Perspective {i}"
            results_str += f"\n### {perspective_label}\n\n{r}\n\n---"

        # Build full research output (preserves all content)
        full_output = f"""## Perspectives Explored

{chr(10).join(f"- **{p.label}**" + (" (blind spot)" if p.from_blind_spot else "") for p in all_perspectives)}

## Research Findings

{results_str}
"""

        # Skip extra synthesis call - return full research instead
        state.synthesis = None
        state.status = AgentStatus.COMPLETE
        state.end_time = datetime.now()
        self._write_agent_file(state)

        self._logger.agent_complete(config.agent_id, state.duration_ms)

        return full_output

    async def run(self) -> str:
        """
        Run the full research process.

        Returns the final synthesis.
        """
        # Validate config before starting
        warnings = validate_research_config(self.config)
        for warning in warnings:
            self._logger.warning(warning)

        # Build perspective info for logging
        perspective_info = None
        if self.use_perspective_expansion:
            if self.config.use_all_perspective_models:
                perspective_info = "all models"
            elif self.config.perspective_models:
                perspective_info = ", ".join(str(m) for m in self.config.perspective_models)

        # Log research start
        self._logger.research_start(
            question=self.config.question,
            orchestrator=str(self.config.orchestrator),
            researcher=str(self.config.researcher),
            max_depth=self.config.max_depth,
            max_parallel=self.config.max_parallel,
            output_dir=self.config.output_dir,
            leaf_models=[str(m) for m in self.config.leaf_models]
            if self.config.leaf_models
            else None,
        )

        if perspective_info:
            self._logger.info(f"[Orchestrator] Perspective expansion enabled: {perspective_info}")

        try:
            # Choose research mode based on perspective expansion
            if self.use_perspective_expansion:
                result = await self._run_with_perspectives()
            else:
                result = await self.process_question(
                    question=self.config.question,
                    model=self.config.orchestrator,
                    depth=0,
                )

            # No separate RESEARCH.md - the orchestrator agent file IS the output
            # Find the orchestrator agent file (d0-001-*.md)
            orchestrator_file = self.agents_dir / f"d0-001-{self.config.orchestrator.model}.md"

            # Log completion and write metrics
            self._logger.research_complete(orchestrator_file, self.agents_dir)
            self._logger.write_metrics_file()

            return result

        except Exception as e:
            self._logger.error(f"Research failed: {e}", exc_info=True)
            self._logger.write_metrics_file()
            raise
