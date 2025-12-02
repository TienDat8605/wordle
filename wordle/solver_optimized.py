"""Optimized search-based solvers with performance enhancements."""

from __future__ import annotations

import heapq
import math
import random
from collections import Counter, deque
from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence, Set, Tuple

from .feedback import Feedback, Mark
from .feedback_table import FeedbackTable
from .knowledge import WordleKnowledge


@dataclass
class SolverResult:
    """Outcome summary for a solver run."""

    success: bool
    history: Tuple[Tuple[str, Feedback], ...]
    expanded_nodes: int
    generated_nodes: int
    frontier_max: int
    explored_words: Optional[List[str]] = None  # Words explored during search
    final_path: Optional[List[str]] = None  # Final path taken (guesses only)
    starting_candidates: Optional[List[str]] = None  # Starting candidates for this game

    def __post_init__(self):
        """Initialize derived fields if not provided."""
        if self.final_path is None:
            self.final_path = [guess for guess, _ in self.history]
        if self.explored_words is None:
            self.explored_words = []

    def to_lines(self) -> List[str]:
        """Render the result as printable lines for reporting."""

        lines = [
            f"Solved: {'yes' if self.success else 'no'}",
            f"Guesses: {len(self.history)}",
            f"Nodes expanded: {self.expanded_nodes}",
            f"Nodes generated: {self.generated_nodes}",
            f"Max frontier size: {self.frontier_max}",
        ]
        if self.explored_words:
            lines.append(f"Words explored: {len(self.explored_words)}")
        if self.final_path:
            lines.append(f"Final path: {' -> '.join(w.upper() for w in self.final_path)}")
        for guess, feedback in self.history:
            marks = ''.join(mark.to_symbol() for mark in feedback)
            lines.append(f"  {guess.upper()} -> {marks}")
        return lines


@dataclass(frozen=True)
class CompactState:
    """Compact, hashable state representation using history signature."""

    history: Tuple[Tuple[str, Tuple[Mark, ...]], ...]
    remaining_count: int

    @classmethod
    def from_history(cls, history: Tuple[Tuple[str, Feedback], ...], remaining: int) -> CompactState:
        """Create a compact state from full history."""
        compact_history = tuple(
            (guess, tuple(feedback)) for guess, feedback in history
        )
        return cls(history=compact_history, remaining_count=remaining)


# ============================================================================
# COST FUNCTIONS (for UCS and g(n) in A*)
# ============================================================================

def cost_constant(before_count: int, after_count: int, word_length: int = 5) -> float:
    """C1: Constant cost = 1 (baseline, makes UCS behave like BFS)."""
    return 1.0


def cost_candidate_reduction(before_count: int, after_count: int, word_length: int = 5) -> float:
    """C2: Cost = 1 + (after/before). Rewards guesses that shrink candidate space."""
    if before_count == 0:
        return 1.0
    return 1.0 + (after_count / before_count)


# Available cost functions
COST_FUNCTIONS = {
    'constant': cost_constant,
    'reduction': cost_candidate_reduction,
}


# ============================================================================
# HEURISTIC FUNCTIONS (for A* only, in f(n) = g(n) + h(n))
# Only admissible heuristics are included to guarantee optimal solutions
# ============================================================================

def heuristic_log2(remaining: int, word_length: int = 5) -> float:
    """H1: log2(remaining) - Optimal admissible heuristic.
    
    Represents the minimum number of binary splits needed to narrow down
    to a single candidate. Never overestimates the true cost.
    """
    return math.log2(max(1, remaining))


# Available heuristic functions (admissible only)
HEURISTIC_FUNCTIONS = {
    'log2': heuristic_log2,
}


# ============================================================================
# SOLVER BASE CLASS
# ============================================================================

class OptimizedGraphSearchSolver:
    """Base class for optimized graph search with feedback caching."""

    name = "optimized-graph-search"
    
    # Class-level shared feedback table (built once, used by all solver instances)
    _shared_feedback_table: FeedbackTable | None = None
    _shared_word_list: List[str] = []

    def __init__(self, word_length: int = 5, max_branching: int = 50, 
                 cost_fn: str = 'constant') -> None:
        """Initialize solver with branching limit and cost function.
        
        Args:
            word_length: Length of words in the puzzle.
            max_branching: Maximum number of guesses to consider per state.
            cost_fn: Name of cost function to use (for UCS and A*).
        """
        self.word_length = word_length
        self.max_branching = max_branching
        self.cost_fn_name = cost_fn
        self.cost_fn = COST_FUNCTIONS.get(cost_fn, cost_constant)

    def solve(
        self, answer: str, word_pool: Sequence[str], max_attempts: int = 6,
        starting_candidates: Optional[List[str]] = None
    ) -> SolverResult:
        """Run the specific frontier strategy against an answer.

        Args:
            answer: The hidden solution word.
            word_pool: Available guess candidates.
            max_attempts: Maximum depth allowed by the puzzle.
            starting_candidates: Optional list of starting words to consider for first guess.
                               If None, randomly selects 30 words from word_pool.
        """
        # Generate random starting candidates if not provided
        if starting_candidates is None:
            starting_candidates = random.sample(
                list(word_pool), min(30, len(word_pool))
            )
        
        # Build feedback table once per word pool (shared across all solver instances)
        if (
            OptimizedGraphSearchSolver._shared_feedback_table is None
            or OptimizedGraphSearchSolver._shared_word_list != list(word_pool)
        ):
            OptimizedGraphSearchSolver._shared_word_list = list(word_pool)
            # Use sparse graph with max 200 connections per word to avoid OOM
            OptimizedGraphSearchSolver._shared_feedback_table = FeedbackTable(
                OptimizedGraphSearchSolver._shared_word_list, max_connections=200
            )

        word_list = OptimizedGraphSearchSolver._shared_word_list
        feedback_table = OptimizedGraphSearchSolver._shared_feedback_table

        # Convert to indices for faster operations
        word_to_idx = {w: i for i, w in enumerate(word_list)}
        answer_idx = word_to_idx[answer.lower()]
        
        # Store starting candidates as indices
        self.starting_candidates_indices = {word_to_idx[w.lower()] for w in starting_candidates}

        # Root state: all words are possible
        root_state = CompactState.from_history(tuple(), len(word_list))
        frontier = self._create_frontier()
        sequence = 0
        self._push_frontier(frontier, root_state, tuple(), set(range(len(word_list))), 0, sequence)
        sequence += 1

        visited: Set[CompactState] = set()
        expanded_nodes = 0
        generated_nodes = 0
        frontier_max = 1
        explored_words: List[str] = []  # Track all words explored

        while not self._frontier_empty(frontier):
            state, history, possible_indices, depth = self._pop_frontier(frontier)
            
            if state in visited:
                continue
            visited.add(state)
            expanded_nodes += 1

            # Check if we found the answer
            if history and word_to_idx[history[-1][0]] == answer_idx:
                final_path = [guess for guess, _ in history]
                return SolverResult(
                    True, history, expanded_nodes, generated_nodes, 
                    frontier_max, explored_words, final_path, starting_candidates
                )

            if depth >= max_attempts:
                continue

            # Select promising guesses (limit branching)
            candidate_indices = self._select_guesses(possible_indices, depth)

            for guess_idx in candidate_indices:
                guess = word_list[guess_idx]
                
                # Track explored words
                if guess not in explored_words:
                    explored_words.append(guess)
                
                feedback = feedback_table.get_feedback(guess, answer)
                
                # Fast filtering using precomputed feedback
                new_possible = self._filter_candidates_fast(
                    possible_indices, guess_idx, feedback, word_list, feedback_table
                )

                if not new_possible:
                    continue

                new_history = history + ((guess, feedback),)
                new_state = CompactState.from_history(new_history, len(new_possible))
                
                # Compute step cost
                step_cost = self._compute_step_cost(
                    guess, len(possible_indices), len(new_possible)
                )
                new_depth = depth + step_cost

                generated_nodes += 1
                priority = self._priority(new_state, new_depth, len(new_possible))
                self._push_frontier(
                    frontier, new_state, new_history, new_possible, new_depth, sequence
                )
                sequence += 1

            frontier_max = max(frontier_max, self._frontier_size(frontier))

        return SolverResult(
            False, tuple(), expanded_nodes, generated_nodes, 
            frontier_max, explored_words, [], starting_candidates
        )

    def _select_guesses(self, possible_indices: Set[int], depth: float) -> List[int]:
        """Select subset of promising guesses to limit branching.
        
        Strategy: At depth=0 (root state), use starting candidates.
                 At depth>0, prioritize words from the remaining possible set.
        """
        if depth == 0:
            # Root state: use only starting candidates
            candidates = list(self.starting_candidates_indices & possible_indices)
        else:
            # Subsequent states: use remaining words
            candidates = list(possible_indices)
        
        if len(candidates) <= self.max_branching:
            return candidates
        
        return candidates[:self.max_branching]
    
    def _compute_step_cost(self, guess: str, before_count: int, after_count: int) -> float:
        """Compute the cost of taking this guess step.
        
        Args:
            guess: The word being guessed.
            before_count: Number of candidates before this guess.
            after_count: Number of candidates after this guess.
        
        Returns:
            The step cost according to the selected cost function.
        """
        # Get unique letters and check for duplicates
        unique_letters = len(set(guess))
        has_duplicates = unique_letters < len(guess)
        
        # Call the cost function
        return self.cost_fn(before_count, after_count, self.word_length)

    def _filter_candidates(
        self, possible_indices: Set[int], guess_idx: int, feedback: Feedback
    ) -> Set[int]:
        """Filter candidates that match the observed feedback."""
        word_list = OptimizedGraphSearchSolver._shared_word_list
        feedback_table = OptimizedGraphSearchSolver._shared_feedback_table
        assert feedback_table is not None
        
        result = set()
        for idx in possible_indices:
            target = word_list[idx]
            guess = word_list[guess_idx]
            if feedback_table.get_feedback(guess, target) == feedback:
                result.add(idx)
        return result
    
    @staticmethod
    def _filter_candidates_fast(
        possible_indices: Set[int],
        guess_idx: int,
        feedback: Feedback,
        word_list: List[str],
        feedback_table: FeedbackTable,
    ) -> Set[int]:
        """Static method for fast candidate filtering."""
        result = set()
        for idx in possible_indices:
            target = word_list[idx]
            guess = word_list[guess_idx]
            if feedback_table.get_feedback(guess, target) == feedback:
                result.add(idx)
        return result

    # --- Frontier management hooks -------------------------------------------------
    def _create_frontier(self):
        raise NotImplementedError

    def _push_frontier(
        self,
        frontier,
        state: CompactState,
        history: Tuple[Tuple[str, Feedback], ...],
        possible: Set[int],
        depth: float,
        sequence: int,
    ) -> None:
        raise NotImplementedError

    def _pop_frontier(self, frontier) -> Tuple[CompactState, Tuple[Tuple[str, Feedback], ...], Set[int], float]:
        raise NotImplementedError

    def _frontier_empty(self, frontier) -> bool:
        raise NotImplementedError

    def _frontier_size(self, frontier) -> int:
        raise NotImplementedError

    def _priority(self, state: CompactState, depth: float, remaining: int) -> float:
        return float(depth)


class OptimizedBFS(OptimizedGraphSearchSolver):
    """Optimized breadth-first search."""

    name = "bfs-opt"

    def _create_frontier(self):
        return deque()

    def _push_frontier(self, frontier, state, history, possible, depth, sequence):
        frontier.append((state, history, possible, depth))

    def _pop_frontier(self, frontier):
        return frontier.popleft()

    def _frontier_empty(self, frontier):
        return not frontier

    def _frontier_size(self, frontier):
        return len(frontier)


class OptimizedDFS(OptimizedGraphSearchSolver):
    """Optimized depth-first search."""

    name = "dfs-opt"

    def _create_frontier(self):
        return []

    def _push_frontier(self, frontier, state, history, possible, depth, sequence):
        frontier.append((state, history, possible, depth))

    def _pop_frontier(self, frontier):
        return frontier.pop()

    def _frontier_empty(self, frontier):
        return not frontier

    def _frontier_size(self, frontier):
        return len(frontier)


class OptimizedUCS(OptimizedGraphSearchSolver):
    """Optimized uniform cost search with configurable cost function."""

    name = "ucs-opt"

    def __init__(self, word_length: int = 5, max_branching: int = 50, cost_fn: str = 'constant'):
        """Initialize UCS with cost function."""
        super().__init__(word_length, max_branching, cost_fn)

    def _create_frontier(self):
        return []

    def _push_frontier(self, frontier, state, history, possible, depth, sequence):
        priority = float(depth)
        heapq.heappush(frontier, (priority, sequence, state, history, possible, depth))

    def _pop_frontier(self, frontier):
        _, _, state, history, possible, depth = heapq.heappop(frontier)
        return state, history, possible, depth

    def _frontier_empty(self, frontier):
        return not frontier

    def _frontier_size(self, frontier):
        return len(frontier)


class OptimizedAStar(OptimizedGraphSearchSolver):
    """Optimized A* search with configurable cost and heuristic functions."""

    name = "astar-opt"

    def __init__(self, word_length: int = 5, max_branching: int = 50, 
                 cost_fn: str = 'constant', heuristic_fn: str = 'log2'):
        """Initialize A* with cost and heuristic functions.
        
        Args:
            word_length: Length of words in the puzzle.
            max_branching: Maximum number of guesses to consider per state.
            cost_fn: Name of cost function to use.
            heuristic_fn: Name of heuristic function to use.
        """
        super().__init__(word_length, max_branching, cost_fn)
        self.heuristic_fn_name = heuristic_fn
        self.heuristic_fn = HEURISTIC_FUNCTIONS.get(heuristic_fn, heuristic_log2)

    def _create_frontier(self):
        return []

    def _push_frontier(self, frontier, state, history, possible, depth, sequence):
        priority = self._priority(state, depth, len(possible))
        heapq.heappush(frontier, (priority, sequence, state, history, possible, depth))

    def _pop_frontier(self, frontier):
        _, _, state, history, possible, depth = heapq.heappop(frontier)
        return state, history, possible, depth

    def _frontier_empty(self, frontier):
        return not frontier

    def _frontier_size(self, frontier):
        return len(frontier)

    def _priority(self, state: CompactState, depth: float, remaining: int) -> float:
        """A* priority: g(n) + h(n) where g is cost and h is heuristic."""
        heuristic = self.heuristic_fn(remaining, self.word_length)
        return depth + heuristic


# Registry of optimized solvers with various configurations
def _build_solver_registry():
    """Build registry with all solver configurations."""
    registry = {}
    
    # BFS and DFS (don't use cost/heuristic)
    registry['bfs-opt'] = OptimizedBFS(max_branching=30)
    registry['dfs-opt'] = OptimizedDFS(max_branching=30)
    
    # UCS with different cost functions
    for cost_name in COST_FUNCTIONS.keys():
        solver = OptimizedUCS(max_branching=30, cost_fn=cost_name)
        solver.name = f"ucs-{cost_name}"
        registry[solver.name] = solver
    
    # A* with different cost and heuristic combinations
    for cost_name in COST_FUNCTIONS.keys():
        for heuristic_name in HEURISTIC_FUNCTIONS.keys():
            solver = OptimizedAStar(max_branching=30, cost_fn=cost_name, heuristic_fn=heuristic_name)
            solver.name = f"astar-{cost_name}-{heuristic_name}"
            registry[solver.name] = solver
    
    return registry


OPTIMIZED_SOLVERS = _build_solver_registry()
