"""CLI entrypoint for running benchmarks."""

from wordle.benchmark import print_benchmarks


if __name__ == "__main__":
    print_benchmarks(samples=10, seed=36)
    
