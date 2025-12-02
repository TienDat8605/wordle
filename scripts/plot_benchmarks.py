"""Generate summary figures for Wordle solver benchmarks.

This script uses hard-coded aggregated results from the detailed benchmark
run (10-sample, seed=36) and outputs a 2x2 PNG with: avg_time, avg_peak_kib,
avg_nodes, avg_guesses.
"""
from __future__ import annotations
import matplotlib.pyplot as plt
import numpy as np
import os

# Data from detailed benchmark run (50-sample, seed=23125033)
solvers = ["BFS-OPT", "DFS-OPT", "UCS-REDUCTION", "ASTAR-REDUCTION-LOG2"]
avg_time_ms = [23059.92, 3547.47, 17672.54, 3278.62]
avg_peak_kib = [20791.27, 4296.15, 36835.19, 4279.57]
avg_nodes = [286.9, 6.4, 154.6, 4.1]
avg_guesses = [2.10, 5.06, 2.10, 2.12]

out_dir = os.path.join(os.path.dirname(__file__), "..", "reports", "images")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "bench_summary.png")

x = np.arange(len(solvers))
width = 0.6

fig, axs = plt.subplots(2, 2, figsize=(12, 8))

# Avg time (log scale to compress large skew)
ax = axs[0,0]
ax.bar(x, avg_time_ms, width, color=['#4C72B0', '#55A868', '#C44E52', '#8172B2'])
ax.set_xticks(x)
ax.set_xticklabels(solvers, rotation=25)
ax.set_ylabel('Avg time (ms)')
ax.set_title('Average Time (ms)')
ax.set_yscale('log')

# Avg peak memory
ax = axs[0,1]
ax.bar(x, avg_peak_kib, width, color=['#4C72B0', '#55A868', '#C44E52', '#8172B2'])
ax.set_xticks(x)
ax.set_xticklabels(solvers, rotation=25)
ax.set_ylabel('Avg peak (KiB)')
ax.set_title('Average Peak Memory (KiB)')
ax.set_yscale('log')

# Avg nodes expanded
ax = axs[1,0]
ax.bar(x, avg_nodes, width, color=['#4C72B0', '#55A868', '#C44E52', '#8172B2'])
ax.set_xticks(x)
ax.set_xticklabels(solvers, rotation=25)
ax.set_ylabel('Avg nodes expanded')
ax.set_title('Average Nodes Expanded')

# Avg guesses
ax = axs[1,1]
ax.bar(x, avg_guesses, width, color=['#4C72B0', '#55A868', '#C44E52', '#8172B2'])
ax.set_xticks(x)
ax.set_xticklabels(solvers, rotation=25)
ax.set_ylabel('Avg guesses')
ax.set_title('Average Number of Guesses')

plt.tight_layout()
plt.savefig(out_path, dpi=150)
print(f"Saved figure to {out_path}")
