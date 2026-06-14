# Contributing

Thanks for your interest in contributing to extract-leads. This guide covers setup, workflow, and conventions.

See [README.md](README.md) for the project overview, features, usage, and full configuration reference.

## Setup

```bash
git clone https://github.com/juancodedev/extract-leads.git
cd extract-leads
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

This installs the project in editable mode plus dev dependencies: pytest, ruff, and mypy.

### API Keys

Copy the example env file and add your keys:

```bash
cp .env.local.example .env.local
```

Fill in `GOOGLE_PLACES_API_KEY` (required) and `HUNTER_API_KEY` (optional). **Never commit `.env.local`.**

## Development Workflow

1. **Create a branch** from `master`:
   ```bash
   git checkout -b feat/my-feature
   ```

2. **Make your changes**, following the code style below.

3. **Run tests**:
   ```bash
   pytest tests/ -v
   ```

4. **Run lint**:
   ```bash
   ruff check .
   ruff format --check .
   ```

5. **Run type check**:
   ```bash
   mypy .
   ```

6. **Commit** using [Conventional Commits](#commit-conventions) format.

7. **Push** and open a Pull Request against `master`.

## Testing

Tests live in `tests/` and use pytest.

| File | What it covers |
|------|---------------|
| `tests/test_lead_scorer.py` | Goal-based scoring (web, SEO, ads, general), tier boundaries, industry classification, city extraction, outreach flags |
| `tests/test_dedup.py` | Fuzzy deduplication with `rapidfuzz` — exact matches, fuzzy matches, case insensitivity, custom thresholds |
| `tests/test_integration.py` | Async pipeline end-to-end — mock Places API responses, scoring, dedup, limit enforcement, SEO audit, error handling |
| `tests/conftest.py` | Shared fixtures (`base_config`) and the `make_lead()` helper used across all tests |

Run all tests:

```bash
pytest tests/ -v
```

Run a specific file:

```bash
pytest tests/test_lead_scorer.py -v
```

Tests should be added alongside new features. Use the `make_lead()` helper from `conftest.py` when constructing lead dicts — it provides sensible defaults so tests only declare what matters.

## Commit Conventions

We use [Conventional Commits](https://www.conventionalcommits.org/). The type prefix maps to the change category:

| Prefix | Use when |
|--------|---------|
| `feat:` | New feature or capability |
| `fix:` | Bug fix |
| `refactor:` | Code restructuring without behavior change |
| `perf:` | Performance improvement |
| `docs:` | Documentation only |
| `test:` | Adding or updating tests |
| `chore:` | Maintenance, tooling, CI, dependencies |

Examples:

```
feat: add ads goal scoring with low-rating bonus
fix: strip postal codes from address before city extraction
docs: add outreach templates to docs/
```

## Code Style

- **Python 3.10+** (per `requires-python` in `pyproject.toml`)
- **Type hints** on all function signatures — mypy must pass
- **Line length:** 100 characters (`E501` is ignored)
- **Ruff rules:** `E`, `F`, `I`, `N`, `W`, `UP`, `B`, `C4`, `SIM`
- Use `dict[str, int]` instead of `typing.Dict[str, int]`
- Use `str | None` instead of `Optional[str]`
- Use `list[X]` instead of `typing.List[X]`
- Imports sorted with `isort` (ruff handles this — known first-party modules are configured)

Auto-format before committing:

```bash
ruff check . --fix
ruff format .
```

## Project Structure

```
extract-leads/
├── cli.py             # CLI entry point and interactive mode
├── pipeline.py        # Main async orchestrator (search → enrich → score → export)
├── extractor.py       # Google Places API with async retry
├── enricher.py        # Social, WhatsApp, booking, and email (Hunter.io) enrichment
├── lead_scorer.py     # Opportunity scoring engine per sales goal
├── analyzer.py        # Website analyzer (SEO, images, contact, booking, performance)
├── reporters.py       # HTML report generation with Jinja2
├── config_loader.py   # YAML config loading with defaults and fallbacks
├── exporters.py       # CSV export/import
├── booking_data.py    # 21 booking platform definitions
├── config.yaml        # User configuration (industries, locations, scoring weights)
├── pyproject.toml     # Package metadata, dependencies, ruff/mypy config
├── requirements.txt   # Runtime dependencies
├── templates/         # Jinja2 HTML templates (lead_report.html, audit_report.html)
├── tests/             # Test suite (pytest)
├── agents/            # Specialized audit kits (SEO, Meta Ads, Business, IG-to-Web)
├── docs/              # Outreach guides, filter references, sales tactics
├── openspec/          # SDD change tracking
└── .github/workflows/ # CI pipeline
```

## CI

GitHub Actions runs on every push and pull request to `master`:

| Job | Steps |
|-----|-------|
| `lint-and-type` | `ruff check` + `ruff format --check` + `mypy` |
| `tests` | `pytest tests/ -v` |

All checks must pass before a PR can be merged. Run them locally first (see [Development Workflow](#development-workflow)).

## Questions?

Open an issue or reach out in the repository. If you're unsure where to start, check the issue tracker for `good first issue` labels.
