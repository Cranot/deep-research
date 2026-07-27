"""
MasterChef Core - The intelligent research orchestration framework.

This module provides the core abstractions for research orchestration:

- **Nodes**: Typed content units with epistemic status
- **Graphs**: Knowledge graphs with persistence
- **Operations**: Epistemic transitions that transform nodes
- **Strategies**: Declarative recipes for research
- **MasterChef**: The intelligent orchestrator

## Quick Start

```python
from deep_research.core import research

# Simple research with default strategy
result = await research("What makes startups successful?")
print(result.final_synthesis.content)

# With custom strategy
from deep_research.core import MasterChef, recursive_research_strategy

chef = MasterChef(output_dir=Path("reports/my-research"))
strategy = recursive_research_strategy(max_depth=3)
result = await chef.cook("My question", strategy)
```

## Architecture

```
Question
    ↓
MasterChef.cook(question, strategy)
    ↓
KnowledgeGraph (holds Nodes)
    ↓
Strategy phases execute Operations
    ↓
Nodes transform: Unknown → Explored → Validated → Synthesized
    ↓
Final Synthesis
```
"""

# Node types and status
# MasterChef orchestrator
from .chef import (
    ExecutionResult,
    ExecutionStats,
    MasterChef,
    PhaseResult,
    research,
)

# Knowledge graph
from .graph import (
    GraphMetadata,
    KnowledgeGraph,
)
from .node import (
    EpistemicStatus,
    Node,
    NodeEdge,
    NodeRelation,
    NodeType,
    assumption,
    insight,
    perspective,
    # Factory functions
    question,
    synthesis,
)

# Operations
from .operation import (
    OPERATION_SPECS,
    BaseOperation,
    Operation,
    OperationRegistry,
    OperationResult,
    OperationSpec,
    OperationType,
    get_spec,
    register_operation,
)

# Strategies
from .strategy import (
    Goal,
    GoalType,
    Phase,
    PhaseCondition,
    PhaseType,
    Strategy,
    StrategyMetadata,
    StrategyRegistry,
    grounded_research_strategy,
    perspective_strategy,
    # Built-in strategy builders
    recursive_research_strategy,
    register_builtin_strategies,
    socratic_strategy,
)

__all__ = [
    # Nodes
    "Node",
    "NodeType",
    "NodeEdge",
    "NodeRelation",
    "EpistemicStatus",
    "question",
    "perspective",
    "assumption",
    "insight",
    "synthesis",
    # Graph
    "KnowledgeGraph",
    "GraphMetadata",
    # Operations
    "Operation",
    "BaseOperation",
    "OperationType",
    "OperationSpec",
    "OperationResult",
    "OperationRegistry",
    "register_operation",
    "get_spec",
    "OPERATION_SPECS",
    # Strategies
    "Strategy",
    "StrategyMetadata",
    "Phase",
    "PhaseType",
    "PhaseCondition",
    "Goal",
    "GoalType",
    "StrategyRegistry",
    "recursive_research_strategy",
    "socratic_strategy",
    "perspective_strategy",
    "grounded_research_strategy",
    "register_builtin_strategies",
    # MasterChef
    "MasterChef",
    "ExecutionResult",
    "ExecutionStats",
    "PhaseResult",
    "research",
]
