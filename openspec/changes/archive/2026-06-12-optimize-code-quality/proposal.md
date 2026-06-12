# Proposal: Optimize Code Quality

## Intent

Clean up technical debt across 4 areas: inline HTML templates, magic numbers, orphaned files, and exact-match dedup. No behavioral changes — pure quality improvement after the major structural refactoring.

## Scope

### In Scope
- **Jinja2 templates**: Replace f-string HTML in reporters.py and analyzer.py with Jinja2 templates (base.html, lead_report.html, audit_report.html)
- **Module-level constants**: Extract ~30 magic numbers from analyzer.py, lead_scorer.py, extractor.py, enricher.py as UPPER_CASE constants
- **files/ cleanup**: Delete QUICK_START_GUIDE.md + README.md (dupes of root), move 4 reference docs to docs/, keep SKILL.md + lead_template.csv
- **Fuzzy dedup**: Add rapidfuzz token_sort_ratio dedup at threshold 85 to pipeline.py

### Out of Scope
- Config migration for thresholds/weights (deferred to own change)
- Async aiohttp extraction (deferred)
- HTML redesign — same visual output, rendered from templates

## Capabilities

> Contract between proposal and specs phases.

### New Capabilities
None — pure refactor, no new user-facing capabilities.

### Modified Capabilities
None — all CLI flags, HTML output, and scoring behavior remain identical.

## Approach

4 independent deliverables, implement in any order:

1. **Templates**: Add Jinja2 dep → create `templates/` with `base.html` (outer shell) + `lead_report.html` + `audit_report.html` → update reporters.py + analyzer.py to use `Environment().get_template().render(data)`
2. **Constants**: grep bare numeric literals → extract as `MODULE_LEVEL = value` at top or near usage grouping
3. **Cleanup**: `rm` duplicates → `mkdir -p docs/` → `mv` 4 reference files → keep SKILL.md + lead_template.csv in files/
4. **Dedup**: Add rapidfuzz dep → `deduplicate(leads, threshold=85)` using `token_sort_ratio` → call in `run_pipeline()` before return, sorted by score desc

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `reporters.py` | Modified | Replace f-string HTML with Jinja2 render |
| `analyzer.py` | Modified | Replace f-string HTML with Jinja2 render; extract magic numbers |
| `lead_scorer.py` | Modified | Extract magic numbers |
| `extractor.py` | Modified | Extract magic numbers |
| `enricher.py` | Modified | Extract magic numbers |
| `pipeline.py` | Modified | Add dedup call |
| `requirements.txt` | Modified | Add Jinja2, rapidfuzz |
| `templates/` | New | 3 Jinja2 template files |
| `files/QUICK_START_GUIDE.md` | Deleted | Duplicate of root README |
| `files/README.md` | Deleted | Duplicate of root README |
| `files/*.md → docs/` | Moved | 4 reference files |
| `files/lead_template.csv` | Kept | Stays as input example |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Jinja2 template differs visually | Low | Render HTML and diff against known-good snapshot |
| Constant extraction misses a literal | Low | Run `grep -n '\d\+'` on modified files after |
| Fuzzy dedup drops valid leads | Low | Threshold 85 is conservative; sort by score desc |

## Rollback Plan

Per-deliverable `git revert` — each deliverable in its own commit. Clean per-file rollback if needed.

## Dependencies

- Jinja2 (PyPI, MIT)
- rapidfuzz (PyPI, MIT)

## Success Criteria

- [ ] `python pipeline.py --limit 3 --html test.html` produces identical HTML output (diff against pre-change snapshot)
- [ ] `python pipeline.py --limit 1 --csv test.csv` produces identical CSV output
- [ ] No bare numeric literals in analyzer.py, lead_scorer.py, extractor.py, enricher.py (excluding 0, 1, and index lookups)
- [ ] `files/` contains only SKILL.md and lead_template.csv
- [ ] Dedup merges "Café A" and "Cafe A" into one lead
