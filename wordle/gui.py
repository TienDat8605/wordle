"""Tkinter-based GUI for playing and visualising Wordle solvers."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from typing import List, Tuple

from .feedback import Mark
from .game import WordleGame
from .solver import SOLVERS, SolverResult, get_solver
from .words import WORD_LIST


class WordleGUI:
    """Main application window for the Wordle game."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Wordle AI Studio")
        self.root.resizable(False, False)

        self.game = WordleGame()
        self.board_labels: List[List[tk.Label]] = []
        self.status_var = tk.StringVar(value="Welcome to Wordle AI Studio!")
        self.solver_var = tk.StringVar(value="bfs")
        self.animating = False
        self.pending_animation: list[Tuple[str, List[Mark]]] = []

        self._build_widgets()
        self._render_board()

    def _build_widgets(self) -> None:
        board_frame = tk.Frame(self.root, padx=10, pady=10)
        board_frame.grid(row=0, column=0, columnspan=3)

        for row in range(self.game.max_attempts):
            row_labels: List[tk.Label] = []
            for col in range(len(self.game.answer)):
                cell = tk.Label(
                    board_frame,
                    text=" ",
                    width=4,
                    height=2,
                    font=("Helvetica", 20, "bold"),
                    relief="groove",
                    bg="#121213",
                    fg="#d7dadc",
                )
                cell.grid(row=row, column=col, padx=3, pady=3)
                row_labels.append(cell)
            self.board_labels.append(row_labels)

        control_frame = tk.Frame(self.root, padx=10, pady=5)
        control_frame.grid(row=1, column=0, sticky="ew")

        tk.Label(control_frame, text="Guess:").grid(row=0, column=0)
        self.guess_var = tk.StringVar()
        self.guess_entry = tk.Entry(control_frame, textvariable=self.guess_var, font=("Helvetica", 14))
        self.guess_entry.grid(row=0, column=1)
        self.guess_entry.bind("<Return>", lambda _: self.submit_guess())

        submit_btn = tk.Button(control_frame, text="Submit", command=self.submit_guess)
        submit_btn.grid(row=0, column=2, padx=5)

        solver_frame = tk.Frame(self.root, padx=10, pady=5)
        solver_frame.grid(row=2, column=0, sticky="ew")

        tk.Label(solver_frame, text="Solver:").grid(row=0, column=0)
        solver_names = list(SOLVERS.keys())
        solver_menu = tk.OptionMenu(solver_frame, self.solver_var, *solver_names)
        solver_menu.grid(row=0, column=1)

        solver_btn = tk.Button(solver_frame, text="Run Solver", command=self.run_solver)
        solver_btn.grid(row=0, column=2, padx=5)

        new_game_btn = tk.Button(solver_frame, text="New Game", command=self.new_game)
        new_game_btn.grid(row=0, column=3, padx=5)

        status_label = tk.Label(self.root, textvariable=self.status_var, anchor="w", padx=10)
        status_label.grid(row=3, column=0, sticky="ew")

    def _render_board(self) -> None:
        history = self.game.state.history
        for row, row_labels in enumerate(self.board_labels):
            if row < len(history):
                guess, feedback = history[row]
                for col, label in enumerate(row_labels):
                    label.config(text=guess[col].upper(), bg=feedback[col].to_color())
            else:
                for label in row_labels:
                    label.config(text=" ", bg="#121213")
        if self.game.state.is_won:
            self.status_var.set("Solved! 🎉")
        elif self.game.state.is_lost:
            self.status_var.set(f"Out of guesses. Answer was {self.game.answer.upper()}.")
        else:
            self.status_var.set(f"Attempts left: {self.game.state.remaining_attempts}")

    def submit_guess(self) -> None:
        if self.animating:
            return
        guess = self.guess_var.get().strip().lower()
        if len(guess) != len(self.game.answer):
            messagebox.showinfo("Invalid Guess", "Enter a five-letter word from the list.")
            return
        if not self.game.valid_guess(guess):
            messagebox.showinfo("Invalid Guess", "Word not in curated list.")
            return
        try:
            self.game.apply_guess(guess)
        except RuntimeError as exc:
            messagebox.showinfo("Game Finished", str(exc))
            return
        self.guess_var.set("")
        self._render_board()

    def new_game(self) -> None:
        if self.animating:
            return
        self.game.reset()
        self.guess_var.set("")
        self._render_board()

    def run_solver(self) -> None:
        if self.animating:
            return
        solver = get_solver(self.solver_var.get())
        simulation = WordleGame(answer=self.game.answer, word_list=WORD_LIST)
        result = solver.solve(simulation.answer, simulation.word_list)
        if not result.success:
            messagebox.showinfo("Solver", "Solver failed to find the answer within the attempt limit.")
            return
        self.pending_animation = [(guess, list(feedback)) for guess, feedback in result.history]
        self.game.reset(answer=simulation.answer)
        self.animating = True
        self._animate_step()

    def _animate_step(self) -> None:
        if not self.pending_animation:
            self.animating = False
            self._render_board()
            return
        guess, feedback = self.pending_animation.pop(0)
        self.game.apply_guess(guess)
        self._render_board()
        self.root.after(750, self._animate_step)

    def run(self) -> None:
        """Start the Tkinter main loop."""

        self.root.mainloop()


def launch_gui() -> None:
    """Convenience function for launching the GUI."""

    app = WordleGUI()
    app.run()
