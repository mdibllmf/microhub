"""
API-based validation for extracted entities.

Validates tags against authoritative external databases:
  - FPbase API:       Fluorescent proteins and dyes
  - SciCrunch API:    RRIDs (antibodies, software, cell lines, plasmids)
  - ROR API:          Research organizations
  - NCBI Taxonomy:    Organism names → TaxIDs

Keys loaded from .env or environment variables.  All validators are
optional — if an API is unreachable the tag passes through unchanged.

Usage:
    validator = ApiValidator()
    validator.validate_paper(paper_results)  # mutates in-place
"""

import logging
import os
import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ---------------------------------------------------------------------------
# .env loader (shared with enrichment.py)
# ---------------------------------------------------------------------------
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)
)))


def _load_env_file() -> Dict[str, str]:
    env_path = os.path.join(_PROJECT_ROOT, ".env")
    vals: Dict[str, str] = {}
    if not os.path.exists(env_path):
        return vals
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                vals[key.strip()] = value.strip().strip("'\"")
    return vals


def _get_key(name: str) -> Optional[str]:
    val = os.environ.get(name)
    if val:
        return val
    return _load_env_file().get(name)


# ======================================================================
# API Validator
# ======================================================================

class ApiValidator:
    """Validate extracted entities against authoritative APIs."""

    def __init__(self):
        self._fpbase_cache: Dict[str, Optional[Dict]] = {}
        self._rrid_cache: Dict[str, Optional[Dict]] = {}
        self._ror_cache: Dict[str, Optional[Dict]] = {}
        self._taxon_cache: Dict[str, Optional[Dict]] = {}

        # Rate limiting
        self._last_call: Dict[str, float] = {}
        self._delays = {
            "fpbase": 0.2,
            "scicrunch": 0.5,
            "ror": 0.3,
            "ncbi": 0.4,
            "pubtator": 0.5,
        }

        # Track exhaustion per API
        self._exhausted: Set[str] = set()

    # ------------------------------------------------------------------
    # Public: validate a full paper result dict
    # ------------------------------------------------------------------

    def validate_paper(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enrich extracted entities.  Mutates in-place.

        Adds ``_validated`` metadata to indicate API confirmation.
        Removes clearly false-positive extractions.
        """
        if not HAS_REQUESTS:
            return results

        # 1. Validate fluorophores against FPbase
        if "fluorophores" in results:
            results["fluorophores"] = self._validate_fluorophores(
                results["fluorophores"]
            )

        # 2. Validate RRIDs against SciCrunch
        if "rrids" in results:
            results["rrids"] = self._validate_rrids(results["rrids"])

        # 3. Validate RORs against ROR API
        if "rors" in results:
            results["rors"] = self._validate_rors(results["rors"])

        # 4. Validate organisms against NCBI Taxonomy
        if "organisms" in results:
            results["organisms"] = self._validate_organisms(
                results["organisms"]
            )

        return results

    # ------------------------------------------------------------------
    # FPbase fluorophore validation
    # ------------------------------------------------------------------

    def _validate_fluorophores(self, fluorophores: List[str]) -> List[str]:
        """Validate fluorophore names against FPbase + known dye list."""
        if "fpbase" in self._exhausted:
            return fluorophores

        # Known organic dyes that FPbase won't have — pass through directly
        KNOWN_DYES = {
            "DAPI", "Hoechst 33342", "Hoechst 33258",
            "Propidium Iodide", "Phalloidin",
            "MitoTracker Red", "MitoTracker Green", "MitoTracker Deep Red",
            "LysoTracker Red", "LysoTracker Green", "LysoTracker Blue",
            "CellTracker Green", "CellTracker Red", "CellTracker Blue",
            "DiI", "DiD", "DiO", "DiR",
            "Calcein AM", "Calcein", "Fluo-4", "Fura-2", "Indo-1",
            "Rhodamine 123", "TMRM", "TMRE", "JC-1",
            "SYTOX Green", "SYTOX Blue", "SYTOX Orange",
            "SYTO 9", "SYTO 13", "SYTO 16",
            "Ethidium Homodimer-1", "7-AAD",
        }
        # Dye families — validate by regex pattern, not API lookup
        DYE_FAMILY_PATTERNS = [
            re.compile(r"^Alexa\s*Fluor\s*\d{3}[A-Z]?$", re.I),
            re.compile(r"^Cy[2-7](?:\.5)?$", re.I),
            re.compile(r"^ATTO\s*\d{3,4}N?$", re.I),
            re.compile(r"^DyLight\s*\d{3}$", re.I),
            re.compile(r"^CF\d{3}$", re.I),
            re.compile(r"^IRDye\s*\d+[A-Z]*$", re.I),
            re.compile(r"^(?:PE|APC|BV|BUV)\d{3}$", re.I),
        ]

        validated = []
        for fp_name in fluorophores:
            # Known dye — pass through
            if fp_name in KNOWN_DYES:
                validated.append(fp_name)
                continue

            # Dye family — pass through
            if any(p.match(fp_name) for p in DYE_FAMILY_PATTERNS):
                validated.append(fp_name)
                continue

            # Check FPbase for fluorescent proteins
            fp_data = self._query_fpbase(fp_name)
            if fp_data is not None:
                # Use canonical name from FPbase if different
                canonical = fp_data.get("name", fp_name)
                validated.append(canonical)
            else:
                # Not found in FPbase or dye lists — still keep but log
                logger.debug("Fluorophore not validated by FPbase: %s", fp_name)
                validated.append(fp_name)

        return validated

    def _query_fpbase(self, name: str) -> Optional[Dict]:
        """Query FPbase for a fluorescent protein by name."""
        if name in self._fpbase_cache:
            return self._fpbase_cache[name]

        self._rate_limit("fpbase")
        try:
            resp = requests.get(
                "https://www.fpbase.org/api/proteins/",
                params={"name__iexact": name, "format": "json"},
                timeout=10,
            )
            self._last_call["fpbase"] = time.time()

            if resp.status_code == 429:
                self._exhausted.add("fpbase")
                return None
            if resp.status_code != 200:
                return None

            data = resp.json()
            results = data.get("results", [])
            if results:
                self._fpbase_cache[name] = results[0]
                return results[0]

            # Try slug-based lookup (e.g., "mCherry" → slug "mcherry")
            slug = name.lower().replace(" ", "-")
            resp2 = requests.get(
                f"https://www.fpbase.org/api/proteins/{slug}/",
                params={"format": "json"},
                timeout=10,
            )
            if resp2.status_code == 200:
                result = resp2.json()
                self._fpbase_cache[name] = result
                return result

            self._fpbase_cache[name] = None
            return None

        except Exception:
            return None

    # ------------------------------------------------------------------
    # RRID validation against SciCrunch
    # ------------------------------------------------------------------

    def _validate_rrids(self, rrids: List[Dict]) -> List[Dict]:
        """Validate RRIDs against SciCrunch resolver API."""
        if "scicrunch" in self._exhausted:
            return rrids

        validated = []
        for rrid_entry in rrids:
            rrid_id = rrid_entry.get("id", "")
            if not rrid_id:
                continue

            sc_data = self._query_scicrunch(rrid_id)
            if sc_data is not None:
                # Enrich with SciCrunch data
                if sc_data.get("name"):
                    rrid_entry["name"] = sc_data["name"]
                if sc_data.get("type"):
                    rrid_entry["type"] = sc_data["type"]
                rrid_entry["validated"] = True
            else:
                rrid_entry["validated"] = False

            validated.append(rrid_entry)

        return validated

    def _query_scicrunch(self, rrid: str) -> Optional[Dict]:
        """Query SciCrunch resolver for RRID metadata."""
        if rrid in self._rrid_cache:
            return self._rrid_cache[rrid]

        self._rate_limit("scicrunch")
        try:
            # SciCrunch resolver API
            resp = requests.get(
                f"https://scicrunch.org/resolver/{rrid}.json",
                timeout=10,
            )
            self._last_call["scicrunch"] = time.time()

            if resp.status_code == 429:
                self._exhausted.add("scicrunch")
                return None
            if resp.status_code != 200:
                self._rrid_cache[rrid] = None
                return None

            data = resp.json()
            # SciCrunch returns nested structure
            hits = data.get("hits", {}).get("hits", [])
            if hits:
                source = hits[0].get("_source", {})
                result = {
                    "name": source.get("item", {}).get("name", ""),
                    "type": source.get("item", {}).get("types", [""])[0]
                             if source.get("item", {}).get("types") else "",
                }
                self._rrid_cache[rrid] = result
                return result

            self._rrid_cache[rrid] = None
            return None

        except Exception:
            return None

    # ------------------------------------------------------------------
    # ROR validation
    # ------------------------------------------------------------------

    def _validate_rors(self, rors: List[Dict]) -> List[Dict]:
        """Validate ROR IDs against the ROR API."""
        if "ror" in self._exhausted:
            return rors

        validated = []
        for ror_entry in rors:
            ror_id = ror_entry.get("id", "")
            if not ror_id:
                continue

            ror_data = self._query_ror(ror_id)
            if ror_data is not None:
                if ror_data.get("name"):
                    ror_entry["name"] = ror_data["name"]
                if ror_data.get("country"):
                    ror_entry["country"] = ror_data["country"]
                ror_entry["validated"] = True
            else:
                ror_entry["validated"] = False

            validated.append(ror_entry)

        return validated

    def _query_ror(self, ror_id: str) -> Optional[Dict]:
        """Query ROR API for organization metadata."""
        if ror_id in self._ror_cache:
            return self._ror_cache[ror_id]

        self._rate_limit("ror")
        try:
            resp = requests.get(
                f"https://api.ror.org/v2/organizations/{ror_id}",
                timeout=10,
            )
            self._last_call["ror"] = time.time()

            if resp.status_code == 429:
                self._exhausted.add("ror")
                return None
            if resp.status_code != 200:
                self._ror_cache[ror_id] = None
                return None

            data = resp.json()
            # Extract English name (preferred) or first available
            names = data.get("names", [])
            name = ""
            for n in names:
                if "ror_display" in n.get("types", []):
                    name = n.get("value", "")
                    break
            if not name and names:
                name = names[0].get("value", "")

            country = ""
            locations = data.get("locations", [])
            if locations:
                country = locations[0].get("geonames_details", {}).get(
                    "country_name", ""
                )

            result = {"name": name, "country": country}
            self._ror_cache[ror_id] = result
            return result

        except Exception:
            return None

    # ------------------------------------------------------------------
    # NCBI Taxonomy organism validation
    # ------------------------------------------------------------------

    def _validate_organisms(self, organisms: List[str]) -> List[str]:
        """Validate organism names against NCBI Taxonomy."""
        if "ncbi" in self._exhausted:
            return organisms

        validated = []
        for org_name in organisms:
            tax_data = self._query_ncbi_taxonomy(org_name)
            if tax_data is not None:
                # Use NCBI's canonical name
                canonical = tax_data.get("scientific_name", org_name)
                validated.append(canonical)
            else:
                # Keep the original — might be a common name we can't resolve
                validated.append(org_name)

        return validated

    def _query_ncbi_taxonomy(self, name: str) -> Optional[Dict]:
        """Query NCBI Taxonomy for organism validation."""
        if name in self._taxon_cache:
            return self._taxon_cache[name]

        # Map common names to Latin for direct lookup
        COMMON_TO_LATIN = {
            "Mouse": "Mus musculus",
            "Rat": "Rattus norvegicus",
            "Zebrafish": "Danio rerio",
            "Fruit Fly": "Drosophila melanogaster",
            "Drosophila": "Drosophila melanogaster",
            "C. elegans": "Caenorhabditis elegans",
            "Human": "Homo sapiens",
            "Xenopus": "Xenopus laevis",
            "Chicken": "Gallus gallus",
            "Pig": "Sus scrofa",
            "Dog": "Canis lupus familiaris",
            "Cat": "Felis catus",
            "Rabbit": "Oryctolagus cuniculus",
            "Sheep": "Ovis aries",
            "Cow": "Bos taurus",
            "Horse": "Equus caballus",
            "Guinea Pig": "Cavia porcellus",
            "Hamster": "Mesocricetus auratus",
            "Yeast": "Saccharomyces cerevisiae",
            "Arabidopsis": "Arabidopsis thaliana",
            "Rice": "Oryza sativa",
            "Maize": "Zea mays",
            "Tobacco": "Nicotiana tabacum",
        }

        # Use Latin name for NCBI lookup
        query_name = COMMON_TO_LATIN.get(name, name)

        self._rate_limit("ncbi")
        try:
            # Use NCBI ESearch to find taxon ID
            resp = requests.get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                params={
                    "db": "taxonomy",
                    "term": query_name,
                    "retmode": "json",
                },
                timeout=10,
            )
            self._last_call["ncbi"] = time.time()

            if resp.status_code == 429:
                self._exhausted.add("ncbi")
                return None
            if resp.status_code != 200:
                return None

            data = resp.json()
            id_list = data.get("esearchresult", {}).get("idlist", [])
            if not id_list:
                self._taxon_cache[name] = None
                return None

            tax_id = id_list[0]

            # Fetch taxonomy details
            self._rate_limit("ncbi")
            resp2 = requests.get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
                params={
                    "db": "taxonomy",
                    "id": tax_id,
                    "retmode": "json",
                },
                timeout=10,
            )
            self._last_call["ncbi"] = time.time()

            if resp2.status_code != 200:
                return None

            data2 = resp2.json()
            result_data = data2.get("result", {}).get(str(tax_id), {})
            if result_data:
                result = {
                    "tax_id": tax_id,
                    "scientific_name": result_data.get("scientificname", ""),
                    "common_name": result_data.get("commonname", ""),
                    "rank": result_data.get("rank", ""),
                }
                self._taxon_cache[name] = result
                return result

            self._taxon_cache[name] = None
            return None

        except Exception:
            return None

    # ------------------------------------------------------------------
    # PubTator supplemental extraction (for papers with PMIDs)
    # ------------------------------------------------------------------

    def extract_pubtator_entities(self, pmid: str) -> Dict[str, List[str]]:
        """Fetch pre-computed annotations from PubTator 3.0 for a PMID.

        Returns dict with keys: chemicals, species, genes, diseases, mutations.
        These can supplement regex-based extraction.
        """
        if "pubtator" in self._exhausted or not pmid:
            return {}

        self._rate_limit("pubtator")
        try:
            resp = requests.get(
                "https://www.ncbi.nlm.nih.gov/research/pubtator3-api/"
                "publications/export/biocjson",
                params={"pmids": str(pmid)},
                timeout=15,
            )
            self._last_call["pubtator"] = time.time()

            if resp.status_code == 429:
                self._exhausted.add("pubtator")
                return {}
            if resp.status_code != 200:
                return {}

            data = resp.json()
            entities: Dict[str, Set[str]] = {
                "chemicals": set(),
                "species": set(),
                "genes": set(),
                "diseases": set(),
                "mutations": set(),
                "cell_lines": set(),
            }

            passages = data.get("passages", [])
            for passage in passages:
                for ann in passage.get("annotations", []):
                    entity_type = ann.get("infons", {}).get("type", "").lower()
                    text = ann.get("text", "")
                    if not text:
                        continue

                    if entity_type == "chemical":
                        entities["chemicals"].add(text)
                    elif entity_type == "species":
                        entities["species"].add(text)
                    elif entity_type == "gene":
                        entities["genes"].add(text)
                    elif entity_type == "disease":
                        entities["diseases"].add(text)
                    elif entity_type == "mutation":
                        entities["mutations"].add(text)
                    elif entity_type == "cellline":
                        entities["cell_lines"].add(text)

            return {k: sorted(v) for k, v in entities.items() if v}

        except Exception:
            return {}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _rate_limit(self, api_name: str) -> None:
        """Sleep if needed to respect per-API rate limits."""
        last = self._last_call.get(api_name, 0.0)
        delay = self._delays.get(api_name, 0.3)
        elapsed = time.time() - last
        if elapsed < delay:
            time.sleep(delay - elapsed)
