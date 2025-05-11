# Plex History Reports

A Python tool to track, analyze, and report on your Plex media watching statistics. Get insights
into TV show and movie watching habits, track completion percentages, view watch history, and export
reports in multiple formats.

## Background

Originally this started as an effort to collect data from Plex so that I could use that to have
ChatGPT help me determine if I would like watching a TV show. I used GitHub Copilot for most of this
and the project kind of went overboard. Overall it works well for my needs and I'm happy with it. I
hope you find it useful too.

## Features

- **Comprehensive Statistics**: Calculate detailed watch statistics for both TV shows and movies
- **Completion Tracking**: See completion percentages for shows and view partially watched content
- **Multiple Output Formats**: Export as tables, JSON, Markdown, CSV, or YAML
- **Flexible Filtering**: Filter by user, watch status, or completion percentage
- **Custom Sorting**: Sort results by various metrics (title, watch count, etc.)
- **User Management**: Query available Plex users and filter statistics by specific users
- **Recently Watched**: View recently watched media with detailed information

## Quick Start with UVX

You can run the tool directly from GitHub without installing it using `uvx`:

```bash
# Run directly from GitHub with uvx (no installation needed)
uvx github:claytono/plex-history-report --help
```

This will automatically download the repository and install all required dependencies. You'll still
need to configure your Plex server details - see the Configuration section below.

## Installation

### Prerequisites

- Python 3.8 or higher
- [UV](https://github.com/astral-sh/uv) package management tool

### Setup

1. Clone this repository:

   ```bash
   git clone https://github.com/claytono/plex-history-report.git
   cd plex-history-report
   ```

2. Install the package with UV:

   ```bash
   # Install in development mode
   uv pip install -e .
   ```

3. Alternatively, run directly from the cloned repository:

   ```bash
   # Run with uvx without installing
   uvx plex_history_report --help

   # Or use the provided wrapper script
   ./bin/plex-history-report --help
   ```

## Configuration

Create a `config.yaml` file in the project directory with the following structure:

```yaml
plex:
  base_url: "http://your-plex-server:32400"
  token: "your-plex-token"
  default_user: "optional-default-username" # Optional: Set a default user
```

You can obtain your Plex token by following the instructions in the
[PlexAPI documentation](https://github.com/pkkid/python-plexapi#getting-a-plex-token).

## Usage

The tool can be run in several ways:

```bash
# Using the installed command if you installed with uv pip install
plex-history-report --tv

# Using the wrapper script from cloned repository
./bin/plex-history-report --tv

# Using uvx from local repository
uvx plex_history_report --tv

# Using uvx directly from GitHub
uvx github:claytono/plex-history-report --tv
```

### Output Formats

```bash
# Default is rich-formatted tables in the terminal
./bin/plex-history-report --tv

# Alternative formats
./bin/plex-history-report --tv --format json      # JSON format
./bin/plex-history-report --tv --format markdown  # Markdown format
./bin/plex-history-report --tv --format csv       # CSV format
./bin/plex-history-report --tv --format yaml      # YAML format
```

### Filtering Options

```bash
# Show recently watched content
./bin/plex-history-report --tv --show-recent

# Filter to only partially watched content
./bin/plex-history-report --tv --partially-watched-only

# Include unwatched content (off by default)
./bin/plex-history-report --tv --include-unwatched
```

### Sorting Options

```bash
# Sort TV shows
./bin/plex-history-report --tv --sort-by completion_percentage
./bin/plex-history-report --tv --sort-by watched_episodes
./bin/plex-history-report --tv --sort-by last_watched

# Sort movies
./bin/plex-history-report --movies --sort-by last_watched
./bin/plex-history-report --movies --sort-by watch_count
./bin/plex-history-report --movies --sort-by duration_minutes
```

### Full Command Reference

Run the help command for a complete list of options:

```bash
./bin/plex-history-report --help
```

### Available Sort Options

#### TV Shows

- `title`: Sort alphabetically by title
- `watched_episodes`: Sort by number of watched episodes (descending)
- `completion_percentage`: Sort by completion percentage (descending, default)
- `last_watched`: Sort by most recently watched
- `year`: Sort by release year (newest first)
- `rating`: Sort by rating (highest first)

#### Movies

- `title`: Sort alphabetically by title
- `year`: Sort by release year (newest first)
- `last_watched`: Sort by most recently watched (default)
- `watch_count`: Sort by number of times watched (descending)
- `rating`: Sort by rating (highest first)
- `duration_minutes`: Sort by movie duration (longest first)

## Development

### Running Tests and Checks

We use pre-commit hooks to ensure code quality. Always run all checks using the provided script:

```bash
./scripts/run-all-checks
```

This script runs all pre-commit hooks including:

- Black (code formatting)
- Ruff (linting)
- Prettier (markdown/yaml/json formatting)
- ShellCheck and shfmt (shell script checks)
- Xenon (code complexity)
- PyMarkdown (markdown linting)
- Tests with coverage

For individual checks, use pre-commit directly:

```bash
uv run pre-commit run [hook-id] --all-files
```

### Code Quality

Run the linter to ensure code quality:

```bash
./scripts/run-lint
```

You can also run all checks at once using:

```bash
./scripts/run-all-checks
```

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file
for details.

This program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.
