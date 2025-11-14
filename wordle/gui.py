"""Tkinter-based GUI for playing and visualising Wordle solvers."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from typing import List, Tuple

from .feedback import Mark
from .game import WordleGame
from .solver_optimized import OPTIMIZED_SOLVERS, COST_FUNCTIONS, HEURISTIC_FUNCTIONS
from .words import WORD_LIST


class WordleGUI:
    """Main application window for the Wordle game."""

    # Friendly display names for solvers
    SOLVER_DISPLAY_NAMES = {
        "BFS": "bfs-opt",
        "DFS": "dfs-opt",
        "UCS": "ucs",
        "A*": "astar",
    }

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Wordle AI Studio")
        self.root.geometry("900x950")  # Initial size (larger for more controls)
        self.root.minsize(800, 900)  # Minimum size
        self.root.resizable(True, True)

        self.game = WordleGame()
        self.board_entries: List[List[tk.Entry]] = []
        self.status_var = tk.StringVar(value="Welcome to Wordle AI Studio!")
        self.solver_var = tk.StringVar(value="BFS")
        self.cost_var = tk.StringVar(value="constant")
        self.heuristic_var = tk.StringVar(value="log2")
        self.animating = False
        self.pending_animation: list[Tuple[str, List[Mark]]] = []
        self.current_row = 0
        self.current_col = 0

        self._build_widgets()
        self._render_board()
        self._update_controls_visibility()

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
        controls_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

        # Row 0: Solver selection
        tk.Label(
            controls_frame,
            text="Solver:",
            font=("Helvetica", 12),
            bg="#f8f9fa",
        ).grid(row=0, column=0, padx=5, sticky="e")

        self.solver_menu = tk.OptionMenu(
            controls_frame,
            self.solver_var,
            *self.SOLVER_DISPLAY_NAMES.keys(),
            command=self._update_controls_visibility,
        )
        self.solver_menu.config(font=("Helvetica", 11), width=8)
        self.solver_menu.grid(row=0, column=1, padx=5, sticky="w")

        # Row 1: Cost function (for UCS and A*)
        self.cost_label = tk.Label(
            controls_frame,
            text="Cost Fn:",
            font=("Helvetica", 12),
            bg="#f8f9fa",
        )
        self.cost_label.grid(row=1, column=0, padx=5, sticky="e")

        self.cost_menu = tk.OptionMenu(
            controls_frame,
            self.cost_var,
            *COST_FUNCTIONS.keys(),
        )
        self.cost_menu.config(font=("Helvetica", 10), width=12)
        self.cost_menu.grid(row=1, column=1, padx=5, sticky="w")

        # Row 2: Heuristic function (for A* only)
        self.heuristic_label = tk.Label(
            controls_frame,
            text="Heuristic:",
            font=("Helvetica", 12),
            bg="#f8f9fa",
        )
        self.heuristic_label.grid(row=2, column=0, padx=5, sticky="e")

        self.heuristic_menu = tk.OptionMenu(
            controls_frame,
            self.heuristic_var,
            *HEURISTIC_FUNCTIONS.keys(),
        )
        self.heuristic_menu.config(font=("Helvetica", 10), width=12)
        self.heuristic_menu.grid(row=2, column=1, padx=5, sticky="w")

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
        run_solver_btn.grid(row=0, column=2, padx=5, rowspan=3)

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
        new_game_btn.grid(row=0, column=3, padx=5, rowspan=3)

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
        benchmark_btn.grid(row=0, column=4, padx=5, rowspan=3)

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

    def _update_controls_visibility(self, *args) -> None:
        """Show/hide cost and heuristic controls based on solver selection."""
        solver = self.solver_var.get()
        
        if solver == "UCS":
            # Show cost, hide heuristic
            self.cost_label.grid()
            self.cost_menu.grid()
            self.heuristic_label.grid_remove()
            self.heuristic_menu.grid_remove()
        elif solver == "A*":
            # Show both cost and heuristic
            self.cost_label.grid()
            self.cost_menu.grid()
            self.heuristic_label.grid()
            self.heuristic_menu.grid()
        else:
            # Hide both (BFS, DFS)
            self.cost_label.grid_remove()
            self.cost_menu.grid_remove()
            self.heuristic_label.grid_remove()
            self.heuristic_menu.grid_remove()

    def run_solver(self) -> None:
        """Run the selected solver with animation."""
        if self.animating:
            return
        
        # Get solver type
        solver_type = self.solver_var.get()
        solver_base = self.SOLVER_DISPLAY_NAMES.get(solver_type, "bfs-opt")
        
        # Build solver key based on type and selected functions
        if solver_base == "bfs-opt" or solver_base == "dfs-opt":
            solver_key = solver_base
        elif solver_base == "ucs":
            cost_fn = self.cost_var.get()
            solver_key = f"ucs-{cost_fn}"
        elif solver_base == "astar":
            cost_fn = self.cost_var.get()
            heuristic_fn = self.heuristic_var.get()
            solver_key = f"astar-{cost_fn}-{heuristic_fn}"
        else:
            solver_key = "bfs-opt"
        
        if solver_key not in OPTIMIZED_SOLVERS:
            messagebox.showerror("Error", f"Solver '{solver_key}' not found!")
            return
        
        solver = OPTIMIZED_SOLVERS[solver_key]
        simulation = WordleGame(answer=self.game.answer, word_list=WORD_LIST)
        result = solver.solve(simulation.answer, simulation.word_list)
        
        if not result.success:
            messagebox.showinfo("Solver", "Solver failed to find the answer within the attempt limit.")
            return
        
        # Display solver exploration info
        self.results_text.config(state="normal")
        self.results_text.delete("1.0", tk.END)
        
        # Build solver description
        solver_desc = solver_type
        if solver_type == "UCS":
            solver_desc += f" (cost={self.cost_var.get()})"
        elif solver_type == "A*":
            solver_desc += f" (cost={self.cost_var.get()}, h={self.heuristic_var.get()})"
        
        result_lines = [
            f"Solver: {solver_desc}\n",
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
        dialog.geometry("500x450")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (250)
        y = (dialog.winfo_screenheight() // 2) - (225)
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
        
        # Solver selection section
        tk.Label(dialog, text="Select Solvers:", font=("Helvetica", 11, "bold")).grid(
            row=2, column=0, columnspan=2, padx=20, pady=(15, 5), sticky="w"
        )
        
        # Checkboxes for basic solvers
        solver_vars = {}
        solver_frame = tk.Frame(dialog)
        solver_frame.grid(row=3, column=0, columnspan=2, padx=40, pady=5, sticky="w")
        
        # Basic solvers
        basic_solvers = [
            ('bfs-opt', 'BFS', True),
            ('dfs-opt', 'DFS', True),
        ]
        
        for i, (key, name, default) in enumerate(basic_solvers):
            var = tk.BooleanVar(value=default)
            solver_vars[key] = var
            cb = tk.Checkbutton(solver_frame, text=name, variable=var, font=("Helvetica", 10))
            cb.grid(row=i // 2, column=i % 2, sticky="w", padx=10, pady=2)
        
        # UCS with cost selection
        tk.Label(solver_frame, text="UCS:", font=("Helvetica", 10)).grid(
            row=1, column=0, sticky="w", padx=10, pady=2
        )
        ucs_var = tk.BooleanVar(value=True)
        ucs_cb = tk.Checkbutton(solver_frame, variable=ucs_var, font=("Helvetica", 10))
        ucs_cb.grid(row=1, column=0, sticky="w", padx=80, pady=2)
        
        ucs_cost_var = tk.StringVar(value="constant")
        ucs_cost_menu = tk.OptionMenu(solver_frame, ucs_cost_var, "constant", "reduction", "partition", "entropy")
        ucs_cost_menu.config(font=("Helvetica", 9), width=10)
        ucs_cost_menu.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        # A* with cost and heuristic selection
        tk.Label(solver_frame, text="A*:", font=("Helvetica", 10)).grid(
            row=2, column=0, sticky="w", padx=10, pady=2
        )
        astar_var = tk.BooleanVar(value=True)
        astar_cb = tk.Checkbutton(solver_frame, variable=astar_var, font=("Helvetica", 10))
        astar_cb.grid(row=2, column=0, sticky="w", padx=80, pady=2)
        
        astar_cost_var = tk.StringVar(value="constant")
        astar_cost_menu = tk.OptionMenu(solver_frame, astar_cost_var, "constant", "reduction", "partition", "entropy")
        astar_cost_menu.config(font=("Helvetica", 9), width=10)
        astar_cost_menu.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        
        tk.Label(solver_frame, text="h:", font=("Helvetica", 9)).grid(
            row=3, column=0, sticky="e", padx=85, pady=2
        )
        astar_h_var = tk.StringVar(value="log2")
        astar_h_menu = tk.OptionMenu(solver_frame, astar_h_var, "ratio", "remaining", "log2", "entropy", "partition")
        astar_h_menu.config(font=("Helvetica", 9), width=10)
        astar_h_menu.grid(row=3, column=1, sticky="w", padx=5, pady=2)
        
        # Status label
        status_var = tk.StringVar(value="")
        status_label = tk.Label(dialog, textvariable=status_var, font=("Helvetica", 10), fg="blue")
        status_label.grid(row=4, column=0, columnspan=2, pady=5)
        
        # Buttons
        button_frame = tk.Frame(dialog)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        def run_benchmark():
            try:
                samples = int(samples_var.get())
                seed = int(seed_var.get())
                
                if samples < 1 or samples > 50:
                    messagebox.showerror("Invalid Input", "Samples must be between 1 and 50")
                    return
                
                # Build solver list based on selections
                selected_solvers = []
                
                if solver_vars['bfs-opt'].get():
                    selected_solvers.append('bfs-opt')
                if solver_vars['dfs-opt'].get():
                    selected_solvers.append('dfs-opt')
                if ucs_var.get():
                    cost = ucs_cost_var.get()
                    selected_solvers.append(f'ucs-{cost}')
                if astar_var.get():
                    cost = astar_cost_var.get()
                    h = astar_h_var.get()
                    selected_solvers.append(f'astar-{cost}-{h}')
                
                if not selected_solvers:
                    messagebox.showerror("No Solvers", "Please select at least one solver")
                    return
                
                status_var.set("Running benchmark...")
                dialog.update()
                
                # Import here to avoid circular dependency
                from .benchmark import run_benchmarks
                
                # Run benchmark with selected solvers
                stats = run_benchmarks(samples=samples, seed=seed, solvers=selected_solvers)
                
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
                    # Format solver name with configuration details
                    if solver_name == 'bfs-opt':
                        display_name = 'BFS'
                    elif solver_name == 'dfs-opt':
                        display_name = 'DFS'
                    elif solver_name.startswith('ucs-'):
                        cost = solver_name.split('-')[1]
                        display_name = f'UCS (cost={cost})'
                    elif solver_name.startswith('astar-'):
                        parts = solver_name.split('-')
                        cost = parts[1]
                        h = parts[2] if len(parts) > 2 else 'unknown'
                        display_name = f'A* (cost={cost}, h={h})'
                    else:
                        display_name = solver_name
                    
                    row = [
                        display_name,
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
