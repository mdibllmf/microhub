#!/usr/bin/env python3
"""
Export all FPbase fluorescent proteins via GraphQL API.
Outputs: fpbase_all_proteins.json
"""
import json
import urllib.request
import sys

GRAPHQL_URL = "https://www.fpbase.org/graphql/"

# Query to get all proteins with useful fields
QUERY = """{
  allProteins {
    edges {
      node {
        name
        slug
        aliases
        seq
        chromophore
        cofactor
        switchType
        defaultState {
          name
          exMax
          emMax
          extCoeff
          qy
          brightness
          lifetime
        }
        states {
          name
          exMax
          emMax
          extCoeff
          qy
          brightness
        }
      }
    }
  }
}"""

# Also get all dyes
DYES_QUERY = """{
  allDyes {
    edges {
      node {
        name
        slug
        aliases
        exMax
        emMax
        extCoeff
        qy
      }
    }
  }
}"""

def run_query(query, label):
    req = urllib.request.Request(
        GRAPHQL_URL,
        data=json.dumps({"query": query}).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "MicroHub-DataDownloader/1.0"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if "errors" in data:
                print(f"  GraphQL errors for {label}: {data['errors']}", file=sys.stderr)
                return None
            return data["data"]
    except Exception as e:
        print(f"  Failed to query {label}: {e}", file=sys.stderr)
        return None

print("  Fetching all proteins...")
proteins_data = run_query(QUERY, "proteins")

print("  Fetching all dyes...")
dyes_data = run_query(DYES_QUERY, "dyes")

output = {
    "download_date": __import__("datetime").datetime.now().isoformat(),
    "source": "https://www.fpbase.org/graphql/",
    "proteins": [],
    "dyes": []
}

if proteins_data and "allProteins" in proteins_data:
    output["proteins"] = [edge["node"] for edge in proteins_data["allProteins"]["edges"]]
    print(f"  Retrieved {len(output['proteins'])} proteins")

if dyes_data and "allDyes" in dyes_data:
    output["dyes"] = [edge["node"] for edge in dyes_data["allDyes"]["edges"]]
    print(f"  Retrieved {len(output['dyes'])} dyes")

# Write full export
outpath = sys.argv[1] if len(sys.argv) > 1 else "fpbase_all_fluorophores.json"
with open(outpath, "w") as f:
    json.dump(output, f, indent=2)
print(f"  Written to {outpath}")

# Also write a simple name lookup table
lookup = {}
for p in output["proteins"]:
    canonical = p["name"]
    lookup[canonical.lower()] = {"canonical_name": canonical, "type": "protein"}
    if p.get("aliases"):
        for alias in p["aliases"]:
            if alias:
                lookup[alias.lower()] = {"canonical_name": canonical, "type": "protein"}

for d in output["dyes"]:
    canonical = d["name"]
    lookup[canonical.lower()] = {"canonical_name": canonical, "type": "dye"}
    if d.get("aliases"):
        for alias in d["aliases"]:
            if alias:
                lookup[alias.lower()] = {"canonical_name": canonical, "type": "dye"}

lookup_path = outpath.replace("_all_fluorophores.json", "_name_lookup.json")
with open(lookup_path, "w") as f:
    json.dump(lookup, f, indent=2)
print(f"  Name lookup table ({len(lookup)} entries) written to {lookup_path}")
