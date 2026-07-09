# Design: Async and Config Migration

## Technical Approach

Two deliverables executed sequentially: (D1) externalize ~15 constants into `config.yaml` with recursive fallback to module defaults, then (D2) flip HTTP from `requests` to `aiohttp` with shared `ClientSession`, per-service semaphores, and `asyncio.gather` for concurrent enrichment/audits. D1 first because D2 reads timeouts from config.

## Architecture Decisions

### Deep-merge config over module defaults

Module constants-only requires source edits to tune (rejected). Config-only breaks existing configs (rejected). **Chosen**: `_merge_with_defaults(cfg)` recursively fills missing keys from a `DEFAULTS` dict — existing configs without new sections keep working. Unknown keys log a warning (typo catch) but don't crash.

### Shared ClientSession injected via constructor

Global session per module can't share connection pool/DNS cache (rejected). **Chosen**: pass session explicitly — one pool per `run_pipeline()`, cleanup via `async with`.

### Service-semaphore per module (self-managed)

Central semaphore couples modules to pipeline internals (rejected). **Chosen**: each module reads its concurrency from config and creates `asyncio.Semaphore` internally.

### LeadScorer stays synchronous

Pure dict computation, no HTTP. Converting adds `async def` noise with zero throughput gain.

## Data Flow

```
config.yaml → load_config() → [deep-merge defaults]
     → run_pipeline() async
       → async with ClientSession as session:
           extractor(session,config).search_businesses()
             gather: _get_place_details (sem=5)
           enricher(session,config).find_email (sem=3)
           enricher.scan_website (sem=10)
         gather: analyzer(session,config).analyze (sem=10)
       → scorer.score(lead)          ← sync
       → deduplicate_leads(dup_threshold) → export
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `config.yaml` | Modify | New `extraction`, `enrichment`, `scoring.thresholds`, `scoring.goal_bonuses` |
| `config_loader.py` | Modify | Add `_merge_with_defaults()` deep-merge + unknown-key warning |
| `extractor.py` | Modify | Constants→config; `_request()` → async `aiohttp`; add `session`+`_sem` |
| `enricher.py` | Modify | Constants→config; `find_email`/`scan_website` → async |
| `analyzer.py` | Modify | Thresholds→config; `analyze()` → async; swap `requests.Session`→`aiohttp` |
| `lead_scorer.py` | Modify | Goal bonuses read from `scoring.goal_bonuses` (stays sync) |
| `pipeline.py` | Modify | `run_pipeline()`→async; create `ClientSession`; `gather` parallel work |
| `cli.py` | Modify | `main()`→`async def`; `asyncio.run()` entry point |
| `requirements.txt` | Modify | Add `aiohttp>=3.9.0` |

## Interfaces / Contracts

### D1 — Config loading

```python
def _merge_with_defaults(cfg: dict) -> dict:
    """Recursive deep-merge: cfg values override DEFAULTS. Warns on unknown keys."""
def load_config(path: str) -> dict:
    """Load YAML + merge. Exits on missing file."""
```

### D2 — Module constructors and async signatures

```python
class PlacesExtractor:
    def __init__(self, api_key: str, session: aiohttp.ClientSession, config: dict | None = None):
        self._sem = asyncio.Semaphore((config or {}).get("extraction", {}).get("concurrency", 5))
    async def search_businesses(self, keyword: str, location: str) -> list[dict]: ...
    async def _get_place_details(self, place_id: str) -> dict: ...

class Enricher:
    def __init__(self, hunter_api_key: str | None, session: aiohttp.ClientSession, config: dict | None = None): ...
    async def find_email(self, domain: str) -> str | None: ...
    async def scan_website(self, website: str, business_name: str = "") -> dict: ...
    @staticmethod
    def extract_domain(website: str) -> str | None: ...

class WebsiteAnalyzer:
    def __init__(self, session: aiohttp.ClientSession, config: dict | None = None):
        self._sem = asyncio.Semaphore((config or {}).get("scoring", {}).get("analysis_concurrency", 10))
    async def analyze(self, url: str) -> dict: ...

class LeadScorer:
    def __init__(self, config: dict, goal: str = "general"): ...   # unchanged
    def score(self, lead: dict) -> dict: ...                         # unchanged

async def run_pipeline(config, api_key, hunter_key="", limit=0, goal="general", do_seo=False, do_ads=False, do_ig_web=False) -> list[dict]: ...

async def main(): ...
def _sync_main(): return asyncio.run(main())
```

### Return shapes (identical to sync)

Error cases: `None` for `find_email`, `{}` for `_get_place_details`/`scan_website`, error-dict for `analyze`.

## Testing Strategy

Manual verification (no test runner installed):

| Scenario | Check |
|----------|-------|
| `python pipeline.py --limit 5` | Identical CSV to sync version |
| `python pipeline.py --from-csv --html` | Identical HTML report |
| Config with new sections removed | Falls back to defaults, no crash |
| Unknown config key | Warning logged, no crash |

## Migration / Rollout

Per-deliverable `git revert`. D1 commit: config + config_loader + per-module config reads. D2 commit: aiohttp dep + async conversions + pipeline/cli plumbing. Test after each with `--limit 5`. D2 is the risky revert boundary (all public method signatures change from sync to async).

## Open Questions

None.
