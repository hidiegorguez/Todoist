# AGENTS.md

## Scope

These rules guide contributors and agents working in this repository.

## Local environment

- Use Python 3.11 and a `.venv` virtual environment.
- Install dependencies with `python -m pip install -r requirements.txt`.
- Keep credentials in `.env`, using `.env.example` as the template.
- Do not add tokens, passwords, API keys, or personal data to code, notebooks,
  logs, or commits.

## Code changes

- Keep the versions pinned in `requirements.txt` unless the change explicitly
  requires updating a dependency.
- Review IDs, filters, and operations before running code that modifies real
  Todoist tasks.
- Keep notebooks free of outputs before uploading them.
- Run `python -m py_compile main.py functions.py` after changing Python
  scripts.

## Git

- Create new branches from `dev` for implementation changes.
- Name branches with a conventional prefix followed by a short kebab-case
  description, e.g. `feature/`, `fix/`, `chore/`, `refactor/`, `docs/`,
  `test/` (`feature/add-weather-labels`, `fix/inbox-cleanup-bug`).
- Review `git diff` before committing.
- Do not commit `.env`, `.venv`, or files containing secrets.