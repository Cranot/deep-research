"""
Structured logging for deep-research.

Provides:
- Console output with Rich formatting
- File logging with timestamps and log levels
- API call tracking with token usage
- Performance metrics
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.logging import RichHandler

# =============================================================================
# Log Entry Types
# =============================================================================


@dataclass
class APICallLog:
    """Log entry for an API call."""

    timestamp: str
    provider: str
    model: str
    operation: str  # explore, answer, synthesize, merge
    prompt_preview: str
    response_preview: str | None = None
    duration_ms: int | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    cached: bool = False
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class AgentLog:
    """Log entry for agent lifecycle events."""

    timestamp: str
    agent_id: str
    event: str  # start, explore, spawn, synthesize, complete, fail
    question_preview: str | None = None
    model: str | None = None
    depth: int | None = None
    children_count: int | None = None
    duration_ms: int | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class ResearchMetrics:
    """Aggregate metrics for a research run."""

    start_time: str | None = None
    end_time: str | None = None
    total_agents: int = 0
    completed_agents: int = 0
    failed_agents: int = 0
    total_api_calls: int = 0
    cached_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_duration_ms: int = 0
    max_depth_reached: int = 0
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# =============================================================================
# Logger Class
# =============================================================================


class ResearchLogger:
    """
    Structured logger for deep-research.

    Provides both console output (via Rich) and file logging (JSON lines).
    """

    def __init__(
        self,
        output_dir: Path | None = None,
        console_level: int = logging.INFO,
        file_level: int = logging.DEBUG,
        verbose: bool = False,
    ):
        self.output_dir = output_dir
        self.console_level = console_level
        self.file_level = file_level
        self.verbose = verbose

        # Rich console for user-facing output
        self.console = Console(stderr=True)

        # Metrics tracking
        self.metrics = ResearchMetrics()

        # API call logs
        self._api_calls: list[APICallLog] = []
        self._agent_logs: list[AgentLog] = []

        # Set up Python logger
        self._logger = self._setup_logger()

        # Log file path
        self._log_file: Path | None = None
        if output_dir:
            self._log_file = output_dir / "research.log"

    def _setup_logger(self) -> logging.Logger:
        """Configure Python logger with Rich handler."""
        logger = logging.getLogger("deep_research")
        logger.setLevel(logging.DEBUG)

        # Clear existing handlers
        logger.handlers.clear()

        # Rich console handler
        rich_handler = RichHandler(
            console=self.console,
            show_time=True,
            show_path=False,
            rich_tracebacks=True,
            markup=True,
        )
        rich_handler.setLevel(self.console_level)
        logger.addHandler(rich_handler)

        return logger

    def _write_to_file(self, entry: dict[str, Any]) -> None:
        """Append a log entry to the log file."""
        if not self._log_file:
            return
        try:
            self._log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except IOError:
            pass  # Don't fail research due to log write errors

    def _timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.now().isoformat()

    # -------------------------------------------------------------------------
    # High-level logging methods
    # -------------------------------------------------------------------------

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self._logger.info(message, extra=kwargs)
        self._write_to_file(
            {
                "level": "INFO",
                "timestamp": self._timestamp(),
                "message": message,
                **kwargs,
            }
        )

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        if self.verbose:
            self._logger.debug(message, extra=kwargs)
        self._write_to_file(
            {
                "level": "DEBUG",
                "timestamp": self._timestamp(),
                "message": message,
                **kwargs,
            }
        )

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self._logger.warning(message, extra=kwargs)
        self._write_to_file(
            {
                "level": "WARNING",
                "timestamp": self._timestamp(),
                "message": message,
                **kwargs,
            }
        )

    def error(self, message: str, exc_info: bool = False, **kwargs: Any) -> None:
        """Log error message."""
        self._logger.error(message, exc_info=exc_info, extra=kwargs)
        self._write_to_file(
            {
                "level": "ERROR",
                "timestamp": self._timestamp(),
                "message": message,
                **kwargs,
            }
        )
        self.metrics.errors.append(message)

    # -------------------------------------------------------------------------
    # Agent lifecycle logging
    # -------------------------------------------------------------------------

    def agent_start(
        self,
        agent_id: str,
        question: str,
        model: str,
        depth: int,
    ) -> None:
        """Log agent starting."""
        entry = AgentLog(
            timestamp=self._timestamp(),
            agent_id=agent_id,
            event="start",
            question_preview=question[:100] if len(question) > 100 else question,
            model=model,
            depth=depth,
        )
        self._agent_logs.append(entry)
        self.metrics.total_agents += 1
        self.metrics.max_depth_reached = max(self.metrics.max_depth_reached, depth)

        self.console.print(f"[dim][{agent_id}][/dim] Starting: {question[:60]}...")
        self._write_to_file({"type": "agent", **entry.to_dict()})

    def agent_exploring(self, agent_id: str) -> None:
        """Log agent exploring for angles."""
        self.console.print(f"[dim][{agent_id}][/dim] Exploring...")

    def agent_found_questions(self, agent_id: str, count: int) -> None:
        """Log questions found during exploration."""
        self.console.print(f"[dim][{agent_id}][/dim] Found {count} research questions")

    def agent_spawning(
        self,
        agent_id: str,
        children_count: int,
        max_parallel: int,
    ) -> None:
        """Log agent spawning children."""
        entry = AgentLog(
            timestamp=self._timestamp(),
            agent_id=agent_id,
            event="spawn",
            children_count=children_count,
        )
        self._agent_logs.append(entry)

        self.console.print(
            f"[dim][{agent_id}][/dim] Spawning {children_count} children "
            f"(max {max_parallel} parallel)..."
        )
        self._write_to_file({"type": "agent", **entry.to_dict()})

    def agent_child_start(
        self,
        parent_id: str,
        child_idx: int,
        total: int,
        question: str,
    ) -> None:
        """Log child agent starting."""
        self.console.print(
            f"[dim][{parent_id}][/dim] Spawning {child_idx}/{total}: {question[:50]}..."
        )

    def agent_children_complete(self, agent_id: str) -> None:
        """Log all children completed."""
        self.console.print(f"[dim][{agent_id}][/dim] All children complete")

    def agent_synthesizing(self, agent_id: str) -> None:
        """Log agent synthesizing results."""
        self.console.print(f"[dim][{agent_id}][/dim] Synthesizing...")

    def agent_answering(self, agent_id: str) -> None:
        """Log leaf agent answering directly."""
        self.console.print(f"[dim][{agent_id}][/dim] Answering directly...")

    def agent_ensemble(self, agent_id: str, model_count: int) -> None:
        """Log ensemble mode."""
        self.console.print(f"[dim][{agent_id}][/dim] Ensemble with {model_count} models...")

    def agent_complete(self, agent_id: str, duration_ms: int | None = None) -> None:
        """Log agent completed."""
        entry = AgentLog(
            timestamp=self._timestamp(),
            agent_id=agent_id,
            event="complete",
            duration_ms=duration_ms,
        )
        self._agent_logs.append(entry)
        self.metrics.completed_agents += 1

        self.console.print(f"[dim][{agent_id}][/dim] Complete")
        self._write_to_file({"type": "agent", **entry.to_dict()})

    def agent_failed(
        self,
        agent_id: str,
        error: str,
        question: str | None = None,
    ) -> None:
        """Log agent failed."""
        entry = AgentLog(
            timestamp=self._timestamp(),
            agent_id=agent_id,
            event="fail",
            error=error,
            question_preview=question[:100] if question else None,
        )
        self._agent_logs.append(entry)
        self.metrics.failed_agents += 1

        self.console.print(f"[red][{agent_id}] Failed: {error}[/red]")
        self._write_to_file({"type": "agent", **entry.to_dict()})

    # -------------------------------------------------------------------------
    # API call logging
    # -------------------------------------------------------------------------

    def api_call(
        self,
        provider: str,
        model: str,
        operation: str,
        prompt: str,
        response: str | None = None,
        duration_ms: int | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        cached: bool = False,
        error: str | None = None,
    ) -> None:
        """Log an API call."""
        entry = APICallLog(
            timestamp=self._timestamp(),
            provider=provider,
            model=model,
            operation=operation,
            prompt_preview=prompt[:100] if len(prompt) > 100 else prompt,
            response_preview=response[:100] if response and len(response) > 100 else response,
            duration_ms=duration_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached=cached,
            error=error,
        )
        self._api_calls.append(entry)

        # Update metrics
        self.metrics.total_api_calls += 1
        if cached:
            self.metrics.cached_calls += 1
        if duration_ms:
            self.metrics.total_duration_ms += duration_ms
        if input_tokens:
            self.metrics.total_input_tokens += input_tokens
        if output_tokens:
            self.metrics.total_output_tokens += output_tokens

        # Console output for cache hits
        if cached:
            self.console.print("[dim cyan]  (cached)[/dim cyan]", end="")

        self._write_to_file({"type": "api_call", **entry.to_dict()})

    # -------------------------------------------------------------------------
    # Research lifecycle
    # -------------------------------------------------------------------------

    def research_start(
        self,
        question: str,
        orchestrator: str,
        researcher: str,
        max_depth: int,
        max_parallel: int,
        output_dir: Path,
        leaf_models: list[str] | None = None,
    ) -> None:
        """Log research run starting."""
        self.metrics.start_time = self._timestamp()

        self.console.print("\n[bold]=== Deep Research ===[/bold]")
        self.console.print(f"Question: {question}")
        self.console.print(f"Orchestrator: {orchestrator}")
        self.console.print(f"Researcher: {researcher}")
        if leaf_models:
            self.console.print(f"Leaf Ensemble: {', '.join(leaf_models)}")
        self.console.print(f"Max Depth: {max_depth or 'unlimited'}")
        self.console.print(f"Max Parallel: {max_parallel}")
        self.console.print(f"Output: {output_dir}")
        self.console.print("[bold]====================[/bold]\n")

        self._write_to_file(
            {
                "type": "research_start",
                "timestamp": self._timestamp(),
                "question": question,
                "orchestrator": orchestrator,
                "researcher": researcher,
                "leaf_models": leaf_models,
                "max_depth": max_depth,
                "max_parallel": max_parallel,
                "output_dir": str(output_dir),
            }
        )

    def research_complete(
        self,
        report_file: Path,
        agents_dir: Path,
    ) -> None:
        """Log research run completed."""
        self.metrics.end_time = self._timestamp()

        self.console.print("\n[bold]=== Research Complete ===[/bold]")
        self.console.print(f"Output: {report_file}")

        # Print summary metrics
        self.console.print("\n[bold]Metrics:[/bold]")
        self.console.print(f"  Agents: {self.metrics.completed_agents}/{self.metrics.total_agents}")
        if self.metrics.failed_agents > 0:
            self.console.print(f"  [red]Failed: {self.metrics.failed_agents}[/red]")
        self.console.print(
            f"  API Calls: {self.metrics.total_api_calls} ({self.metrics.cached_calls} cached)"
        )
        if self.metrics.total_input_tokens or self.metrics.total_output_tokens:
            self.console.print(
                f"  Tokens: {self.metrics.total_input_tokens:,} in / "
                f"{self.metrics.total_output_tokens:,} out"
            )
        self.console.print(f"  Duration: {self.metrics.total_duration_ms / 1000:.1f}s")

        self._write_to_file(
            {
                "type": "research_complete",
                **self.metrics.to_dict(),
            }
        )

    def get_metrics(self) -> ResearchMetrics:
        """Get current metrics."""
        return self.metrics

    def write_metrics_file(self) -> None:
        """Write final metrics to a JSON file."""
        if not self.output_dir:
            return
        metrics_file = self.output_dir / "metrics.json"
        try:
            with open(metrics_file, "w", encoding="utf-8") as f:
                json.dump(self.metrics.to_dict(), f, indent=2)
        except IOError:
            pass


# =============================================================================
# Global logger instance
# =============================================================================


_logger: ResearchLogger | None = None


def get_logger() -> ResearchLogger:
    """Get or create the global logger instance."""
    global _logger
    if _logger is None:
        _logger = ResearchLogger()
    return _logger


def init_logger(
    output_dir: Path | None = None,
    verbose: bool = False,
) -> ResearchLogger:
    """Initialize a new logger for a research run."""
    global _logger
    _logger = ResearchLogger(output_dir=output_dir, verbose=verbose)
    return _logger
