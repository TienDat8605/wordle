"""Search-based solvers for the Wordle game."""

from __future__ import annotations

import heapq
from collections import deque
from dataclasses import dataclass
from typing import Callable, Iterable, List, Sequence, Tuple

from .feedback import Feedback, Mark, evaluate_guess
from .knowledge import WordleKnowledge


@dataclass
class SolverResult:
    """Outcome summary for a solver run."""

    success: bool
    history: Tuple[Tuple[str, Feedback], ...]
    expanded_nodes: int
    generated_nodes: int
    frontier_max: int

    def to_lines(self) -> List[str]:
        """Render the result as printable lines for reporting."""

        lines = [
            f"Solved: {'yes' if self.success else 'no'}",
            f"Guesses: {len(self.history)}",
            f"Nodes expanded: {self.expanded_nodes}",
            f"Nodes generated: {self.generated_nodes}",
            f"Max frontier size: {self.frontier_max}",
        ]
        for guess, feedback in self.history:
            marks = ''.join(mark.to_symbol() for mark in feedback)
            lines.append(f"  {guess.upper()} -> {marks}")
        return lines


@dataclass
class SearchNode:
    """Container for a search frontier element."""

    knowledge: WordleKnowledge
    history: Tuple[Tuple[str, Feedback], ...]
    candidates: Tuple[str, ...]
    guessed: frozenset[str]
    cost: int = 0

    @property
    def depth(self) -> int:
        """Return the depth (number of guesses)."""

        return len(self.history)


class GraphSearchSolver:
    """Base class implementing common search mechanics."""

    name = "graph-search"

    def __init__(self, word_length: int = 5) -> None:
        self.word_length = word_length

    def solve(self, answer: str, word_pool: Sequence[str], max_attempts: int = 6) -> SolverResult:
        """Run the specific frontier strategy against an answer.

        Args:
            answer: The hidden solution word.
            word_pool: Available guess candidates.
            max_attempts: Maximum depth allowed by the puzzle.
        """

        root_knowledge = WordleKnowledge(word_length=self.word_length)
        root_candidates = tuple(word_pool)
        root = SearchNode(
            knowledge=root_knowledge,
            history=tuple(),
            candidates=root_candidates,
            guessed=frozenset(),
            cost=0,
        )

        frontier = self._create_frontier()
        sequence = 0
        self._push_frontier(frontier, root, priority=self._priority(root), sequence=sequence)
        sequence += 1
        visited: set[tuple] = set()
        expanded_nodes = 0
        generated_nodes = 0
        frontier_max = 1

        while not self._frontier_empty(frontier):
            node = self._pop_frontier(frontier)
            signature = (node.knowledge.signature(), tuple(sorted(node.guessed)))
            if signature in visited:
                continue
            visited.add(signature)
            expanded_nodes += 1

            if node.history and node.history[-1][0] == answer:
                return SolverResult(True, node.history, expanded_nodes, generated_nodes, frontier_max)

            if node.depth >= max_attempts:
                continue

            for guess in node.candidates:
                if guess in node.guessed:
                    continue
                feedback = evaluate_guess(answer, guess)
                new_history = node.history + ((guess, feedback),)
                new_knowledge = node.knowledge.clone()
                new_knowledge.incorporate(guess, feedback)
                new_candidates = tuple(new_knowledge.candidate_filter(list(word_pool)))
                new_node = SearchNode(
                    knowledge=new_knowledge,
                    history=new_history,
                    candidates=new_candidates,
                    guessed=node.guessed.union({guess}),
                    cost=node.cost + 1,
                )
                generated_nodes += 1
                self._push_frontier(frontier, new_node, priority=self._priority(new_node), sequence=sequence)
                sequence += 1
            frontier_max = max(frontier_max, self._frontier_size(frontier))

        return SolverResult(False, tuple(), expanded_nodes, generated_nodes, frontier_max)

    # --- Frontier management hooks -------------------------------------------------
    def _create_frontier(self):
        raise NotImplementedError

    def _push_frontier(self, frontier, node: SearchNode, priority: float, sequence: int) -> None:
        raise NotImplementedError

    def _pop_frontier(self, frontier) -> SearchNode:
        raise NotImplementedError

    def _frontier_empty(self, frontier) -> bool:
        raise NotImplementedError

    def _frontier_size(self, frontier) -> int:
        raise NotImplementedError

    def _priority(self, node: SearchNode) -> float:
        return node.cost


class BFSSolver(GraphSearchSolver):
    """Breadth-first search solver."""

    name = "bfs"

    def _create_frontier(self):  # type: ignore[override]
        return deque()

    def _push_frontier(self, frontier, node: SearchNode, priority: float, sequence: int) -> None:  # type: ignore[override]
        frontier.append(node)

    def _pop_frontier(self, frontier) -> SearchNode:  # type: ignore[override]
        return frontier.popleft()

    def _frontier_empty(self, frontier) -> bool:  # type: ignore[override]
        return not frontier

    def _frontier_size(self, frontier) -> int:  # type: ignore[override]
        return len(frontier)

    def _priority(self, node: SearchNode) -> float:  # type: ignore[override]
        return node.depth


class DFSSolver(GraphSearchSolver):
    """Depth-first search solver."""

    name = "dfs"

    def _create_frontier(self):  # type: ignore[override]
        return []

    def _push_frontier(self, frontier, node: SearchNode, priority: float, sequence: int) -> None:  # type: ignore[override]
        frontier.append(node)

    def _pop_frontier(self, frontier) -> SearchNode:  # type: ignore[override]
        return frontier.pop()

    def _frontier_empty(self, frontier) -> bool:  # type: ignore[override]
        return not frontier

    def _frontier_size(self, frontier) -> int:  # type: ignore[override]
        return len(frontier)

    def _priority(self, node: SearchNode) -> float:  # type: ignore[override]
        return -node.depth


class UCSSolver(GraphSearchSolver):
    """Uniform cost search solver (cost == number of guesses)."""

    name = "ucs"

    def _create_frontier(self):  # type: ignore[override]
        return []

    def _push_frontier(self, frontier, node: SearchNode, priority: float, sequence: int) -> None:  # type: ignore[override]
        heapq.heappush(frontier, (priority, sequence, node))

    def _pop_frontier(self, frontier) -> SearchNode:  # type: ignore[override]
        _, _, node = heapq.heappop(frontier)
        return node

    def _frontier_empty(self, frontier) -> bool:  # type: ignore[override]
        return not frontier

    def _frontier_size(self, frontier) -> int:  # type: ignore[override]
        return len(frontier)

    def _priority(self, node: SearchNode) -> float:  # type: ignore[override]
        return float(node.cost)


class AStarSolver(GraphSearchSolver):
    """A* search solver using the candidate pool size as heuristic."""

    name = "astar"

    def _create_frontier(self):  # type: ignore[override]
        return []

    def _push_frontier(self, frontier, node: SearchNode, priority: float, sequence: int) -> None:  # type: ignore[override]
        heapq.heappush(frontier, (priority, sequence, node))

    def _pop_frontier(self, frontier) -> SearchNode:  # type: ignore[override]
        _, _, node = heapq.heappop(frontier)
        return node

    def _frontier_empty(self, frontier) -> bool:  # type: ignore[override]
        return not frontier

    def _frontier_size(self, frontier) -> int:  # type: ignore[override]
        return len(frontier)

    def _priority(self, node: SearchNode) -> float:  # type: ignore[override]
        heuristic = len(node.candidates) / max(1, self.word_length)
        return node.cost + heuristic


SOLVERS: dict[str, GraphSearchSolver] = {
    solver.name: solver
    for solver in (BFSSolver(), DFSSolver(), UCSSolver(), AStarSolver())
}


def available_solvers() -> Iterable[str]:
    """Return the names of the registered solvers."""

    return SOLVERS.keys()


def get_solver(name: str) -> GraphSearchSolver:
    """Retrieve a solver instance by name."""

    try:
        return SOLVERS[name]
    except KeyError as exc:
        raise ValueError(f"Unknown solver: {name}") from exc
