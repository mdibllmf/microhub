"""
Cellosaurus API client for cell line validation and enrichment.

Uses the Cellosaurus REST API (https://api.cellosaurus.org) to:
  - Validate cell line names against the Cellosaurus database
  - Retrieve species of origin, disease, and cross-references
  - Map cell line names to Cellosaurus accession IDs (CVCL_xxxx)
  - Provide STR profile data when available

Cellosaurus is the most comprehensive cell line knowledge base,
maintained by the SIB Swiss Institute of Bioinformatics.  It covers
~150k cell lines with extensive metadata and is freely accessible
without authentication.

Rate limit: No official limit, but we use 0.3s delay to be polite.

Usage:
    from pipeline.validation.cellosaurus_client import CellosaurusClient
    client = CellosaurusClient()
    result = client.validate("HeLa")
    # {'accession': 'CVCL_0030', 'name': 'HeLa', 'species': 'Homo sapiens',
    #  'disease': 'Cervical adenocarcinoma', 'sex': 'Female', ...}
"""

import logging
import os
import re
import time
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

_CELLOSAURUS_API = "https://api.cellosaurus.org"


class CellosaurusClient:
    """Validate and enrich cell line names via the Cellosaurus REST API.

    Thread-safe with per-instance rate limiting and caching.
    Supports local-first validation from the cellosaurus.txt flat file.
    """

    def __init__(self, delay: float = 0.3, local_path: str = None):
        self._cache: Dict[str, Optional[Dict[str, Any]]] = {}
        self._last_call = 0.0
        self._delay = delay
        self._exhausted = False
        self._local_index: Dict[str, Dict[str, Any]] = {}
        self._local_loaded = False
        self._local_path = local_path  # deferred to first use

    def _ensure_local_loaded(self):
        """Lazy-load local flat file on first use."""
        if not self._local_loaded and self._local_path:
            self._load_local(self._local_path)
            self._local_path = None  # prevent re-loading

    def _load_local(self, path: str):
        """Parse cellosaurus.txt flat file into a fast lookup index."""
        txt_path = path
        if os.path.isdir(path):
            txt_path = os.path.join(path, "cellosaurus.txt")

        if not os.path.exists(txt_path):
            logger.warning("Cellosaurus flat file not found at %s", txt_path)
            return

        count = 0
        current: Dict[str, Any] = {}
        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.rstrip("\n")
                    if line == "//":
                        if current.get("name") and current.get("accession"):
                            entry = {
                                "accession": current["accession"],
                                "name": current["name"],
                                "synonyms": current.get("synonyms", []),
                                "species": current.get("species", ""),
                                "species_tax_id": current.get("tax_id", ""),
                                "disease": current.get("disease", ""),
                                "category": current.get("category", ""),
                            }
                            # Index by primary name
                            self._local_index[current["name"].lower()] = entry
                            # Index by all synonyms
                            for syn in current.get("synonyms", []):
                                syn_lower = syn.strip().lower()
                                if syn_lower and syn_lower not in self._local_index:
                                    self._local_index[syn_lower] = entry
                            count += 1
                            if count % 50000 == 0:
                                logger.info("  ... loaded %d cell lines so far", count)
                        current = {}
                    elif line.startswith("ID   "):
                        current["name"] = line[5:].strip()
                    elif line.startswith("AC   "):
                        current["accession"] = line[5:].strip()
                    elif line.startswith("SY   "):
                        syns = line[5:].split(";")
                        current.setdefault("synonyms", []).extend(
                            s.strip() for s in syns if s.strip()
                        )
                    elif line.startswith("OX   "):
                        # "NCBI_TaxID=9606; ! Homo sapiens"
                        parts = line[5:].split("!")
                        if len(parts) > 1:
                            current["species"] = parts[1].strip()
                        tax_match = re.search(r'NCBI_TaxID=(\d+)', line)
                        if tax_match:
                            current["tax_id"] = tax_match.group(1)
                    elif line.startswith("DI   "):
                        # "NCIt; C27677; Cervical adenocarcinoma"
                        parts = line[5:].split(";")
                        if len(parts) >= 3:
                            current["disease"] = parts[2].strip()
                    elif line.startswith("CA   "):
                        current["category"] = line[5:].strip()

            self._local_loaded = True
            logger.info(
                "Cellosaurus local index loaded: %d cell lines, %d lookup keys",
                count, len(self._local_index),
            )
        except Exception as exc:
            logger.warning("Failed to load Cellosaurus flat file: %s", exc)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate(self, cell_line_name: str) -> Optional[Dict[str, Any]]:
        """Validate a single cell line name against Cellosaurus.

        Parameters
        ----------
        cell_line_name : str
            The cell line name to validate (e.g., "HeLa", "HEK293T").

        Returns
        -------
        dict or None
            If found, returns a dict with keys:
              - accession: Cellosaurus accession ID (e.g., "CVCL_0030")
              - name: Canonical cell line name
              - synonyms: List of known synonyms
              - species: Species of origin
              - disease: Associated disease (if any)
              - sex: Sex of the donor (if known)
              - category: Cell line category (e.g., "Cancer cell line")
              - cross_references: List of cross-reference dicts
              - str_data: STR profile data (if available)
            Returns None if the cell line is not found.
        """
        if not cell_line_name:
            return None

        cache_key = cell_line_name.strip().lower()
        if cache_key in self._cache:
            return self._cache[cache_key]

        # LOCAL FIRST (lazy-load on first use)
        self._ensure_local_loaded()
        if self._local_loaded:
            entry = self._local_index.get(cache_key)
            if entry:
                self._cache[cache_key] = entry
                return entry

        # FALLBACK: original API search
        if not HAS_REQUESTS or self._exhausted:
            return None
        result = self._search_cell_line(cell_line_name.strip())
        self._cache[cache_key] = result
        return result

    def validate_batch(
        self, cell_line_names: List[str]
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        """Validate multiple cell line names.

        Parameters
        ----------
        cell_line_names : list of str
            Cell line names to validate.

        Returns
        -------
        dict mapping cell line name -> validation result (or None)
        """
        results: Dict[str, Optional[Dict[str, Any]]] = {}
        for name in cell_line_names:
            if not name:
                continue
            results[name] = self.validate(name)
            if self._exhausted:
                break
        return results

    def enrich_cell_lines(
        self, cell_line_names: List[str]
    ) -> List[Dict[str, Any]]:
        """Validate and enrich a list of cell line names.

        Returns a list of enriched dicts for all cell lines that were
        successfully validated.  Cell lines not found in Cellosaurus
        are included with ``validated=False``.
        """
        enriched: List[Dict[str, Any]] = []
        for name in cell_line_names:
            if not name:
                continue
            result = self.validate(name)
            if result:
                entry = dict(result)
                entry["validated"] = True
                entry["original_name"] = name
                enriched.append(entry)
            else:
                enriched.append({
                    "name": name,
                    "original_name": name,
                    "validated": False,
                })
        return enriched

    # ------------------------------------------------------------------
    # Internal: API queries
    # ------------------------------------------------------------------

    def _search_cell_line(self, name: str) -> Optional[Dict[str, Any]]:
        """Search Cellosaurus for a cell line by name."""
        # Strategy: use the search endpoint with the cell line name,
        # then parse the best matching result.

        self._rate_limit()
        try:
            # Use the cell-line search endpoint
            resp = requests.get(
                f"{_CELLOSAURUS_API}/search/cell-line",
                params={
                    "q": name,
                    "fields": "id,ac,sy,ox,di,sx,ca,dr,str",
                    "format": "json",
                },
                timeout=15,
                headers={"Accept": "application/json"},
            )
            self._last_call = time.time()

            if resp.status_code == 429:
                logger.warning("Cellosaurus rate limited")
                self._exhausted = True
                return None

            if resp.status_code != 200:
                logger.debug(
                    "Cellosaurus HTTP %d for '%s'", resp.status_code, name
                )
                return None

            data = resp.json()
            return self._find_best_match(data, name)

        except Exception as exc:
            logger.debug("Cellosaurus error for '%s': %s", name, exc)
            return None

    def _find_best_match(
        self, data: Dict[str, Any], query: str
    ) -> Optional[Dict[str, Any]]:
        """Find the best matching cell line from Cellosaurus search results."""
        cell_lines = data.get("result", {}).get("cell-line-list", [])
        if not cell_lines:
            return None

        query_lower = query.lower()

        # First pass: exact name match
        for cl in cell_lines:
            cl_name = self._get_name(cl)
            if cl_name and cl_name.lower() == query_lower:
                return self._parse_cell_line(cl)

        # Second pass: exact synonym match
        for cl in cell_lines:
            synonyms = self._get_synonyms(cl)
            for syn in synonyms:
                if syn.lower() == query_lower:
                    return self._parse_cell_line(cl)

        # Third pass: case-insensitive prefix match on name
        for cl in cell_lines:
            cl_name = self._get_name(cl)
            if cl_name and cl_name.lower().startswith(query_lower):
                return self._parse_cell_line(cl)

        # Fall back to first result if search returned anything
        if cell_lines:
            first = cell_lines[0]
            first_name = self._get_name(first)
            # Only accept if the name is reasonably similar
            if first_name and (
                query_lower in first_name.lower()
                or first_name.lower() in query_lower
            ):
                return self._parse_cell_line(first)

        return None

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_name(cl: Dict) -> str:
        """Extract the primary name from a Cellosaurus cell line entry."""
        # The name field varies by API version
        name_info = cl.get("id") or cl.get("ID") or ""
        if isinstance(name_info, str):
            return name_info
        if isinstance(name_info, dict):
            return name_info.get("value", "")
        return ""

    @staticmethod
    def _get_accession(cl: Dict) -> str:
        """Extract the accession ID (CVCL_xxxx)."""
        ac = cl.get("ac") or cl.get("AC") or ""
        if isinstance(ac, str):
            return ac
        if isinstance(ac, list) and ac:
            return ac[0] if isinstance(ac[0], str) else ac[0].get("value", "")
        if isinstance(ac, dict):
            return ac.get("value", "")
        return ""

    @staticmethod
    def _get_synonyms(cl: Dict) -> List[str]:
        """Extract synonym list."""
        sy = cl.get("sy") or cl.get("SY") or []
        if isinstance(sy, str):
            # Semicolon-separated list
            return [s.strip() for s in sy.split(";") if s.strip()]
        if isinstance(sy, list):
            result = []
            for item in sy:
                if isinstance(item, str):
                    result.append(item)
                elif isinstance(item, dict):
                    result.append(item.get("value", ""))
            return result
        return []

    def _parse_cell_line(self, cl: Dict) -> Dict[str, Any]:
        """Parse a Cellosaurus cell line entry into a clean dict."""
        result: Dict[str, Any] = {
            "accession": self._get_accession(cl),
            "name": self._get_name(cl),
            "synonyms": self._get_synonyms(cl),
        }

        # Species of origin (OX field)
        ox = cl.get("ox") or cl.get("OX") or cl.get("species-list") or []
        species = self._parse_species(ox)
        if species:
            result["species"] = species[0].get("name", "")
            result["species_tax_id"] = species[0].get("tax_id", "")
            if len(species) > 1:
                result["all_species"] = species

        # Disease (DI field)
        di = cl.get("di") or cl.get("DI") or cl.get("disease-list") or []
        diseases = self._parse_diseases(di)
        if diseases:
            result["disease"] = diseases[0].get("name", "")
            result["disease_id"] = diseases[0].get("id", "")

        # Sex (SX field)
        sx = cl.get("sx") or cl.get("SX") or cl.get("sex") or ""
        if isinstance(sx, str) and sx:
            result["sex"] = sx
        elif isinstance(sx, dict):
            result["sex"] = sx.get("value", "")

        # Category (CA field)
        ca = cl.get("ca") or cl.get("CA") or cl.get("category") or ""
        if isinstance(ca, str) and ca:
            result["category"] = ca
        elif isinstance(ca, dict):
            result["category"] = ca.get("value", "")

        # Cross-references (DR field) — select useful ones
        dr = cl.get("dr") or cl.get("DR") or cl.get("xref-list") or []
        result["cross_references"] = self._parse_cross_refs(dr)

        # STR profile data (if available)
        str_data = cl.get("str") or cl.get("STR") or cl.get("str-list") or []
        if str_data:
            result["str_data"] = self._parse_str_profile(str_data)

        return result

    @staticmethod
    def _parse_species(ox: Any) -> List[Dict[str, str]]:
        """Parse species/origin data."""
        species: List[Dict[str, str]] = []
        if isinstance(ox, str):
            # Simple text like "Homo sapiens"
            species.append({"name": ox, "tax_id": ""})
        elif isinstance(ox, list):
            for item in ox:
                if isinstance(item, str):
                    species.append({"name": item, "tax_id": ""})
                elif isinstance(item, dict):
                    name = (
                        item.get("species-name", "")
                        or item.get("value", "")
                        or item.get("name", "")
                    )
                    tax_id = str(
                        item.get("ncbi-taxonomy-id", "")
                        or item.get("tax_id", "")
                        or item.get("id", "")
                    )
                    if name:
                        species.append({"name": name, "tax_id": tax_id})
        elif isinstance(ox, dict):
            name = ox.get("species-name", "") or ox.get("value", "")
            tax_id = str(ox.get("ncbi-taxonomy-id", "") or ox.get("id", ""))
            if name:
                species.append({"name": name, "tax_id": tax_id})
        return species

    @staticmethod
    def _parse_diseases(di: Any) -> List[Dict[str, str]]:
        """Parse disease information."""
        diseases: List[Dict[str, str]] = []
        if isinstance(di, str) and di:
            diseases.append({"name": di, "id": ""})
        elif isinstance(di, list):
            for item in di:
                if isinstance(item, str):
                    diseases.append({"name": item, "id": ""})
                elif isinstance(item, dict):
                    name = (
                        item.get("disease-name", "")
                        or item.get("value", "")
                        or item.get("name", "")
                    )
                    did = (
                        item.get("accession", "")
                        or item.get("id", "")
                    )
                    if name:
                        diseases.append({"name": name, "id": did})
        elif isinstance(di, dict):
            name = di.get("disease-name", "") or di.get("value", "")
            did = di.get("accession", "") or di.get("id", "")
            if name:
                diseases.append({"name": name, "id": did})
        return diseases

    @staticmethod
    def _parse_cross_refs(dr: Any) -> List[Dict[str, str]]:
        """Parse cross-references, keeping the most useful databases."""
        USEFUL_DBS = {
            "ATCC", "DSMZ", "ECACC", "JCRB", "RIKEN",
            "Coriell", "CLS", "AddexBio", "ICLC",
            "BTO", "CLO", "EFO",
            "Wikidata", "DepMap",
        }
        refs: List[Dict[str, str]] = []
        if isinstance(dr, list):
            for item in dr:
                if isinstance(item, dict):
                    db = (
                        item.get("database", "")
                        or item.get("db", "")
                        or item.get("resource-name", "")
                    )
                    acc = (
                        item.get("accession", "")
                        or item.get("ac", "")
                        or item.get("id", "")
                    )
                    if db in USEFUL_DBS and acc:
                        refs.append({"database": db, "accession": acc})
                elif isinstance(item, str) and ";" in item:
                    parts = item.split(";", 1)
                    db = parts[0].strip()
                    acc = parts[1].strip() if len(parts) > 1 else ""
                    if db in USEFUL_DBS and acc:
                        refs.append({"database": db, "accession": acc})
        return refs

    @staticmethod
    def _parse_str_profile(str_data: Any) -> List[Dict[str, str]]:
        """Parse STR profile data."""
        profiles: List[Dict[str, str]] = []
        if isinstance(str_data, list):
            for item in str_data:
                if isinstance(item, dict):
                    marker = (
                        item.get("marker-name", "")
                        or item.get("marker", "")
                        or item.get("locus", "")
                    )
                    alleles = (
                        item.get("marker-alleles", "")
                        or item.get("alleles", "")
                        or item.get("value", "")
                    )
                    if marker:
                        profiles.append({
                            "marker": marker,
                            "alleles": str(alleles),
                        })
        return profiles

    # ------------------------------------------------------------------
    # Rate limiting
    # ------------------------------------------------------------------

    def _rate_limit(self) -> None:
        elapsed = time.time() - self._last_call
        if elapsed < self._delay:
            time.sleep(self._delay - elapsed)
