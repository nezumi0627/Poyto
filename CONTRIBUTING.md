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
python scripts/code_stats.py
```

## Endpoint changes

For a new or changed POYP endpoint:

1. Base the implementation on request/response evidence you are authorized to inspect.
2. Do not commit private traffic exports or credentials.
3. Update `docs/endpoints.md`, `docs/capabilities.md`, and `docs/known-gaps.md` where relevant.
4. Add a mock test that verifies method, URL, query, headers, and body where relevant.
5. Avoid guessing unsupported request fields or response schemas.

## Style

Keep the public API small and explicit. Prefer dedicated methods for established endpoints and the generic `request()` helper for experimental work.
