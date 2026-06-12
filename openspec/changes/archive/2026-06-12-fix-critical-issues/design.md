# Design: fix-critical-issues

## Technical Approach

Pure structural refactoring — four independent tasks: delete orphaned `files/lead_scorer.py`, deduplicate booking domain data into a shared `booking_data.py` module (with the `bookingsystem` false-positive fix), move hardcoded industry/city defaults into `config_loader.py`, and extract four public functions from `pipeline.py` into focused modules (`cli.py`, `exporters.py`, `reporters.py`, `config_loader.py`) with backward-compatible re-exports at the bottom of `pipeline.py`.

## Architecture Decisions

### Decision: Re-exports in pipeline.py (no `__init__.py`)

| Option | Tradeoff | Decision |
|--------|----------|----------|
| `__init__.py` package | Breaks `python pipeline.py` invocation; requires restructure | ❌ |
| Re-exports in pipeline.py | File stays runnable; every `from pipeline import X` preserved; zero external consumers confirmed | ✅ |

### Decision: booking_data exports `BOOKING_DOMAINS` (dict) and `BOOKING_SKIP` (set)

Same casing as analyzer.py's existing names — zero consumer changes after swapping the import. Exclude `bookingsystem` from the union (generic term → substring false positives in enricher's regex). Include `appointmentplus.com` from enricher (the only unique entry not in analyzer).

### Decision: Interactive mode writes config.yaml on completion

After `run_interactive()` finishes extraction, dump the chosen config to `config.yaml` via `yaml.dump()`. First-run flow: user completes interactive prompts → config.yaml is written → subsequent `--config config.yaml` runs work without re-answering. `run_interactive()` never reads config.yaml (uses `get_default_industries()` / `get_default_locations()` directly), avoiding circular dependency.

### Decision: `get_default_industries()` returns dict with string keys "1".."12"

Interactive mode iterates `sorted(items(), key=lambda x: int(x[0]))` and checks `if s in AVAILABLE_INDUSTRIES`. Dict-key structure is required by the menu logic. `get_default_locations()` returns a list (matches `ALL_CITIES` structure).

## Data Flow

```
python pipeline.py
  │
  ├── pipeline.py: re-exports from cli import main
  │
  └── cli.main()
       ├── --interactive → run_interactive()
       │    ├── get_default_industries()  ← config_loader
       │    ├── get_default_locations()   ← config_loader
       │    ├── run_pipeline()            ← pipeline
       │    ├── export_csv()              ← exporters
       │    ├── print_summary()           ← reporters
       │    ├── export_html()             ← reporters
       │    └── yaml.dump(config.yaml)
       │
       └── --config path → load_config() ← config_loader
            └── run_pipeline() ← pipeline
                 ├── export_csv()    ← exporters
                 └── print_summary() ← reporters
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `files/lead_scorer.py` | Delete | 324-line orphan, zero references. `git rm` |
| `booking_data.py` | Create | `BOOKING_DOMAINS` (21 entries), `BOOKING_SKIP` (17 terms) |
| `config_loader.py` | Create | `load_config()` + `get_default_industries()` + `get_default_locations()` |
| `cli.py` | Create | `main()` + `run_interactive()` — entry point module |
| `exporters.py` | Create | `export_csv()` + `load_leads_from_csv()` |
| `reporters.py` | Create | `print_summary()` + `export_html()` |
| `enricher.py` | Modify | Remove inline `booking_domains` list & `booking_skip` set; import from `booking_data` |
| `analyzer.py` | Modify | Remove inline `BOOKING_DOMAINS` dict & `BOOKING_SKIP` set; import from `booking_data` |
| `pipeline.py` | Modify | Strip to ~170 lines: keep only `run_pipeline()` + re-exports |

## Interfaces / Contracts

### booking_data.py
```python
BOOKING_DOMAINS: Dict[str, str] = {
    "agendapro.com": "AgendaPro",
    "setmore.com": "Setmore",
    "tuu.cl": "TUU",
    "calendly.com": "Calendly",
    "acuityscheduling.com": "Acuity",
    "reservo.cl": "Reservo",
    "reservas.cl": "Reservas",
    "simplybook.me": "SimplyBook",
    "bookeo.com": "Bookeo",
    "youcanbook.me": "YouCanBook",
    "situdy.com": "Situdy",
    "turnero.cl": "Turnero",
    "timify.com": "Timify",
    "squareup.com/appointments": "Square Appointments",
    "wix.com/book": "Wix Bookings",
    "mibarbed.com": "MiBarbEd",
    "reservaenlinea.cl": "ReservaEnLinea",
    "agendaonline.cl": "AgendaOnline",
    "superbook": "SuperBook",
    "zenbooking": "ZenBooking",
    "appointmentplus.com": "AppointmentPlus",
}
# Union of analyzer (20) + enricher.appointmentplus.com (1).
# Excluded: "bookingsystem" — partial-substring false-positive in enricher's regex.
# Analyzer's human-readable labels take precedence for shared entries.

BOOKING_SKIP: Set[str] = {
    "terminos", "terms", "condiciones", "conditions",
    "privacy", "privacidad", "legal", "aviso-legal",
    "cookies", "blog", "faq", "ayuda", "help",
    "login", "registro", "register", "signin",
}
# Union of both skip sets (analyzer has all 17; enricher was missing 4).
```

### config_loader.py
```python
def load_config(path: str) -> Dict
    # From pipeline.py — unchanged

def get_default_industries() -> Dict[str, Dict]
    # 12 entries, matches current AVAILABLE_INDUSTRIES (name, keywords, bonus_score)
    # Dict with string keys "1".."12" for interactive menu ordering

def get_default_locations() -> List[Dict]
    # 25 entries, matches current ALL_CITIES (city, region, premium)
```

### pipeline.py — re-export shim (appended at file bottom)
```python
# ── Backward-compatible re-exports ──
from config_loader import load_config, get_default_industries, get_default_locations
from exporters import export_csv, load_leads_from_csv
from reporters import print_summary, export_html
from cli import main, run_interactive

if __name__ == "__main__":
    main()
```

### Internal import chain
```
cli.py  →  config_loader     (load_config, get_default_industries, get_default_locations)
cli.py  →  pipeline          (run_pipeline)
cli.py  →  exporters         (export_csv, load_leads_from_csv)
cli.py  →  reporters         (print_summary, export_html)
cli.py  →  analyzer          (generate_audit_report)  # for --audit mode only

pipeline.py  →  extractor    (PlacesExtractor)
pipeline.py  →  enricher     (Enricher)
pipeline.py  →  lead_scorer  (LeadScorer)
pipeline.py  →  analyzer     (WebsiteAnalyzer)

enricher.py  →  booking_data (BOOKING_DOMAINS, BOOKING_SKIP)
analyzer.py  →  booking_data (BOOKING_DOMAINS, BOOKING_SKIP)
```

## Module-level details

### pipeline.py (post-split, ~170 lines)
- **Imports**: `logging`, `re`, `datetime`, `typing`, `extractor`, `enricher`, `lead_scorer`, `analyzer.WebsiteAnalyzer`, `config_loader.load_config`
- **Removed**: `argparse`, `csv`, `html`, `json`, `tempfile`, `os`, `sys`, `yaml`, `dotenv`, `generate_audit_report` import, `AVAILABLE_INDUSTRIES`, `ALL_CITIES`, `load_config`, `export_csv`, `print_summary`, `export_html`, `load_leads_from_csv`, `main`, `run_interactive`
- **No `load_dotenv()`** — moved to `cli.py` where the entry point lives

### cli.py
- **Imports**: `argparse`, `logging`, `os`, `sys`, `datetime`, `yaml`, `dotenv`, `config_loader`, `pipeline.run_pipeline`, `exporters`, `reporters`, `analyzer.generate_audit_report`
- Calls `load_dotenv(".env.local"); load_dotenv(".env")` at module level
- `main()`: argparse identical to current — all 12 flags preserved
- `run_interactive()`: calls `get_default_industries()` and `get_default_locations()` for menus; writes `config.yaml` via `yaml.dump` on completion

### config_loader.py
- **Imports**: `os`, `sys`, `logging`, `typing`, `yaml`
- **Public**: `load_config(path)`, `get_default_industries()`, `get_default_locations()`
- `load_config`: unchanged from pipeline.py (lines 141-147)

### exporters.py
- **Imports**: `csv`, `logging`, `os`, `typing`
- **Public**: `export_csv(leads, output_path)`, `load_leads_from_csv(path)`

### reporters.py
- **Imports**: `html`, `logging`, `os`, `re`, `datetime`, `typing`
- **Public**: `print_summary(leads)`, `export_html(leads, output_path)`

### enricher.py (modified)
- **Add**: `from booking_data import BOOKING_DOMAINS, BOOKING_SKIP`
- **Remove**: inline `booking_domains` list (lines 134-142), `booking_skip` set (lines 143-145)
- The loop at lines 147-158 iterates `BOOKING_DOMAINS.keys()` instead of `booking_domains`. The skip reference changes from local `booking_skip` to `BOOKING_SKIP`

### analyzer.py (modified)
- **Add**: `from booking_data import BOOKING_DOMAINS, BOOKING_SKIP`
- **Remove**: inline `BOOKING_DOMAINS` dict (lines 18-39), `BOOKING_SKIP` set (lines 57-62)
- All usages at lines 264 and 272 continue to resolve identically

## Testing Strategy

No test framework exists (`strict_tdd: false` in openspec config). Verification is manual per spec scenarios:

| Scenario | Verification |
|----------|-------------|
| `files/lead_scorer.py` gone | `git ls-files files/lead_scorer.py` returns empty |
| Active scorer preserved | `git grep LeadScorer` only matches `lead_scorer.py` (root) |
| Booking union correct | Compare BOOKING_DOMAINS against both originals programmatically |
| `--interactive` first-run | Delete config.yaml, run, verify prompts identical |
| `--config config.yaml --limit 5` | Compare CSV output with main branch |
| `--from-csv leads.csv --html report.html` | Compare HTML output with main branch |
| `--audit report.html --from-csv leads.csv` | Compare audit output with main branch |
| Backward-compat imports | `python -c "from pipeline import load_config, export_csv, print_summary, main, run_interactive, export_html, load_leads_from_csv"` |
| All 12 CLI flags | Spot-check `--seo`, `--ads`, `--ig-web`, `--goal`, `--output`, `--google-key`, `--hunter-key` |

## Migration / Rollout

No migration required. Each task is independently revertible per-file via `git checkout HEAD -- <file>`. The full change is a single commit since all tasks modify non-overlapping areas.
