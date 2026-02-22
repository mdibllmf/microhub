# FBbi — Biological Imaging Methods Ontology

**Source:** https://obofoundry.org/ontology/fbbi
**GitHub:** https://github.com/Imaging-semantics/fbbi
**License:** CC BY 4.0
**Purpose:** Microscopy technique normalization (647 classes)

## Key Files
- `fbbi.owl` — Full OWL ontology
- `fbbi.obo` — OBO format (text-based, easier to parse)
- `fbbi_terms.json` — All active terms with IDs, names, synonyms, parents
- `fbbi_name_lookup.json` — Name/synonym → canonical term lookup

## Coverage
Covers sample preparation, visualization, and imaging methods:
- Confocal microscopy, STED, PALM, STORM, SIM, light sheet
- Brightfield, darkfield, DIC, phase contrast
- Electron microscopy (TEM, SEM, cryo-EM)
- Fluorescence techniques (FRAP, FRET, FLIM)
- Sample prep (immunofluorescence, live cell imaging, tissue clearing)

## Python Usage
```python
import json

with open('fbbi_name_lookup.json') as f:
    lookup = json.load(f)

query = "confocal microscopy"
if query.lower() in lookup:
    term = lookup[query.lower()]
    print(f"{query} → {term['canonical_name']} ({term['id']})")
```

## API Alternative (OLS4)
```
GET https://www.ebi.ac.uk/ols4/api/search?q=confocal+microscopy&ontology=fbbi
```
