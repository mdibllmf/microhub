#!/usr/bin/env python3
"""Parse fbbi.obo into a JSON lookup table for MicroHub."""
import json
import re
import sys
import os

obo_path = sys.argv[1] if len(sys.argv) > 1 else "fbbi.obo"
if not os.path.exists(obo_path):
    print(f"  {obo_path} not found, skipping OBO parse", file=sys.stderr)
    sys.exit(1)

terms = []
current = None

with open(obo_path) as f:
    for line in f:
        line = line.strip()
        if line == "[Term]":
            if current:
                terms.append(current)
            current = {"id": "", "name": "", "synonyms": [], "is_a": [], "def": ""}
        elif current is not None:
            if line.startswith("id: "):
                current["id"] = line[4:]
            elif line.startswith("name: "):
                current["name"] = line[6:]
            elif line.startswith("def: "):
                current["def"] = line[5:].split('"')[1] if '"' in line else line[5:]
            elif line.startswith("synonym: "):
                match = re.search(r'"([^"]+)"', line)
                if match:
                    current["synonyms"].append(match.group(1))
            elif line.startswith("is_a: "):
                parent = line[6:].split("!")[0].strip()
                current["is_a"].append(parent)
            elif line.startswith("is_obsolete: true"):
                current["obsolete"] = True

    if current:
        terms.append(current)

# Filter out obsolete terms
active_terms = [t for t in terms if not t.get("obsolete")]

# Build lookup
lookup = {}
for t in active_terms:
    entry = {
        "id": t["id"],
        "canonical_name": t["name"],
        "definition": t["def"],
        "parents": t["is_a"]
    }
    # Index by name and all synonyms
    lookup[t["name"].lower()] = entry
    for syn in t["synonyms"]:
        lookup[syn.lower()] = entry

out_dir = os.path.dirname(obo_path) or "."

with open(os.path.join(out_dir, "fbbi_terms.json"), "w") as f:
    json.dump(active_terms, f, indent=2)

with open(os.path.join(out_dir, "fbbi_name_lookup.json"), "w") as f:
    json.dump(lookup, f, indent=2)

print(f"  {len(active_terms)} active terms, {len(lookup)} lookup entries")
