# Contributing

Thanks for helping improve Poyto.

## Setup

```bash
git clone https://github.com/nezumi0627/Poyto.git
cd Poyto
python -m venv .venv
pip install -e '.[dev]'
```

Run checks before opening a pull request:

```bash
pytest
ruff check .
mypy src/poyto
```

## Endpoint changes

For a new or changed POYP endpoint:

1. Base the implementation on traffic you are authorized to inspect.
2. Do not commit HAR files or credentials.
3. Update `docs/endpoints.md`.
4. Add a mock test that verifies method, URL, headers, and body where relevant.
5. Avoid guessing unobserved request fields.

## Style

Keep the public API small and explicit. Prefer dedicated methods for confirmed endpoints and the generic `request()` helper for experimental work.
