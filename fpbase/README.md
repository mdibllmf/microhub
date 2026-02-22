# FPbase Lookup Table

**Source:** https://www.fpbase.org/
**GraphQL:** https://www.fpbase.org/graphql/
**License:** Open source (community-editable database)
**Purpose:** Fluorescent protein and synthetic dye validation + canonical naming

## Key Files
- `fpbase_all_fluorophores.json` — Complete export of all proteins + dyes with spectral data
- `fpbase_name_lookup.json` — Flat name→canonical lookup table (includes aliases)
- `_query.py` — Script to re-run the GraphQL export

## Python Usage
```python
import json

with open('fpbase_name_lookup.json') as f:
    lookup = json.load(f)

# Validate and canonicalize a fluorophore name
query = "egfp"
if query.lower() in lookup:
    info = lookup[query.lower()]
    print(f"{query} → {info['canonical_name']} ({info['type']})")
```

## Python Package (alternative)
```bash
pip install fpbase
```
```python
import fpbase
fp = fpbase.get_fluorophore("mCherry")
print(fp.name, fp.default_state.ex_max, fp.default_state.em_max)
```

## Coverage
Covers fluorescent proteins (EGFP, mCherry, tdTomato, etc.) AND synthetic dyes
(DAPI, Hoechst, Alexa Fluor series, Cy3/Cy5, FITC, TRITC, etc.)
