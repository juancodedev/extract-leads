# Async aiohttp Migration Specification

## Purpose

Replace synchronous `requests` with `aiohttp` across the pipeline to enable concurrent HTTP and increase throughput for 500+ lead runs.

## Requirements

### Requirement: ClientSession lifecycle

One `aiohttp.ClientSession` per `run_pipeline()` invocation, injected into `PlacesExtractor`, `Enricher`, and `WebsiteAnalyzer` constructors. Session MUST be closed via `async with` or explicit `await session.close()`.

#### Scenario: Single session per run

- GIVEN a pipeline run
- WHEN `run_pipeline()` executes
- THEN exactly one `ClientSession` is created and injected into all three consumer classes

#### Scenario: Session closed

- GIVEN a pipeline run that completes or errors
- WHEN the run ends
- THEN the session is closed

### Requirement: Per-service semaphores

Concurrency limits MUST be enforced: Places API 5, Hunter.io 3, website scans 10.

#### Scenario: Places respects limit

- GIVEN 5+ concurrent Places API calls
- WHEN all arrive at the semaphore
- THEN at most 5 execute concurrently

#### Scenario: Scans respect limit

- GIVEN 10+ concurrent website fetches
- WHEN all arrive at the semaphore
- THEN at most 10 execute concurrently

### Requirement: Async method signatures

| Module | Method | Change |
|--------|--------|--------|
| `extractor.py` | `_request()`, `_get_place_details()`, `search_businesses()` | `async` |
| `enricher.py` | `find_email()`, `scan_website()` | `async` |
| `analyzer.py` | `analyze()` | `async` |
| `pipeline.py` | `run_pipeline()` | `async` |
| `cli.py` | `main()` | `async` + `asyncio.run()` |

`LeadScorer` MUST remain synchronous — pure computation, no HTTP.

#### Scenario: Returns match sync shapes

- GIVEN any async method above
- WHEN awaited
- THEN return type/value matches the sync original exactly

### Requirement: Parallel enrichment

`find_email()` and `scan_website()` per lead MUST run via `asyncio.gather(return_exceptions=True)`. Failure in one MUST NOT block the other.

#### Scenario: Enrichment runs concurrently

- GIVEN a lead with domain and website
- WHEN enriching
- THEN `find_email` and `scan_website` are scheduled via `gather`

#### Scenario: Hunter timeout is isolated

- GIVEN Hunter.io times out for one lead
- WHEN `gather` returns
- THEN `find_email` returns `None`
- AND all other leads enrich normally

### Requirement: Parallel place details

`_get_place_details()` for all results in a text search page MUST use `asyncio.gather(return_exceptions=True)`.

#### Scenario: Details fetched concurrently

- GIVEN a text search response with 20 places
- WHEN `search_businesses()` processes them
- THEN all 20 detail calls are scheduled via `gather`

### Requirement: Parallel website analysis

Top 10 audit in `run_pipeline()` MUST run `analyze()` calls via `asyncio.gather(return_exceptions=True)`.

#### Scenario: Top 10 audits concurrent

- GIVEN 10 leads for SEO audit
- WHEN the deep audit phase runs
- THEN all 10 `analyze()` calls are scheduled concurrently

#### Scenario: Single audit failure

- GIVEN one website that times out
- WHEN `gather` returns
- THEN that lead's `audit_data` is an error dict
- AND the other 9 have complete audits
- AND the pipeline continues

### Requirement: Error shape preservation

Failed async calls MUST return the same shape as sync: `None` for `find_email`, `{}` for `_get_place_details`/`scan_website`, error dict for `analyze`.

#### Scenario: Timeout returns expected shape

- GIVEN any async HTTP call that times out
- WHEN the exception is caught
- THEN the return value matches the original sync error return

### Requirement: CLI unchanged

All CLI flags (`--config`, `--limit`, `--goal`, `--seo`, `--ads`, `--ig-web`, `--interactive`, `--html`, `--from-csv`, `--audit`) MUST produce identical output.

#### Scenario: All flags work

- GIVEN any CLI invocation that worked before
- WHEN run after migration
- THEN CSV rows, HTML report, and log messages are identical

### Requirement: Dependency

`requirements.txt` MUST add `aiohttp`.
