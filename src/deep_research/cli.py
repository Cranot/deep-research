"""
CLI entry point for deep-research.

Usage:
    deep-research research [options] "Your question"

A subcommand is required: research, perspectives, socratic, cache, config,
validate. The flag set overlaps with the legacy bash script but is not
identical -- see the CLI Options table in README.md.
"""

# Load .env file before anything else
from dotenv import load_dotenv

load_dotenv()

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from .cache import cache_stats, clear_cache
from .exceptions import (
    APIKeyError,
    ConfigValidationError,
    DeepResearchError,
    ModelValidationError,
    QuestionValidationError,
    ValidationError,
)
from .models import ModelSpec, ResearchConfig
from .orchestrator import Orchestrator
from .recipes import SocraticEngine
from .recipes.base import RecipeContext
from .settings import settings
from .validation import (
    validate_api_keys_for_config,
    validate_depth,
    validate_model_spec,
    validate_parallel,
    validate_question,
)

app = typer.Typer(
    name="deep-research",
    help="Fractal exploration of any question through recursive AI agents.",
    add_completion=False,
)
console = Console()
error_console = Console(stderr=True)


def parse_model(value: str) -> ModelSpec:
    """Parse model specification with validation."""
    model_spec, warnings = validate_model_spec(value)
    for warning in warnings:
        error_console.print(f"[yellow]Warning: {warning}[/yellow]")
    return model_spec


def parse_leaf_models(value: str | None) -> list[ModelSpec]:
    """Parse comma-separated leaf models with validation."""
    if not value:
        return []
    specs = [m.strip() for m in value.split(",")]
    models = []
    for spec in specs:
        model, warnings = validate_model_spec(spec)
        for warning in warnings:
            error_console.print(f"[yellow]Warning: {warning}[/yellow]")
        models.append(model)
    return models


def handle_error(e: Exception) -> None:
    """Handle errors with user-friendly messages."""
    if isinstance(e, QuestionValidationError):
        error_console.print("\n[red]Error: Invalid question[/red]")
        error_console.print(f"  {e.message}")
        if e.reason:
            error_console.print(f"  Reason: {e.reason}")
        error_console.print("\n[dim]Tip: Questions must be 3-10,000 characters[/dim]")

    elif isinstance(e, ModelValidationError):
        error_console.print("\n[red]Error: Invalid model specification[/red]")
        error_console.print(f"  {e.message}")
        if e.valid_models:
            error_console.print(f"  Valid options: {', '.join(e.valid_models)}")

    elif isinstance(e, APIKeyError):
        error_console.print("\n[red]Error: Missing API key[/red]")
        error_console.print(f"  {e.message}")
        error_console.print("\n[dim]Set the environment variable and try again:[/dim]")
        error_console.print(f"  export {e.env_var}=your-key-here")

    elif isinstance(e, ConfigValidationError):
        error_console.print("\n[red]Error: Invalid configuration[/red]")
        error_console.print(f"  {e.message}")
        if e.field:
            error_console.print(f"  Field: {e.field}")
        if e.expected:
            error_console.print(f"  Expected: {e.expected}")

    elif isinstance(e, DeepResearchError):
        error_console.print(f"\n[red]Error: {type(e).__name__}[/red]")
        error_console.print(f"  {e.message}")
        if e.details:
            for key, value in e.details.items():
                if value is not None:
                    error_console.print(f"  {key}: {value}")

    else:
        error_console.print(f"\n[red]Error: {type(e).__name__}[/red]")
        error_console.print(f"  {str(e)}")

    error_console.print("\n[dim]Use --help for usage information[/dim]")


@app.command()
def research(
    question: str = typer.Argument(..., help="The research question"),
    model: str = typer.Option(
        None,
        "-m",
        "--model",
        help="Orchestrator model (opus, sonnet, haiku, gemini:pro, gemini:flash)",
    ),
    researcher: str = typer.Option(
        None,
        "-r",
        "--researcher",
        help="Researcher model for child agents",
    ),
    leaves: Optional[str] = typer.Option(
        None,
        "-l",
        "--leaves",
        help="Leaf ensemble models, comma-separated (e.g., 'haiku,gemini:flash')",
    ),
    merger: Optional[str] = typer.Option(
        None,
        "--merger",
        help="Model for merging ensemble results (default: use orchestrator)",
    ),
    depth: int = typer.Option(
        0,
        "-d",
        "--depth",
        help="Max recursion depth (0 = use the configured default, normally 5)",
    ),
    parallel: int = typer.Option(
        None,
        "-p",
        "--parallel",
        help="Max concurrent agents (default: 10)",
    ),
    web: bool = typer.Option(
        False,
        "-w",
        "--web",
        help="[not yet wired on this command] Enable web search (Claude only)",
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "-o",
        "--output",
        help="Output directory (default: reports/YYYY-MM-DD-slug)",
    ),
    verbose: bool = typer.Option(
        False,
        "-v",
        "--verbose",
        help="[not yet wired on this command] Enable verbose output",
    ),
    # Perspective expansion options
    perspectives: Optional[str] = typer.Option(
        None,
        "--perspectives",
        help="Perspective models, comma-separated (e.g., 'opus,gemini:flash,kimi:kimi')",
    ),
    perspective_picker: Optional[str] = typer.Option(
        None,
        "--perspective-picker",
        help="Model to select best perspectives (default: sonnet)",
    ),
    all_perspectives: bool = typer.Option(
        False,
        "--all-perspectives",
        help="Use all available models for perspective expansion",
    ),
    perspective_depth: int = typer.Option(
        1,
        "--perspective-depth",
        help="Recursive perspective depth (1 = flat, 2+ = recursive sub-perspectives)",
    ),
    no_blind_spot: bool = typer.Option(
        False,
        "--no-blind-spot",
        help="Disable blind spot detection for perspectives",
    ),
    no_perspective_cache: bool = typer.Option(
        False,
        "--no-perspective-cache",
        help="Disable perspective caching",
    ),
):
    """
    Run recursive research on a question.

    COST: fan-out is uncapped -- one child agent per sub-question, at every
    level. -p limits concurrency, not the total. Start with -d 1.

    Examples:
        deep-research research -d 1 "What makes startups successful?"
        deep-research research -m opus -r haiku "Complex analysis"
        deep-research research -m gemini:pro -r gemini:flash "Use Gemini"
        deep-research research -l "haiku,gemini:flash" "Multi-model ensemble"

    Perspective Expansion Examples:
        deep-research research --all-perspectives "What makes AI safe?"
        deep-research research --perspectives "opus,gemini:flash,kimi:kimi" "Complex question"
        deep-research research --perspectives "opus,sonnet" --perspective-picker sonnet "Topic"
    """
    try:
        # Validate question first
        question = validate_question(question)

        # Validate depth and parallel
        validate_depth(depth)
        validate_parallel(parallel)

        # Parse models (use settings defaults if not specified)
        orchestrator = parse_model(model or settings.default_orchestrator)
        researcher_model = parse_model(researcher or settings.default_researcher)
        leaf_models = parse_leaf_models(leaves)
        merger_model = parse_model(merger) if merger else None

        # Parse perspective models
        perspective_models = parse_leaf_models(perspectives)  # Same parsing logic
        picker_model = parse_model(perspective_picker) if perspective_picker else None

        # Use settings defaults for depth/parallel if not overridden.
        # depth==0 is a sentinel meaning "use the configured default"; it does
        # NOT mean unlimited on this command.
        effective_depth = depth if depth != 0 else settings.max_depth
        effective_parallel = parallel if parallel is not None else settings.max_parallel

        # Be honest about flags this command accepts but does not yet act on,
        # rather than silently ignoring them.
        if web:
            console.print(
                "[yellow]Note:[/yellow] -w/--web is not yet wired into this command "
                "and will have no effect. Use the 'grounded_research' strategy via the "
                "Python API for web grounding."
            )
        if verbose:
            console.print(
                "[yellow]Note:[/yellow] -v/--verbose is not yet wired into this command "
                "and will have no effect."
            )

        # Build config
        config = ResearchConfig(
            question=question,
            orchestrator=orchestrator,
            researcher=researcher_model,
            leaf_models=leaf_models,
            merger=merger_model,
            max_depth=effective_depth,
            max_parallel=effective_parallel,
            web_search=web,
            output_dir=output_dir,
            # Perspective expansion options
            perspective_models=perspective_models,
            perspective_picker=picker_model,
            use_all_perspective_models=all_perspectives,
            perspective_depth=perspective_depth,
            perspective_enable_blind_spot=not no_blind_spot,
            perspective_enable_cache=not no_perspective_cache,
        )

        # Validate API keys upfront
        validate_api_keys_for_config(config)

        # Show perspective mode if enabled
        if all_perspectives:
            console.print("[bold blue]Perspective Expansion: ALL MODELS[/bold blue]")
        elif perspective_models:
            console.print(
                f"[bold blue]Perspective Expansion: {', '.join(str(m) for m in perspective_models)}[/bold blue]"
            )

        # Run the research
        orchestrator_instance = Orchestrator(config)
        asyncio.run(orchestrator_instance.run())

    except ValidationError as e:
        handle_error(e)
        raise typer.Exit(1)
    except DeepResearchError as e:
        handle_error(e)
        raise typer.Exit(1)
    except KeyboardInterrupt:
        error_console.print("\n[yellow]Research cancelled by user[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        handle_error(e)
        raise typer.Exit(1)


@app.command()
def perspectives(
    question: str = typer.Argument(..., help="The question to expand into perspectives"),
    models: Optional[str] = typer.Option(
        None,
        "-m",
        "--models",
        help="Models to query for perspectives, comma-separated (default: opus,gemini:flash,kimi:kimi)",
    ),
    picker: str = typer.Option(
        "sonnet",
        "--picker",
        help="Model to select best perspectives (default: sonnet)",
    ),
    all_models: bool = typer.Option(
        False,
        "--all",
        help="Use all available models for maximum diversity",
    ),
    depth: int = typer.Option(
        1,
        "-d",
        "--depth",
        help="Recursive perspective depth (1 = flat, 2+ = recursive sub-perspectives)",
    ),
    no_blind_spot: bool = typer.Option(
        False,
        "--no-blind-spot",
        help="Disable blind spot detection",
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Disable perspective caching",
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "-o",
        "--output",
        help="Output directory",
    ),
):
    """
    Run perspective expansion on a question (without full research).

    Queries multiple models for their perspectives on a question, then uses
    a picker model to select the most valuable and diverse ones.

    Examples:
        deep-research perspectives "What makes AI safe?"
        deep-research perspectives --all "Complex question"
        deep-research perspectives -m "opus,gemini:pro" --picker opus "Topic"
    """
    try:
        from .recipes import (
            PerspectiveExpander,
            create_all_models_expander,
            create_default_expander,
        )

        # Validate question
        question = validate_question(question)

        # Determine output directory
        if output_dir is None:
            from datetime import datetime

            date = datetime.now().strftime("%Y-%m-%d")
            slug = ResearchConfig._slugify(question)
            output_dir = Path(f"reports/{date}-{slug}")

        output_dir.mkdir(parents=True, exist_ok=True)

        # Create expander based on options
        if all_models:
            expander = create_all_models_expander(output_dir=output_dir)
            # Override depth and feature flags
            expander.depth = depth
            expander.enable_blind_spot_check = not no_blind_spot
            expander.enable_caching = not no_cache
            console.print("[bold blue]Perspective Expansion: ALL MODELS[/bold blue]")
        elif models:
            perspective_models = parse_leaf_models(models)
            picker_model = parse_model(picker)
            expander = PerspectiveExpander(
                models=perspective_models,
                picker=picker_model,
                output_dir=output_dir,
                depth=depth,
                enable_blind_spot_check=not no_blind_spot,
                enable_caching=not no_cache,
            )
            console.print(
                f"[bold blue]Perspectives: {', '.join(str(m) for m in perspective_models)}[/bold blue]"
            )
        else:
            expander = create_default_expander(output_dir=output_dir)
            # Override depth and feature flags
            expander.depth = depth
            expander.enable_blind_spot_check = not no_blind_spot
            expander.enable_caching = not no_cache
            console.print(
                "[bold blue]Perspectives: opus, gemini:flash, kimi:kimi (default)[/bold blue]"
            )

        # Show active features
        if depth > 1:
            console.print(f"[dim]Recursive depth: {depth}[/dim]")
        if no_blind_spot:
            console.print("[dim]Blind spot detection: disabled[/dim]")
        if no_cache:
            console.print("[dim]Caching: disabled[/dim]")

        console.print(f"[bold]Question:[/bold] {question}\n")

        # Run perspective expansion
        result = asyncio.run(expander.expand(question))

        # Display results
        console.print("\n[bold green]Perspective Expansion Complete![/bold green]")
        console.print(f"Total perspectives gathered: {len(result.all_perspectives)}")
        console.print(f"Selected perspectives: {len(result.selected_perspectives)}")
        if result.blind_spot_perspectives:
            console.print(f"Blind spots discovered: {len(result.blind_spot_perspectives)}")
        if result.domain_detected:
            console.print(f"Domain detected: {result.domain_detected}")
        console.print(f"Duration: {result.duration_ms}ms")
        if result.from_cache:
            console.print("[dim](from cache)[/dim]")

        console.print("\n[bold]Selected Perspectives:[/bold]")
        for i, p in enumerate(result.selected_perspectives, 1):
            console.print(f"  {i}. [cyan]{p.label}[/cyan]: {p.description}")
            if p.selection_reason:
                console.print(f"     [dim]({p.selection_reason})[/dim]")
            if p.matched_model:
                console.print(f"     [dim]Matched model: {p.matched_model}[/dim]")
            if p.children:
                for child in p.children:
                    console.print(f"       → [cyan]{child.label}[/cyan]: {child.description}")

        if result.blind_spot_perspectives:
            console.print("\n[bold yellow]Blind Spot Perspectives (Discovered):[/bold yellow]")
            for i, p in enumerate(result.blind_spot_perspectives, 1):
                console.print(f"  {i}. [yellow]{p.label}[/yellow]: {p.description}")
                if p.matched_model:
                    console.print(f"     [dim]Matched model: {p.matched_model}[/dim]")

        console.print(f"\nOutput: {output_dir / 'PERSPECTIVES.md'}")

        # Suggest next step
        console.print("\n[dim]Next step: Use these perspectives with full research:[/dim]")
        console.print(f'[dim]  deep-research research "{question}"[/dim]')

    except ValidationError as e:
        handle_error(e)
        raise typer.Exit(1)
    except DeepResearchError as e:
        handle_error(e)
        raise typer.Exit(1)
    except KeyboardInterrupt:
        error_console.print("\n[yellow]Expansion cancelled by user[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        handle_error(e)
        raise typer.Exit(1)


@app.command()
def socratic(
    question: str = typer.Argument(..., help="The question to analyze"),
    model: str = typer.Option(
        None,
        "-m",
        "--model",
        help="Model for Socratic analysis (requires good judgment)",
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "-o",
        "--output",
        help="Output directory",
    ),
):
    """
    Run the Socratic Engine on a question.

    The Socratic Engine transforms questions through recursive assumption-challenging.
    Often, the right question makes the answer obvious.

    Examples:
        deep-research socratic "How do I become more productive?"
        deep-research socratic -m opus "What makes a startup successful?"
    """
    try:
        # Validate question
        question = validate_question(question)

        orchestrator = parse_model(model or settings.default_orchestrator)

        # Build minimal config for Socratic
        config = ResearchConfig(
            question=question,
            orchestrator=orchestrator,
            researcher=orchestrator,  # Not used for Socratic
            output_dir=output_dir,
        )

        # Ensure output dir exists
        config.output_dir.mkdir(parents=True, exist_ok=True)

        # Create context
        context = RecipeContext(config=config, output_dir=config.output_dir)

        # Run the Socratic Engine
        engine = SocraticEngine()
        result = asyncio.run(engine.run(question, context))

        # Write output
        output_file = config.output_dir / "SOCRATIC.md"
        output_file.write_text(result.final_output, encoding="utf-8")

        console.print("\n[bold green]Socratic analysis complete![/bold green]")
        console.print(f"Output: {output_file}")

        if result.answer_emerged:
            console.print("\n[bold]Answer emerged from the question:[/bold]")
            console.print(result.emergent_answer)
        else:
            console.print("\n[bold]Reconstructed question:[/bold]")
            console.print(result.reconstructed_question)
            console.print("\n[dim]Use 'deep-research research' on the reconstructed question[/dim]")

    except ValidationError as e:
        handle_error(e)
        raise typer.Exit(1)
    except DeepResearchError as e:
        handle_error(e)
        raise typer.Exit(1)
    except KeyboardInterrupt:
        error_console.print("\n[yellow]Analysis cancelled by user[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        handle_error(e)
        raise typer.Exit(1)


@app.command()
def cache(
    action: str = typer.Argument(
        "stats",
        help="Action: stats, clear",
    ),
):
    """
    Manage the response cache.

    Examples:
        deep-research cache stats  # Show cache statistics
        deep-research cache clear  # Clear all cached responses
    """
    if action == "stats":
        stats = cache_stats()
        console.print("[bold]Cache Statistics[/bold]")
        console.print(f"  Enabled: {stats['enabled']}")
        console.print(f"  Entries: {stats['entries']}")
        console.print(f"  Size: {stats['size_bytes'] / 1024:.1f} KB")
        console.print(f"  Location: {stats['file']}")
    elif action == "clear":
        count = clear_cache()
        console.print(f"[green]Cleared {count} cached entries[/green]")
    else:
        error_console.print(f"[red]Unknown action: {action}[/red]")
        console.print("Use 'stats' or 'clear'")
        raise typer.Exit(1)


@app.command("config")
def show_config():
    """
    Show current configuration.

    Settings can be overridden via environment variables:
        DEEP_RESEARCH_ORCHESTRATOR=opus
        DEEP_RESEARCH_RESEARCHER=haiku
        DEEP_RESEARCH_MAX_DEPTH=3
        DEEP_RESEARCH_CACHE_ENABLED=false
    """
    console.print("[bold]Current Configuration[/bold]")
    for key, value in settings.to_dict().items():
        console.print(f"  {key}: {value}")


@app.command()
def validate(
    question: str = typer.Argument(..., help="The question to validate"),
    model: str = typer.Option(
        None,
        "-m",
        "--model",
        help="Model specification to validate",
    ),
):
    """
    Validate inputs without running research.

    Useful for checking API keys and model specifications.

    Examples:
        deep-research validate "My question"
        deep-research validate "My question" -m gemini:flash
    """
    errors = []
    warnings = []

    # Validate question
    try:
        validate_question(question)
        console.print("[green]OK[/green] Question is valid")
    except QuestionValidationError as e:
        errors.append(f"Question: {e.message}")

    # Validate model if provided
    if model:
        try:
            model_spec, model_warnings = validate_model_spec(model)
            console.print(f"[green]OK[/green] Model '{model}' is valid ({model_spec})")
            warnings.extend(model_warnings)
        except ModelValidationError as e:
            errors.append(f"Model: {e.message}")

    # Check API keys
    import os

    from .validation import ALL_ENV_VARS

    console.print("\n[bold]API Keys:[/bold]")
    for provider, env_var in ALL_ENV_VARS.items():
        # Extract actual env var name (before any description)
        actual_var = env_var.split(" ")[0]
        if os.environ.get(actual_var):
            console.print(f"  [green]OK[/green] {provider.value}: {actual_var} is set")
        elif provider.value == "claude":
            console.print(
                f"  [green]OK[/green] {provider.value}: uses CLI subscription (no API key needed)"
            )
        else:
            console.print(f"  [dim]-[/dim] {provider.value}: {actual_var} not set")

    # Print warnings
    if warnings:
        console.print("\n[yellow]Warnings:[/yellow]")
        for warning in warnings:
            console.print(f"  {warning}")

    # Print errors
    if errors:
        console.print("\n[red]Errors:[/red]")
        for error in errors:
            console.print(f"  {error}")
        raise typer.Exit(1)

    console.print("\n[green]All validations passed![/green]")


def main():
    """Entry point."""
    app()


if __name__ == "__main__":
    main()
