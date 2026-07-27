"""
MasterChef - The intelligent research orchestrator.

The MasterChef executes strategies on knowledge graphs by:
- Interpreting strategy phases
- Selecting nodes based on phase criteria
- Executing operations (with parallelism)
- Managing checkpoints
- Checking goal completion
- Handling stalls and errors

The MasterChef is the "cook" that uses the "cookbook" (strategy)
to transform raw "ingredients" (questions) into "dishes" (syntheses).
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from .graph import KnowledgeGraph
from .node import Node, NodeRelation, NodeType, question
from .operation import (
    OperationRegistry,
    OperationResult,
    OperationType,
)
from .strategy import (
    Goal,
    Phase,
    PhaseType,
    Strategy,
    StrategyRegistry,
)

logger = logging.getLogger(__name__)


@dataclass
class ExecutionStats:
    """Statistics about strategy execution."""

    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    phases_completed: int = 0
    operations_executed: int = 0
    nodes_created: int = 0
    nodes_modified: int = 0
    errors: list[str] = field(default_factory=list)
    stall_count: int = 0

    @property
    def duration_seconds(self) -> float:
        """Get execution duration in seconds."""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()


@dataclass
class PhaseResult:
    """Result of executing a phase."""

    phase_name: str
    success: bool
    nodes_affected: int = 0
    operations_executed: int = 0
    created_nodes: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    duration_ms: int = 0


@dataclass
class ExecutionResult:
    """Result of executing a strategy."""

    success: bool
    graph: KnowledgeGraph
    stats: ExecutionStats
    phase_results: list[PhaseResult] = field(default_factory=list)
    goals_met: list[str] = field(default_factory=list)
    final_synthesis: Node | None = None


class MasterChef:
    """The intelligent research orchestrator.

    The MasterChef executes strategies by interpreting phases,
    selecting nodes, executing operations, and managing the
    research process.
    """

    def __init__(
        self,
        output_dir: Path | None = None,
        max_parallel: int = 10,
        on_progress: Callable[[str, dict[str, Any]], None] | None = None,
    ):
        """Initialize the MasterChef.

        Args:
            output_dir: Directory for output and checkpoints
            max_parallel: Maximum parallel operations
            on_progress: Callback for progress updates
        """
        self.output_dir = output_dir
        self.max_parallel = max_parallel
        self.on_progress = on_progress

        # Ensure registrations
        self._ensure_registrations()

        # Registries
        self._operation_registry = OperationRegistry.instance()
        self._strategy_registry = StrategyRegistry.instance()

        # Execution state
        self._current_graph: KnowledgeGraph | None = None
        self._current_strategy: Strategy | None = None
        self._stats: ExecutionStats | None = None

    _registrations_done: bool = False

    @classmethod
    def _ensure_registrations(cls) -> None:
        """Ensure operations and strategies are registered (once)."""
        if cls._registrations_done:
            return

        # Register built-in strategies
        from .strategy import register_builtin_strategies

        register_builtin_strategies()

        # Register operations
        try:
            from .operations.base import register_all_operations

            register_all_operations()
        except ImportError:
            # Operations module not yet available
            logger.warning("Operations module not found - using mock operations")

        cls._registrations_done = True

    # =========================================================================
    # Main Execution
    # =========================================================================

    async def cook(
        self,
        question_text: str,
        strategy: Strategy | str,
        context: dict[str, Any] | None = None,
    ) -> ExecutionResult:
        """Execute a research strategy on a question.

        This is the main entry point for research. It:
        1. Initializes the graph with the root question
        2. Executes strategy phases in order
        3. Checks goal completion
        4. Returns the final result

        Args:
            question_text: The research question
            strategy: Strategy object or name to load from registry
            context: Additional context (models, config, etc.)

        Returns:
            ExecutionResult with the completed graph
        """
        # Resolve strategy
        if isinstance(strategy, str):
            resolved = self._strategy_registry.get(strategy)
            if not resolved:
                return ExecutionResult(
                    success=False,
                    graph=KnowledgeGraph(question_text, self.output_dir),
                    stats=ExecutionStats(),
                    phase_results=[],
                )
            strategy = resolved

        # Initialize
        self._current_strategy = strategy
        self._stats = ExecutionStats()
        self._current_graph = KnowledgeGraph(
            question=question_text,
            output_dir=self.output_dir,
            strategy=strategy.metadata.name,
        )

        # Add root question
        root = question(question_text, depth=0)
        self._current_graph.add(root)

        context = context or {}
        context["max_parallel"] = self.max_parallel

        self._emit_progress(
            "started",
            {
                "strategy": strategy.metadata.name,
                "question": question_text,
            },
        )

        # Execute phases
        phase_results: list[PhaseResult] = []
        iteration = 0
        stall_counter = 0
        last_node_count = 1

        while iteration < strategy.max_iterations:
            iteration += 1

            # Check early termination
            if strategy.early_termination:
                stats = self._current_graph.stats()
                if strategy.early_termination.matches(stats):
                    self._emit_progress("early_termination", stats)
                    break

            # Check goals
            goals_met = self._check_goals(strategy.goals)
            if all(g in goals_met for g in [goal.goal_type.value for goal in strategy.goals]):
                self._emit_progress("goals_met", {"goals": goals_met})
                break

            # Execute each phase
            made_progress = False
            for phase in strategy.phases:
                # Check skip condition
                if phase.skip_if:
                    stats = self._current_graph.stats()
                    if phase.skip_if.matches(stats):
                        continue

                result = await self._execute_phase(phase, context)
                phase_results.append(result)
                self._stats.phases_completed += 1

                if result.success and result.nodes_affected > 0:
                    made_progress = True

                # Checkpoint after phase if configured
                if strategy.checkpoint_after_phases:
                    self._current_graph.checkpoint(phase.name)

                # Handle phase errors
                if not result.success and not phase.continue_on_error:
                    self._stats.errors.append(f"Phase {phase.name} failed: {result.errors}")
                    if strategy.on_error:
                        # TODO: Execute error recovery strategy
                        pass

            # Stall detection
            current_count = len(self._current_graph)
            if current_count == last_node_count and not made_progress:
                stall_counter += 1
                if stall_counter >= strategy.stall_detection:
                    self._emit_progress("stalled", {"iterations": stall_counter})
                    if strategy.on_stall:
                        # TODO: Execute stall recovery strategy
                        pass
                    break
            else:
                stall_counter = 0
                last_node_count = current_count

        # Finalize
        self._stats.end_time = datetime.now()

        # Find final synthesis
        syntheses = self._current_graph.by_type(NodeType.SYNTHESIS)
        final_synthesis = syntheses[-1] if syntheses else None

        # Final checkpoint
        self._current_graph.checkpoint("final")

        goals_met = self._check_goals(strategy.goals)

        self._emit_progress(
            "completed",
            {
                "duration_seconds": self._stats.duration_seconds,
                "nodes_created": self._stats.nodes_created,
                "goals_met": goals_met,
            },
        )

        return ExecutionResult(
            success=len(self._stats.errors) == 0,
            graph=self._current_graph,
            stats=self._stats,
            phase_results=phase_results,
            goals_met=goals_met,
            final_synthesis=final_synthesis,
        )

    # =========================================================================
    # Phase Execution
    # =========================================================================

    async def _execute_phase(
        self,
        phase: Phase,
        context: dict[str, Any],
    ) -> PhaseResult:
        """Execute a single strategy phase."""
        start = datetime.now()

        self._emit_progress("phase_started", {"phase": phase.name})

        # Handle delegation to sub-strategy
        if phase.phase_type == PhaseType.DELEGATE and phase.delegate_to:
            result = await self._execute_delegation(phase, context)
            return result

        # Select target nodes
        targets = self._select_targets(phase)

        if not targets:
            return PhaseResult(
                phase_name=phase.name,
                success=True,
                duration_ms=int((datetime.now() - start).total_seconds() * 1000),
            )

        # Build phase context with web_search and model_hint
        phase_context = {**context}
        if phase.web_search:
            phase_context["web_search"] = True
        if phase.model_hint:
            phase_context["model"] = phase.model_hint

        # Execute operations on targets
        created_nodes: list[str] = []
        errors: list[str] = []
        operations_executed = 0

        if phase.parallel and len(targets) > 1:
            # Parallel execution
            results = await self._execute_parallel(
                phase.operations,
                targets,
                phase_context,
                phase.max_concurrent,
            )
            for result in results:
                if result.success:
                    created_nodes.extend([n.id for n in result.created_nodes])
                    operations_executed += 1
                else:
                    errors.append(result.error or "Unknown error")
        else:
            # Sequential execution
            for target in targets:
                for op_type in phase.operations:
                    result = await self._execute_operation(op_type, [target.id], phase_context)
                    if result.success:
                        created_nodes.extend([n.id for n in result.created_nodes])
                        operations_executed += 1
                    else:
                        errors.append(result.error or "Unknown error")

        self._stats.operations_executed += operations_executed
        self._stats.nodes_created += len(created_nodes)

        duration_ms = int((datetime.now() - start).total_seconds() * 1000)

        self._emit_progress(
            "phase_completed",
            {
                "phase": phase.name,
                "targets": len(targets),
                "created": len(created_nodes),
                "duration_ms": duration_ms,
            },
        )

        return PhaseResult(
            phase_name=phase.name,
            success=len(errors) == 0 or phase.continue_on_error,
            nodes_affected=len(targets),
            operations_executed=operations_executed,
            created_nodes=created_nodes,
            errors=errors,
            duration_ms=duration_ms,
        )

    async def _execute_delegation(
        self,
        phase: Phase,
        context: dict[str, Any],
    ) -> PhaseResult:
        """Execute a phase that delegates to a sub-strategy."""
        if not phase.delegate_to:
            return PhaseResult(
                phase_name=phase.name,
                success=False,
                errors=["No delegate_to specified"],
            )

        sub_strategy = self._strategy_registry.get(phase.delegate_to)
        if not sub_strategy:
            return PhaseResult(
                phase_name=phase.name,
                success=False,
                errors=[f"Strategy '{phase.delegate_to}' not found"],
            )

        # Select target nodes for delegation
        targets = self._select_targets(phase)

        if not targets:
            return PhaseResult(
                phase_name=phase.name,
                success=True,
            )

        # For each target, run sub-strategy
        # TODO: This is a simplified implementation
        # Full implementation would spawn sub-graphs and merge results
        created_nodes: list[str] = []

        for target in targets:
            # Create sub-question from target content
            sub_result = await self.cook(
                target.content,
                sub_strategy,
                {**context, "depth": target.depth + 1},
            )

            if sub_result.success and sub_result.final_synthesis:
                # Link synthesis back to target
                self._current_graph.add(sub_result.final_synthesis)
                self._current_graph.link(
                    target.id,
                    sub_result.final_synthesis.id,
                    NodeRelation.TRANSFORMS_TO,
                )
                created_nodes.append(sub_result.final_synthesis.id)

        return PhaseResult(
            phase_name=phase.name,
            success=True,
            nodes_affected=len(targets),
            created_nodes=created_nodes,
        )

    def _select_targets(self, phase: Phase) -> list[Node]:
        """Select nodes that match phase criteria."""
        if not self._current_graph:
            return []

        candidates = list(self._current_graph)

        # Filter by type
        if phase.target_types:
            candidates = [n for n in candidates if n.node_type in phase.target_types]

        # Filter by status
        if phase.target_status:
            candidates = [n for n in candidates if n.status in phase.target_status]

        # Apply batch size
        if phase.batch_size:
            candidates = candidates[: phase.batch_size]

        return candidates

    # =========================================================================
    # Operation Execution
    # =========================================================================

    async def _execute_operation(
        self,
        op_type: OperationType,
        target_ids: list[str],
        context: dict[str, Any],
    ) -> OperationResult:
        """Execute a single operation on target nodes."""
        operation = self._operation_registry.create(op_type)

        if not operation:
            return OperationResult.failed(f"Operation {op_type.value} not registered")

        if not self._current_graph:
            return OperationResult.failed("No active graph")

        result = await operation.execute(self._current_graph, target_ids, context)

        # Add created nodes to graph
        for node in result.created_nodes:
            self._current_graph.add(node)

        return result

    async def _execute_parallel(
        self,
        operations: list[OperationType],
        targets: list[Node],
        context: dict[str, Any],
        max_concurrent: int,
    ) -> list[OperationResult]:
        """Execute operations on targets in parallel."""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def run_with_semaphore(target: Node) -> OperationResult:
            async with semaphore:
                results: list[OperationResult] = []
                for op_type in operations:
                    result = await self._execute_operation(op_type, [target.id], context)
                    results.append(result)
                # Combine results
                if results:
                    created = []
                    modified = []
                    for r in results:
                        created.extend(r.created_nodes)
                        modified.extend(r.modified_nodes)
                    return OperationResult(
                        success=all(r.success for r in results),
                        created_nodes=created,
                        modified_nodes=modified,
                    )
                return OperationResult(success=True)

        tasks = [run_with_semaphore(target) for target in targets]
        return await asyncio.gather(*tasks)

    # =========================================================================
    # Goal Checking
    # =========================================================================

    def _check_goals(self, goals: list[Goal]) -> list[str]:
        """Check which goals are met."""
        if not self._current_graph:
            return []

        stats = self._current_graph.stats()
        met = []

        for goal in goals:
            if goal.check(stats):
                met.append(goal.goal_type.value)

        return met

    # =========================================================================
    # Progress & Utilities
    # =========================================================================

    def _emit_progress(self, event: str, data: dict[str, Any]) -> None:
        """Emit a progress event."""
        if self.on_progress:
            self.on_progress(event, data)
        logger.debug(f"MasterChef: {event} - {data}")


# =============================================================================
# Convenience Functions
# =============================================================================


async def research(
    question: str,
    strategy: str = "recursive_research",
    output_dir: Path | None = None,
    max_parallel: int = 10,
    **context: Any,
) -> ExecutionResult:
    """Quick research function.

    Args:
        question: The research question
        strategy: Strategy name
        output_dir: Output directory
        max_parallel: Max parallel operations
        **context: Additional context

    Returns:
        ExecutionResult
    """
    # Ensure built-in strategies are registered
    from .strategy import register_builtin_strategies

    register_builtin_strategies()

    chef = MasterChef(
        output_dir=output_dir,
        max_parallel=max_parallel,
    )

    return await chef.cook(question, strategy, context)
