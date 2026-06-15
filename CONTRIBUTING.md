# Contributing to MediumDarwin

Thanks for your interest in contributing! Please follow the guidelines below to help us maintain quality and consistency.

## Development Environment
- Use Python 3.8+.
- Create a virtual environment and install dependencies:
  ```bash
  python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
  pip install -r requirements.txt
  ```

## Code Style
- Prefer readable, self-documenting code.
- Use descriptive variable and function names.
- Keep functions small and cohesive; avoid deep nesting.
- Add type hints for public APIs and function signatures where helpful.

## Docstrings and Documentation
- Use Google-style docstrings; docs are built with Sphinx + napoleon.
- Document modules, classes, functions, arguments, return values, and side effects.
- To build docs locally:
  ```bash
  pip install sphinx sphinxcontrib-napoleon
  sphinx-build -b html docs _build/html
  ```

## Testing
- Run tests before submitting:
  ```bash
  python -m pytest -q
  ```
- Prefer adding tests when fixing bugs or adding features.

## Commit Messages
- Use clear, imperative commit messages (e.g., "Add X", "Fix Y").
- Reference issues where applicable.

## Pull Requests
- Keep PRs focused and small.
- Describe motivation, approach, and any trade-offs.
- Ensure CI passes (if configured) and documentation is updated.
