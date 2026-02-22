# ROR (Research Organization Registry) Lookup Table

**Source:** https://ror.org/
**Data Dump:** https://zenodo.org/doi/10.5281/zenodo.6347574
**License:** CC0 1.0 Universal (Public Domain)
**Purpose:** Institution name → ROR ID mapping for ~122,000 research organizations

## Key Files
- `v*.json` — Full registry in JSON format (schema v2)
- `v*.csv` — Subset of fields in CSV format

## Python Usage
```python
import json

with open('v2.2-2025-12-16-ror-data.json') as f:  # adjust filename
    orgs = json.load(f)

# Build lookup by name
name_to_ror = {}
for org in orgs:
    ror_id = org['id']
    for name_entry in org.get('names', []):
        name_to_ror[name_entry['value'].lower()] = ror_id

# Lookup
query = "harvard university"
print(name_to_ror.get(query.lower(), "Not found"))
```

## API Alternative (for fuzzy affiliation matching)
```
GET https://api.ror.org/v2/organizations?affiliation=Dept+of+Biology,+Harvard+University
```
The affiliation endpoint handles messy author affiliation strings.
Rate limit: 2,000 requests per 5-minute window.
