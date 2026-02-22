#!/usr/bin/env python3
"""
Download bulk lookup data for local-first validation.

Run this ONCE (or periodically to refresh). Downloads:
  1. ROR data dump     (~50 MB JSON)  — all ~110K research organizations
  2. Cellosaurus       (~25 MB JSON)  — all ~150K cell lines
  3. NCBI Taxonomy     (~60 MB)       — all organism names → tax IDs
  4. FPbase proteins   (~2 MB JSON)   — all fluorescent proteins

Files are stored in: microhub_lookup_tables/

Usage:
    python download_lookup_data.py                  # download all
    python download_lookup_data.py --only ror       # download just ROR
    python download_lookup_data.py --only taxonomy   # download just NCBI taxonomy
    python download_lookup_data.py --dir /path/to/dir  # custom directory
"""

import argparse
import gzip
import io
import json
import logging
import os
import shutil
import sys
import tarfile
import time
import zipfile

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

try:
    import requests
except ImportError:
    logger.error("'requests' package required: pip install requests")
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DIR = os.path.join(SCRIPT_DIR, "microhub_lookup_tables")


# ======================================================================
# 1. ROR Data Dump
# ======================================================================

def download_ror(output_dir: str) -> str:
    """Download the latest ROR data dump from Zenodo.

    ROR publishes versioned data dumps as JSON-zipped archives.
    We download the latest, extract, and build a flat lookup JSON:
      { "institution name (lowercase)": {"ror_id": "...", "name": "...", "country": "..."} }
    Plus an inverted index of aliases.
    """
    logger.info("=== Downloading ROR data dump ===")

    # Find latest release via Zenodo API
    resp = requests.get(
        "https://zenodo.org/api/records",
        params={"communities": "ror-data", "sort": "mostrecent", "size": 1},
        timeout=30,
    )
    resp.raise_for_status()
    records = resp.json().get("hits", {}).get("hits", [])
    if not records:
        logger.error("No ROR records found on Zenodo")
        return ""

    # Find the JSON zip file in the record
    files = records[0].get("files", [])
    json_zip = None
    for f in files:
        if f.get("key", "").endswith(".zip") and "json" in f.get("key", "").lower():
            json_zip = f
            break
    if not json_zip:
        # Fallback: any zip
        for f in files:
            if f.get("key", "").endswith(".zip"):
                json_zip = f
                break

    if not json_zip:
        logger.error("No ZIP file found in latest ROR record")
        return ""

    download_url = json_zip["links"]["self"]
    file_size = json_zip.get("size", 0)
    logger.info("Downloading: %s (%.1f MB)", json_zip["key"], file_size / 1e6)

    # Download
    resp = requests.get(download_url, stream=True, timeout=120)
    resp.raise_for_status()

    zip_path = os.path.join(output_dir, "ror_dump.zip")
    with open(zip_path, "wb") as f:
        for chunk in resp.iter_content(8192):
            f.write(chunk)

    # Extract JSON from zip
    logger.info("Extracting ROR data...")
    ror_orgs = []
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            if name.endswith(".json") and not name.startswith("__"):
                with zf.open(name) as jf:
                    data = json.load(jf)
                    if isinstance(data, list):
                        ror_orgs = data
                    break

    if not ror_orgs:
        logger.error("No organization data found in ROR zip")
        return ""

    # Build lookup index: name → {ror_id, name, country, types, aliases}
    logger.info("Building ROR index from %d organizations...", len(ror_orgs))
    index = {}
    for org in ror_orgs:
        ror_id = org.get("id", "").replace("https://ror.org/", "")
        if not ror_id:
            continue

        # Get display name
        names = org.get("names", [])
        display_name = ""
        all_names = []
        for n in names:
            if isinstance(n, dict):
                val = n.get("value", "")
                types = n.get("types", [])
                if val:
                    all_names.append(val)
                if "ror_display" in types:
                    display_name = val
            elif isinstance(n, str):
                all_names.append(n)

        if not display_name:
            display_name = all_names[0] if all_names else ""
        if not display_name:
            continue

        # Country
        country = ""
        country_code = ""
        locations = org.get("locations", [])
        if locations:
            geo = locations[0].get("geonames_details", {})
            country = geo.get("country_name", "")
            country_code = geo.get("country_code", "")

        # Types
        types = org.get("types", [])

        # Status
        status = org.get("status", "active")
        if status != "active":
            continue  # Skip inactive/deprecated

        entry = {
            "ror_id": ror_id,
            "name": display_name,
            "country": country,
            "country_code": country_code,
            "types": types,
        }

        # Index by all name variants (lowercase)
        for name_str in all_names:
            key = name_str.strip().lower()
            if key and len(key) > 2:
                index[key] = entry

        # Also add acronyms if present
        for n in names:
            if isinstance(n, dict) and "acronym" in n.get("types", []):
                acr = n.get("value", "").strip().lower()
                if acr and len(acr) > 1:
                    index[acr] = entry

    out_path = os.path.join(output_dir, "ror_lookup.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False)

    # Clean up zip
    os.remove(zip_path)

    logger.info("ROR index: %d name variants → %d unique organizations",
                len(index), len(set(v["ror_id"] for v in index.values())))
    return out_path


# ======================================================================
# 2. Cellosaurus
# ======================================================================

def download_cellosaurus(output_dir: str) -> str:
    """Download Cellosaurus cell line database and build lookup.

    Source: ExPASy FTP (cellosaurus.txt)
    Output: { "cell line name (lowercase)": {"accession": "CVCL_xxxx", "name": "...", "species": "..."} }
    """
    logger.info("=== Downloading Cellosaurus ===")

    url = "https://ftp.expasy.org/databases/cellosaurus/cellosaurus.txt"
    logger.info("Downloading cellosaurus.txt (~180 MB)...")

    resp = requests.get(url, stream=True, timeout=300)
    resp.raise_for_status()

    raw_path = os.path.join(output_dir, "cellosaurus.txt")
    with open(raw_path, "wb") as f:
        for chunk in resp.iter_content(65536):
            f.write(chunk)

    logger.info("Parsing Cellosaurus entries...")
    index = {}
    current = {}
    count = 0

    with open(raw_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("//"):
                # End of entry
                if current.get("accession") and current.get("name"):
                    entry = {
                        "accession": current["accession"],
                        "name": current["name"],
                        "species": current.get("species", ""),
                        "disease": current.get("disease", ""),
                        "category": current.get("category", ""),
                    }
                    # Index by primary name
                    index[current["name"].lower()] = entry
                    # Index by synonyms
                    for syn in current.get("synonyms", []):
                        syn_key = syn.strip().lower()
                        if syn_key and syn_key not in index:
                            index[syn_key] = entry
                    count += 1
                current = {}
            elif line.startswith("ID   "):
                current["name"] = line[5:].strip()
            elif line.startswith("AC   "):
                current["accession"] = line[5:].strip()
            elif line.startswith("SY   "):
                syns = line[5:].strip()
                current.setdefault("synonyms", []).extend(
                    [s.strip() for s in syns.split(";") if s.strip()]
                )
            elif line.startswith("OX   "):
                # Species: "NCBI_TaxID=9606; ! Homo sapiens"
                species_part = line[5:].strip()
                if "! " in species_part:
                    current["species"] = species_part.split("! ", 1)[1].strip()
            elif line.startswith("DI   "):
                # Disease
                di_part = line[5:].strip()
                if "; " in di_part:
                    parts = di_part.split("; ")
                    if len(parts) >= 2:
                        current["disease"] = parts[1].strip()
            elif line.startswith("CA   "):
                current["category"] = line[5:].strip()

    out_path = os.path.join(output_dir, "cellosaurus_lookup.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False)

    # Clean up raw file (180 MB)
    os.remove(raw_path)

    logger.info("Cellosaurus index: %d name variants from %d cell lines", len(index), count)
    return out_path


# ======================================================================
# 3. NCBI Taxonomy
# ======================================================================

def download_taxonomy(output_dir: str) -> str:
    """Download NCBI taxonomy names.dmp and build lookup.

    Source: NCBI FTP (taxdump.tar.gz)
    Output: { "organism name (lowercase)": {"tax_id": 9606, "scientific_name": "Homo sapiens", "rank": "species"} }
    """
    logger.info("=== Downloading NCBI Taxonomy ===")

    url = "https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdump.tar.gz"
    logger.info("Downloading taxdump.tar.gz (~60 MB)...")

    resp = requests.get(url, stream=True, timeout=300)
    resp.raise_for_status()

    tar_path = os.path.join(output_dir, "taxdump.tar.gz")
    with open(tar_path, "wb") as f:
        for chunk in resp.iter_content(65536):
            f.write(chunk)

    # Extract names.dmp and nodes.dmp
    logger.info("Extracting taxonomy data...")
    with tarfile.open(tar_path, "r:gz") as tar:
        # Extract names.dmp
        try:
            names_member = tar.getmember("names.dmp")
            tar.extract(names_member, output_dir)
        except KeyError:
            logger.error("names.dmp not found in taxdump.tar.gz")
            return ""
        # Extract nodes.dmp for rank info
        try:
            nodes_member = tar.getmember("nodes.dmp")
            tar.extract(nodes_member, output_dir)
        except KeyError:
            pass  # Optional

    names_path = os.path.join(output_dir, "names.dmp")
    nodes_path = os.path.join(output_dir, "nodes.dmp")

    # Parse nodes.dmp for rank info
    ranks = {}
    if os.path.exists(nodes_path):
        with open(nodes_path, "r") as f:
            for line in f:
                parts = line.strip().split("\t|\t")
                if len(parts) >= 3:
                    tax_id = int(parts[0].strip())
                    rank = parts[2].strip().rstrip("\t|")
                    ranks[tax_id] = rank

    # Parse names.dmp
    logger.info("Parsing taxonomy names...")
    index = {}
    scientific_names = {}  # tax_id → scientific_name

    with open(names_path, "r") as f:
        for line in f:
            parts = line.strip().rstrip("\t|").split("\t|\t")
            if len(parts) < 4:
                continue
            tax_id = int(parts[0].strip())
            name = parts[1].strip()
            name_class = parts[3].strip().rstrip("\t|")

            if name_class == "scientific name":
                scientific_names[tax_id] = name

    # Build index from scientific names + synonyms
    # Re-read for all names
    with open(names_path, "r") as f:
        for line in f:
            parts = line.strip().rstrip("\t|").split("\t|\t")
            if len(parts) < 4:
                continue
            tax_id = int(parts[0].strip())
            name = parts[1].strip()
            name_class = parts[3].strip().rstrip("\t|")

            # Only index species and below, plus key genera
            rank = ranks.get(tax_id, "")
            if rank not in ("species", "subspecies", "varietas", "forma",
                            "genus", "strain"):
                continue

            key = name.lower()
            if key and len(key) > 2:
                entry = {
                    "tax_id": tax_id,
                    "scientific_name": scientific_names.get(tax_id, name),
                    "name_class": name_class,
                    "rank": rank,
                }
                # Prefer scientific names over synonyms
                if key not in index or name_class == "scientific name":
                    index[key] = entry

    out_path = os.path.join(output_dir, "taxonomy_lookup.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False)

    # Clean up
    os.remove(tar_path)
    os.remove(names_path)
    if os.path.exists(nodes_path):
        os.remove(nodes_path)

    logger.info("Taxonomy index: %d name variants", len(index))
    return out_path


# ======================================================================
# 4. FPbase Fluorescent Proteins
# ======================================================================

def download_fpbase(output_dir: str) -> str:
    """Download all fluorescent proteins from FPbase API.

    Output: { "protein name (lowercase)": {"name": "...", "ex_max": 488, "em_max": 509, ...} }
    """
    logger.info("=== Downloading FPbase proteins ===")

    index = {}
    url = "https://www.fpbase.org/api/proteins/"
    params = {"format": "json", "limit": 200}
    page = 0

    while url:
        page += 1
        logger.info("  Page %d...", page)
        try:
            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code != 200:
                logger.warning("FPbase API returned %d", resp.status_code)
                break
            data = resp.json()
        except Exception as e:
            logger.warning("FPbase API error: %s", e)
            break

        for protein in data.get("results", []):
            name = protein.get("name", "")
            if not name:
                continue

            state = protein.get("default_state") or {}
            entry = {
                "name": name,
                "slug": protein.get("slug", ""),
                "ex_max": state.get("ex_max"),
                "em_max": state.get("em_max"),
                "qy": state.get("qy"),
                "ext_coeff": state.get("ext_coeff"),
                "brightness": state.get("brightness"),
                "cofactor": protein.get("cofactor", ""),
                "switch_type": protein.get("switch_type", ""),
            }

            # Index by primary name
            index[name.lower()] = entry

            # Index by aliases
            for alias in protein.get("aliases", []):
                if alias:
                    index[alias.lower()] = entry

        url = data.get("next")
        params = {}  # next URL already includes params
        time.sleep(0.3)  # Be polite

    out_path = os.path.join(output_dir, "fpbase_lookup.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False)

    logger.info("FPbase index: %d name variants from %d proteins",
                len(index), len(set(v["name"] for v in index.values())))
    return out_path


# ======================================================================
# Main
# ======================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Download bulk lookup data for MicroHub pipeline"
    )
    parser.add_argument(
        "--dir", default=DEFAULT_DIR,
        help="Output directory (default: microhub_lookup_tables/)",
    )
    parser.add_argument(
        "--only", choices=["ror", "cellosaurus", "taxonomy", "fpbase"],
        help="Download only one dataset",
    )
    args = parser.parse_args()

    os.makedirs(args.dir, exist_ok=True)
    logger.info("Output directory: %s", args.dir)

    downloaders = {
        "ror": download_ror,
        "cellosaurus": download_cellosaurus,
        "taxonomy": download_taxonomy,
        "fpbase": download_fpbase,
    }

    if args.only:
        downloaders[args.only](args.dir)
    else:
        for name, func in downloaders.items():
            try:
                func(args.dir)
            except Exception as e:
                logger.error("Failed to download %s: %s", name, e)
            print()

    # Write metadata
    meta = {
        "downloaded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "files": os.listdir(args.dir),
    }
    with open(os.path.join(args.dir, "metadata.json"), "w") as f:
        json.dump(meta, f, indent=2)

    logger.info("Done! Lookup tables ready in: %s", args.dir)
    logger.info("Files:")
    for fname in sorted(os.listdir(args.dir)):
        fpath = os.path.join(args.dir, fname)
        size = os.path.getsize(fpath) / 1e6
        logger.info("  %s (%.1f MB)", fname, size)


if __name__ == "__main__":
    main()
