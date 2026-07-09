# Config Migration Specification

## Purpose

Module-level constants scattered across `extractor.py`, `enricher.py`, `analyzer.py`, `lead_scorer.py`, and `pipeline.py` MUST be externalized to `config.yaml` so tuning does not require editing source code.

## Requirements

### Requirement: Config sections added

The system MUST recognize four new top-level sections in `config.yaml`:

- `extraction` — contains `max_pages`, `page_token_delay`, `request_timeout`
- `enrichment` — contains `hunter_timeout`, `website_scan_timeout`
- `scoring.thresholds` — contains `slow_ms`, `warn_ms`
- `scoring.goal_bonuses` — contains bonus values per goal (`web`, `seo`, `ads`, `general`) and rating thresholds
- `scoring.dup_threshold` — integer threshold for fuzzy deduplication

#### Scenario: All keys present

- GIVEN a `config.yaml` with all new sections fully populated
- WHEN each module loads its values
- THEN every constant reads from the config key instead of the module-level default

#### Scenario: Single key missing

- GIVEN a `config.yaml` missing one key from `extraction.max_pages`
- WHEN `PlacesExtractor` initializes
- THEN `MAX_PAGES` falls back to the module constant `3`
- AND a warning is logged

#### Scenario: Entire config section missing

- GIVEN a `config.yaml` with no `extraction` section at all
- WHEN `PlacesExtractor` is instantiated and runs
- THEN all extraction-related values use their module-level defaults
- AND a warning is logged per missing key

### Requirement: Fallback to module constants

Each module MUST keep its current constant as a default. A helper `_get_optional(key, default)` pattern MUST be used so that reading from config never crashes on missing keys.

#### Scenario: No config file change

- GIVEN an existing `config.yaml` with no new sections
- WHEN the pipeline runs
- THEN behavior is identical to before — all constants use module defaults

### Requirement: Config key validation

`config_loader.load_config()` SHOULD warn on unknown top-level keys to catch typos. It MUST NOT crash on any missing key.

#### Scenario: Unknown key in config

- GIVEN a `config.yaml` with a typo like `extractoin.max_pages`
- WHEN `load_config()` parses the file
- THEN a log warning is emitted but no crash occurs
- AND the unknown key is ignored (the module constant fallback is used)

### Requirement: Config mapping

| Module | Constant | Config path | Default |
|--------|----------|-------------|---------|
| `extractor.py` | `MAX_PAGES` | `extraction.max_pages` | `3` |
| `extractor.py` | `PAGE_TOKEN_DELAY` | `extraction.page_token_delay` | `2` |
| `extractor.py` | `REQUEST_TIMEOUT` | `extraction.request_timeout` | `15` |
| `enricher.py` | `HUNTER_TIMEOUT` | `enrichment.hunter_timeout` | `10` |
| `enricher.py` | `WEBSITE_SCAN_TIMEOUT` | `enrichment.website_scan_timeout` | `10` |
| `analyzer.py` | `SLOW_THRESHOLD_MS` | `scoring.thresholds.slow_ms` | `3000` |
| `analyzer.py` | `WARN_THRESHOLD_MS` | `scoring.thresholds.warn_ms` | `1500` |
| `lead_scorer.py` | `WEB_NO_SITE_BONUS` | `scoring.goal_bonuses.web.no_site_bonus` | `40` |
| `lead_scorer.py` | `WEB_HAS_SITE_PENALTY` | `scoring.goal_bonuses.web.has_site_penalty` | `-10` |
| `lead_scorer.py` | `SEO_NO_SOCIAL_BONUS` | `scoring.goal_bonuses.seo.no_social_bonus` | `20` |
| `lead_scorer.py` | `SEO_POOR_TECH_BONUS` | `scoring.goal_bonuses.seo.poor_tech_bonus` | `30` |
| `lead_scorer.py` | `SEO_NO_SITE_PENALTY` | `scoring.goal_bonuses.seo.no_site_penalty` | `-20` |
| `lead_scorer.py` | `ADS_HAS_SITE_BONUS` | `scoring.goal_bonuses.ads.has_site_bonus` | `20` |
| `lead_scorer.py` | `ADS_LOW_RATING_BONUS` | `scoring.goal_bonuses.ads.low_rating_bonus` | `15` |
| `lead_scorer.py` | `ADS_LOW_RATING_THRESHOLD` | `scoring.goal_bonuses.ads.low_rating_threshold` | `4.2` |
| `lead_scorer.py` | `GENERAL_HIGH_RATING_THRESHOLD` | `scoring.goal_bonuses.general.high_rating_threshold` | `4.5` |
| `pipeline.py` | `DUP_THRESHOLD` | `scoring.dup_threshold` | `85` |

#### Scenario: All defaults match

- GIVEN the module constants as defined in source
- WHEN config is loaded with no overrides
- THEN the effective value for every path equals the table default above
