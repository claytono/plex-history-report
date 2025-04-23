# Copilot Instructions for Plex Stats

- When running `git` commands use `git --no-pager` to avoid paging output.
- Group multiple commands into logical sets and offer to run them in a single invocation or separately.
- Ensure no trailing whitespace is added to lines and all edited files have a final newline.
- Consult TODO.md to track progress and update it when completing tasks.
- Ask if new feature requests should be tracked in the TODO file.
- When processing tasks from the TODO file, focus on a single task at a time unless told otherwise.
- If a task requires multiple steps, ask if I want to break it down into smaller tasks and ask for confirmation before proceeding.
- Prefer editing files directly using your tools, instead of using shell commands
- We are using `uv` and use best practices for `uv` in all aspects of this project
- We are using Python 3 for this project.  Use the `python3` binary when invoking Python directly.
- Only add comments to the code if they are necessary for understanding the code.
- When making a commit, inspect the README.md to determine if the commit message should be updated to reflect the changes made.
- Before making a commit, offer to run the linter and tests to ensure everything is working correctly.
- Assume the `gh` command is available for GitHub CLI operations.
