"""Tkinter-based GUI for playing and visualising Wordle solvers."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from typing import List, Tuple

from .feedback import Mark
from .game import WordleGame
from .solver_optimized import OPTIMIZED_SOLVERS
from .words import WORD_LIST


class WordleGUI:
    """Main application window for the Wordle game."""

    # Friendly display names for solvers
    SOLVER_DISPLAY_NAMES = {
        "bfs-opt": "BFS",
        "dfs-opt": "DFS",
        "ucs-opt": "UCS",
        "astar-opt": "A*",
    }

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Wordle AI Studio")
        self.root.geometry("800x900")  # Initial size
        self.root.minsize(700, 800)  # Minimum size
        self.root.resizable(True, True)

        self.game = WordleGame()
        self.board_entries: List[List[tk.Entry]] = []
        self.status_var = tk.StringVar(value="Welcome to Wordle AI Studio!")
        self.solver_var = tk.StringVar(value="BFS")
        self.animating = False
        self.pending_animation: list[Tuple[str, List[Mark]]] = []
        self.current_row = 0
        self.current_col = 0

        self._build_widgets()
        self._render_board()

    def _build_widgets(self) -> None:
        # Configure grid weights for resizing
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=0)
        self.root.grid_rowconfigure(2, weight=0)
        self.root.grid_rowconfigure(3, weight=2)
        self.root.grid_columnconfigure(0, weight=1)

        # ==== Game Board ====
        board_frame = tk.Frame(self.root, bg="white")
        board_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        # Center the board grid
        board_frame.grid_rowconfigure(0, weight=1)
        board_frame.grid_columnconfigure(0, weight=1)

        grid_container = tk.Frame(board_frame, bg="white")
        grid_container.grid(row=0, column=0)

        # Create 6x5 grid of Entry widgets (bigger blocks with 36pt font)
        for row in range(6):
            row_entries = []
            for col in range(5):
                entry = tk.Entry(
                    grid_container,
                    width=2,
                    font=("Helvetica", 36, "bold"),
                    justify="center",
                    bg="white",
                    fg="black",
                    disabledbackground="white",
                    disabledforeground="black",
                    relief="solid",
                    borderwidth=2,
                    highlightthickness=0,
                )
                entry.grid(row=row, column=col, padx=3, pady=3)
                row_entries.append(entry)
            self.board_entries.append(row_entries)

        # Bind keyboard events to the first row
        for entry in self.board_entries[0]:
            entry.bind("<KeyPress>", self._on_key_press)
            entry.bind("<BackSpace>", self._on_backspace)
            entry.bind("<Return>", self._on_return)

        # ==== Status Label ====
        status_label = tk.Label(
            self.root,
            textvariable=self.status_var,
            font=("Helvetica", 14, "bold"),
            bg="#f8f9fa",
            fg="#333",
            pady=10,
        )
        status_label.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))

        # ==== Controls ====
        controls_frame = tk.Frame(self.root, bg="#f8f9fa")
        controls_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        controls_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Solver dropdown
        tk.Label(
            controls_frame,
            text="Solver:",
            font=("Helvetica", 12),
            bg="#f8f9fa",
        ).grid(row=0, column=0, padx=5, sticky="e")

        solver_menu = tk.OptionMenu(
            controls_frame,
            self.solver_var,
            *self.SOLVER_DISPLAY_NAMES.values(),
        )
        solver_menu.config(font=("Helvetica", 11), width=8)
        solver_menu.grid(row=0, column=1, padx=5, sticky="w")

        # Run Solver button
        run_solver_btn = tk.Button(
            controls_frame,
            text="Run Solver",
            command=self.run_solver,
            font=("Helvetica", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            padx=15,
            pady=5,
            relief="raised",
        )
        run_solver_btn.grid(row=0, column=2, padx=5)

        # New Game button
        new_game_btn = tk.Button(
            controls_frame,
            text="New Game",
            command=self.new_game,
            font=("Helvetica", 12, "bold"),
            bg="#2196F3",
            fg="white",
            padx=15,
            pady=5,
            relief="raised",
        )
        new_game_btn.grid(row=0, column=3, padx=5)

        # Benchmark button
        benchmark_btn = tk.Button(
            controls_frame,
            text="Benchmark",
            command=self.show_benchmark_dialog,
            font=("Helvetica", 12, "bold"),
            bg="#FF9800",
            fg="white",
            padx=15,
            pady=5,
            relief="raised",
        )
        benchmark_btn.grid(row=0, column=4, padx=5)

        # ==== Benchmark Results Area ====
        results_frame = tk.Frame(self.root, bg="#f8f9fa")
        results_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=(0, 20))
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)

        results_scroll = tk.Scrollbar(results_frame)
        results_scroll.grid(row=0, column=1, sticky="ns")

        self.results_text = tk.Text(
            results_frame,
            height=12,
            font=("Courier", 10),
            yscrollcommand=results_scroll.set,
            wrap=tk.WORD,
            bg="#f8f9fa",
        )
        self.results_text.grid(row=0, column=0, sticky="nsew")
        results_scroll.config(command=self.results_text.yview)
        self.results_text.insert("1.0", "Click 'Benchmark' to run solver performance tests...")
        self.results_text.config(state="disabled")

    def _on_key_press(self, event: tk.Event) -> str:
        """Handle single character input with auto-advance."""
        char = event.char.upper()
        
        # Only allow letters
        if not char.isalpha() or len(char) != 1:
            return "break"
        
        # Don't allow input during animation or game over
        if self.animating or self.game.state.is_won or self.game.state.is_lost:
            return "break"
        
        # Find current position
        current_entry: tk.Entry = event.widget  # type: ignore
        row_idx = -1
        col_idx = -1
        
        for r, row_entries in enumerate(self.board_entries):
            if current_entry in row_entries:
                row_idx = r
                col_idx = row_entries.index(current_entry)
                break
        
        # Only allow input in current row
        if row_idx != self.current_row:
            return "break"
        
        # Clear and insert the character
        current_entry.delete(0, tk.END)
        current_entry.insert(0, char)
        
        # Move to next cell if not at end of row
        if col_idx < 4:
            next_entry = self.board_entries[row_idx][col_idx + 1]
            next_entry.focus_set()
            next_entry.icursor(tk.END)
        
        return "break"

    def _on_backspace(self, event: tk.Event) -> str:
        """Handle backspace - delete current cell or move to previous."""
        if self.animating or self.game.state.is_won or self.game.state.is_lost:
            return "break"
        
        current_entry: tk.Entry = event.widget  # type: ignore
        row_idx = -1
        col_idx = -1
        
        for r, row_entries in enumerate(self.board_entries):
            if current_entry in row_entries:
                row_idx = r
                col_idx = row_entries.index(current_entry)
                break
        
        # Only allow backspace in current row
        if row_idx != self.current_row:
            return "break"
        
        # If current cell has text, delete it
        if current_entry.get():
            current_entry.delete(0, tk.END)
        # Otherwise, move to previous cell and delete
        elif col_idx > 0:
            prev_entry = self.board_entries[row_idx][col_idx - 1]
            prev_entry.delete(0, tk.END)
            prev_entry.focus_set()
            prev_entry.icursor(tk.END)
        
        return "break"

    def _on_return(self, event: tk.Event) -> str:
        """Handle Enter key - submit guess if row is complete."""
        if self.animating or self.game.state.is_won or self.game.state.is_lost:
            return "break"
        
        # Check if current row is complete
        guess = "".join(
            entry.get().strip().upper()
            for entry in self.board_entries[self.current_row]
        )
        
        if len(guess) == 5:
            self.submit_guess()
        
        return "break"

    def _render_board(self) -> None:
        """Update the board display based on game state."""
        history = self.game.state.history
        
        for row, row_entries in enumerate(self.board_entries):
            if row < len(history):
                # Show completed guess with feedback
                guess, feedback = history[row]
                for col, entry in enumerate(row_entries):
                    entry.config(state="normal")  # Enable to allow modification
                    entry.delete(0, tk.END)
                    entry.insert(0, guess[col].upper())
                    entry.config(
                        bg=feedback[col].to_color(),
                        state="disabled",
                        disabledbackground=feedback[col].to_color(),
                    )
                    # Unbind events from completed rows
                    entry.unbind("<KeyPress>")
                    entry.unbind("<BackSpace>")
                    entry.unbind("<Return>")
            else:
                # Clear and configure row (for all rows >= len(history))
                for entry in row_entries:
                    entry.config(state="normal")  # Enable to allow modification
                    entry.delete(0, tk.END)
                    entry.config(
                        bg="white",
                        disabledbackground="white",
                    )
                    
                    # Enable input only for current row
                    if row == len(history):
                        entry.config(state="normal")
                        # Bind events
                        entry.bind("<KeyPress>", self._on_key_press)
                        entry.bind("<BackSpace>", self._on_backspace)
                        entry.bind("<Return>", self._on_return)
                    else:
                        entry.config(state="disabled")
                        # Unbind events
                        entry.unbind("<KeyPress>")
                        entry.unbind("<BackSpace>")
                        entry.unbind("<Return>")
        
        self.current_row = len(history)
        
        # Focus first cell of current row
        if self.current_row < 6:
            self.board_entries[self.current_row][0].focus_set()
        
        # Update status
        if self.game.state.is_won:
            self.status_var.set("Solved!")
        elif self.game.state.is_lost:
            self.status_var.set(f"Out of guesses. Answer was {self.game.answer.upper()}.")
        else:
            self.status_var.set(f"Attempts left: {self.game.state.remaining_attempts}")

    def submit_guess(self) -> None:
        """Submit the current guess."""
        if self.animating or self.current_row >= self.game.max_attempts:
            return
        
        # Collect guess from current row
        guess = "".join(
            entry.get().strip().lower()
            for entry in self.board_entries[self.current_row]
        )
        
        if len(guess) != 5:
            messagebox.showinfo("Invalid Guess", "Enter a five-letter word.")
            return
        
        if not self.game.valid_guess(guess):
            messagebox.showinfo("Invalid Guess", "Word not in curated list.")
            return
        
        try:
            self.game.apply_guess(guess)
        except RuntimeError as exc:
            messagebox.showinfo("Game Finished", str(exc))
            return
        
        self._render_board()

    def new_game(self) -> None:
        """Start a new game."""
        if self.animating:
            return
        self.game.reset()
        self._render_board()
        
        # Clear benchmark results
        self.results_text.config(state="normal")
        self.results_text.delete("1.0", tk.END)
        self.results_text.insert("1.0", "Click 'Benchmark' to run solver performance tests...")
        self.results_text.config(state="disabled")
        
        # Reset status message
        self.status_var.set(f"Attempts left: {self.game.state.remaining_attempts}")

    def run_solver(self) -> None:
        """Run the selected solver with animation."""
        if self.animating:
            return
        
        # Map display name back to internal solver key
        display_name = self.solver_var.get()
        solver_key = next(
            (k for k, v in self.SOLVER_DISPLAY_NAMES.items() if v == display_name),
            "bfs-opt"
        )
        
        solver = OPTIMIZED_SOLVERS[solver_key]
        simulation = WordleGame(answer=self.game.answer, word_list=WORD_LIST)
        result = solver.solve(simulation.answer, simulation.word_list)
        
        if not result.success:
            messagebox.showinfo("Solver", "Solver failed to find the answer within the attempt limit.")
            return
        
        # Display solver exploration info
        self.results_text.config(state="normal")
        self.results_text.delete("1.0", tk.END)
        
        result_lines = [
            f"Solver: {display_name}\n",
            f"Target word: {simulation.answer.upper()}\n",
            "=" * 80 + "\n\n",
            f"• Solved in {len(result.history)} guesses\n",
            f"• Nodes expanded: {result.expanded_nodes}\n",
            f"• Nodes generated: {result.generated_nodes}\n",
            f"• Max frontier size: {result.frontier_max}\n",
        ]
        
        if result.explored_words:
            result_lines.append(f"• Words explored: {len(result.explored_words)}\n\n")
            
            # Show first 40 explored words
            max_display = 40
            if len(result.explored_words) <= max_display:
                explored_str = ", ".join(w.upper() for w in result.explored_words)
            else:
                displayed = result.explored_words[:max_display]
                explored_str = ", ".join(w.upper() for w in displayed)
                explored_str += f", ... and {len(result.explored_words) - max_display} more"
            
            result_lines.append(f"Explored: {explored_str}\n\n")
        
        if result.final_path:
            path_str = " → ".join(w.upper() for w in result.final_path)
            result_lines.append(f"Solution path: {path_str}\n\n")
        
        result_lines.append("Guess details:\n")
        result_lines.append("-" * 80 + "\n")
        for i, (guess, feedback) in enumerate(result.history, 1):
            marks = ''.join(mark.to_symbol() for mark in feedback)
            result_lines.append(f"{i}. {guess.upper()} → {marks}\n")
        
        self.results_text.insert("1.0", "".join(result_lines))
        self.results_text.config(state="disabled")
        
        self.pending_animation = [(guess, list(feedback)) for guess, feedback in result.history]
        self.game.reset(answer=simulation.answer)
        self.animating = True
        self._animate_step()

    def _animate_step(self) -> None:
        """Animate one step of the solver solution."""
        if not self.pending_animation:
            self.animating = False
            self._render_board()
            return
        
        guess, feedback = self.pending_animation.pop(0)
        self.game.apply_guess(guess)
        self._render_board()
        self.root.after(750, self._animate_step)

    def show_benchmark_dialog(self) -> None:
        """Show dialog to configure and run benchmarks."""
        if self.animating:
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Run Benchmark")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (dialog.winfo_screenheight() // 2) - (200 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Samples input
        tk.Label(dialog, text="Number of samples:", font=("Helvetica", 11)).grid(
            row=0, column=0, padx=20, pady=10, sticky="e"
        )
        samples_var = tk.StringVar(value="3")
        samples_entry = tk.Entry(dialog, textvariable=samples_var, font=("Helvetica", 11), width=10)
        samples_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        # Seed input
        tk.Label(dialog, text="Random seed:", font=("Helvetica", 11)).grid(
            row=1, column=0, padx=20, pady=10, sticky="e"
        )
        seed_var = tk.StringVar(value="7")
        seed_entry = tk.Entry(dialog, textvariable=seed_var, font=("Helvetica", 11), width=10)
        seed_entry.grid(row=1, column=1, padx=10, pady=10, sticky="w")
        
        # Status label
        status_var = tk.StringVar(value="")
        status_label = tk.Label(dialog, textvariable=status_var, font=("Helvetica", 10), fg="blue")
        status_label.grid(row=2, column=0, columnspan=2, pady=5)
        
        # Buttons
        button_frame = tk.Frame(dialog)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        def run_benchmark():
            try:
                samples = int(samples_var.get())
                seed = int(seed_var.get())
                
                if samples < 1 or samples > 50:
                    messagebox.showerror("Invalid Input", "Samples must be between 1 and 50")
                    return
                
                status_var.set("Running benchmark...")
                dialog.update()
                
                # Import here to avoid circular dependency
                from .benchmark import run_benchmarks
                
                # Run benchmark
                stats = run_benchmarks(samples=samples, seed=seed)
                
                # Display results
                self.results_text.config(state="normal")
                self.results_text.delete("1.0", tk.END)
                
                result_lines = [
                    f"Benchmark Results (samples={samples}, seed={seed})\n",
                    "=" * 80 + "\n\n",
                ]
                
                headers = ["Solver", "Success", "Avg Time", "Max Time", "Avg Mem", "Max Mem", "Avg Nodes"]
                result_lines.append(" | ".join(f"{h:<10}" for h in headers) + "\n")
                result_lines.append("-" * 80 + "\n")
                
                for solver_name, stat in stats.items():
                    row = [
                        self.SOLVER_DISPLAY_NAMES.get(solver_name, solver_name).upper(),
                        f"{stat.success_rate * 100:.0f}%",
                        f"{stat.avg_time_ms:.2f}ms",
                        f"{stat.max_time_ms:.2f}ms",
                        f"{stat.avg_peak_kib:.1f}KB",
                        f"{stat.max_peak_kib:.1f}KB",
                        f"{stat.avg_nodes_expanded:.1f}",
                    ]
                    result_lines.append(" | ".join(f"{v:<10}" for v in row) + "\n")
                
                result_lines.append("\n" + "=" * 80 + "\n")
                
                self.results_text.insert("1.0", "".join(result_lines))
                self.results_text.config(state="disabled")
                
                dialog.destroy()
                messagebox.showinfo("Benchmark Complete", "Benchmark completed successfully!")
                
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter valid numbers")
            except Exception as e:
                messagebox.showerror("Error", f"Benchmark failed: {str(e)}")
                dialog.destroy()
        
        run_btn = tk.Button(
            button_frame,
            text="Run",
            command=run_benchmark,
            font=("Helvetica", 11),
            padx=20,
        )
        run_btn.grid(row=0, column=0, padx=5)
        
        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy,
            font=("Helvetica", 11),
            padx=20,
        )
        cancel_btn.grid(row=0, column=1, padx=5)

    def run(self) -> None:
        """Start the Tkinter main loop."""
        self.root.mainloop()


def launch_gui() -> None:
    """Convenience function for launching the GUI."""
    app = WordleGUI()
    app.run()
