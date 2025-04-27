# Copilot Instructions for Plex History Report

## Project Overview

- This project is hosted on GitHub at `claytono/plex-history-report`.
- Group multiple commands into logical sets and offer to run them in a single invocation or
  separately.
- We are using Python 3 for this project. Use the `python3` binary when invoking Python directly.
- We are using `uv` for Python package management. Follow best practices for `uv` in all aspects of
  this project.

## General Guidelines

- Always evaluate tools that are available via MCP servers and use them when appropriate.
- For complex tasks, consider use the sequential thinking MCP server.

## Coding Standards

- Ensure no trailing whitespace is added to lines and all edited files have a final newline.
- Prefer editing files directly using your tools, instead of using shell commands.
- Only add comments to the code if they are necessary for understanding the code.
- Never run shellcheck or other linting tools directly; always use the corresponding
  `./scripts/run-*` scripts (e.g., `./scripts/run-shellcheck`, `./scripts/run-black`, etc.).

## GitHub Workflow

- ALWAYS use GitHub MCP tools when available instead of shell commands or gh CLI.
- Use the GitHub MCP tool to track tasks via GitHub issues and pull requests.
  - Ask if new feature requests should be tracked in a GitHub issue.
  - When creating a new pull request, use a short descriptive name.
  - Add `cc: #<issue-number>` to the end of the body of the pull request.
  - When processing tasks from a GitHub issue, focus on a single task at a time unless told
    otherwise.
  - If an issue requires multiple steps, ask if I want to break it down into smaller tasks and ask
    for confirmation before proceeding. These sub-tasks should be represented as a checklist in the
    associated issue.
  - Only fall back to using the `gh` cli tool if the GitHub MCP tool is not available.

### Monitoring CI Status

- After pushing changes to a pull request, always run `./scripts/check-gh-actions` to monitor CI
  status and wait for workflows to complete.
- If any CI checks fail, examine the logs provided by the script to diagnose and fix the issues
  before proceeding.

## Git Workflow

- When running `git` commands use `git --no-pager` to avoid paging output.
- Group multiple commands into logical sets and offer to run them in a single invocation using `&&`
  or separately.
- Branch naming: Use descriptive names with issue numbers when applicable (e.g.,
  `fix-reporting-issue-42`).

### Creating New Branches

- Before creating a new branch for an issue:
  - Check for unstaged changes and fetch the latest changes in one step:
    `git --no-pager status && git fetch origin`
  - Handle any unstaged changes appropriately (stash, commit, or abort) before proceeding.
  - Update the default branch with `git checkout main && git pull`.
  - Create the new branch from the updated default branch: `git checkout -b branch-name`.

### Preparing for Pull Requests

- Before pushing changes for a pull request:
  - Run all tests using `./scripts/run-all-checks`.
  - Update the current branch with the latest changes from the default branch using a single
    command: `git pull --rebase origin main`
  - If conflicts occur during rebasing, help resolve them and then continue with
    `git rebase --continue`.
  - If the branch has already been pushed remotely, use `git push --force-with-lease --set-upstream`
    to update it safely after rebasing (this is safer than `--force` as it prevents overwriting
    others' changes).

## Testing and Committing

- Any time you need to run any tests, use `./scripts/run-all-checks`.
- When making a commit:
  - Write clear, descriptive commit messages that explain the "why" not just the "what"
  - Use the imperative mood in the subject line (e.g., "Fix bug" not "Fixed bug")
  - Inspect the README.md to determine if the commit message should be updated to reflect the
    changes made.
