#!/bin/bash

# Directory to store test outputs
OUTPUT_DIR="test_output"

# Ensure the output directory exists
mkdir -p "$OUTPUT_DIR"

# Function to run a command and save its output
run_test() {
    local description="$1"
    local command="$2"
    local output_file="$3"

    echo "Running test: $description"
    echo "$command" >"$OUTPUT_DIR/$output_file"
    eval "$command" >>"$OUTPUT_DIR/$output_file" 2>&1
}

# Basic functionality tests
run_test "TV statistics in table format" "./bin/plex-history-report --tv" "output_tv_table.txt"
run_test "Movie statistics in table format" "./bin/plex-history-report --movies" "output_movies_table.txt"

# Output format tests
run_test "TV statistics in JSON format" "./bin/plex-history-report --tv --format json" "output_tv_json.txt"
run_test "TV statistics in Markdown format" "./bin/plex-history-report --tv --format markdown" "output_tv_markdown.txt"
run_test "TV statistics in CSV format" "./bin/plex-history-report --tv --format csv" "output_tv_csv.txt"
run_test "TV statistics in YAML format" "./bin/plex-history-report --tv --format yaml" "output_tv_yaml.txt"
run_test "TV statistics in Compact format" "./bin/plex-history-report --tv --format compact" "output_tv_compact.txt"

# Filtering tests
run_test "Partially watched TV shows" "./bin/plex-history-report --tv --partially-watched-only" "output_tv_partially_watched.txt"
run_test "Include unwatched TV shows" "./bin/plex-history-report --tv --include-unwatched" "output_tv_include_unwatched.txt"

# Feature tests
run_test "TV statistics with show recent items" "./bin/plex-history-report --tv --show-recent" "output_tv_show_recent.txt"
run_test "Movie statistics with show recent items" "./bin/plex-history-report --movies --show-recent" "output_movies_show_recent.txt"

# Debug logging test
run_test "TV statistics with debug logging" "./bin/plex-history-report --tv --debug" "output_tv_debug.txt"

# Performance benchmarking test
run_test "TV statistics with benchmarking" "./bin/plex-history-report --tv --benchmark" "output_tv_benchmark.txt"

# Sorting tests
run_test "TV statistics sorted by completion percentage" "./bin/plex-history-report --tv --sort-by completion_percentage" "output_tv_sorted_completion.txt"
run_test "Movie statistics sorted by last watched" "./bin/plex-history-report --movies --sort-by last_watched" "output_movies_sorted_last_watched.txt"

# Cleanup option
if [[ "$1" == "clean" ]]; then
    echo "Cleaning up test outputs..."
    rm -rf "$OUTPUT_DIR"
    echo "Test outputs cleaned."
fi

# Completion message
echo "All tests completed. Outputs saved in $OUTPUT_DIR."
