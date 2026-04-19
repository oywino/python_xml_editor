# Contributing

## Workflow

1. Branch from `main`.
2. Keep changes focused and easy to review.
3. Test locally before opening a pull request.
4. Describe user-facing behavior changes clearly in the PR.

Suggested branch prefixes:

- `feature/` for new functionality
- `fix/` for bug fixes
- `chore/` for maintenance and repo setup

## Pull Request Checklist

- explain what changed
- explain why it changed
- note how it was tested
- include screenshots for UI changes when useful
- mention any parsing or export behavior changes explicitly

## Local Run

```bash
python app.py
```

If needed on Windows:

```bash
py app.py
```

## Project Expectations

- prefer simple, readable changes over heavy abstractions
- keep the static app easy to run without extra dependencies
- document changes that affect file formats, parsing, or export behavior

## Issues

Use the GitHub issue templates for:

- bug reports
- feature requests

For larger changes, open an issue first so the implementation plan is easy to discuss.
