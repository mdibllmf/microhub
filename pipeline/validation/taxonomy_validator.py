"""
Taxonomy validation using NCBI Taxonomy and PubTator APIs.

Validates organism names against NCBI Taxonomy IDs and enriches
extractions with taxonomic identifiers.

Supports local-first validation via NCBI names.dmp (downloaded by
download_lookup_tables.sh).  Falls back to the live NCBI API if
local lookup misses or is not loaded.
"""

import logging
import os
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# Common organisms pre-mapped to NCBI Taxonomy IDs
NCBI_TAXIDS: Dict[str, int] = {
    "Human": 9606,
    "Mouse": 10090,
    "Rat": 10116,
    "Zebrafish": 7955,
    "Drosophila": 7227,
    "C. elegans": 6239,
    "Xenopus": 8355,
    "Arabidopsis": 3702,
    "Yeast": 4932,
    "E. coli": 562,
    "Chicken": 9031,
    "Pig": 9823,
    "Dog": 9615,
    "Monkey": 9544,
    "Rabbit": 9986,
    "Maize": 4577,
    "Tobacco": 4097,
}

_PUBTATOR_API = "https://www.ncbi.nlm.nih.gov/research/pubtator3-api"


class TaxonomyValidator:
    """Validate organism names against NCBI Taxonomy."""

    def __init__(self, local_path: str = None):
        self._cache: Dict[str, Optional[int]] = {}
        self._local_names: Dict[str, int] = {}  # lowercase name → taxid
        self._local_loaded = False
        self._local_path = local_path  # deferred to first use

    def _ensure_local_loaded(self):
        """Lazy-load NCBI names.dmp on first use."""
        if not self._local_loaded and self._local_path:
            self._load_local(self._local_path)
            self._local_path = None  # prevent re-loading

    def _load_local(self, path: str):
        """Parse NCBI names.dmp for comprehensive name → TaxID mapping."""
        names_path = path
        if os.path.isdir(path):
            names_path = os.path.join(path, "names.dmp")

        if not os.path.exists(names_path):
            logger.warning("NCBI names.dmp not found at %s", names_path)
            return

        count = 0
        try:
            with open(names_path, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split("\t|\t")
                    if len(parts) >= 4:
                        try:
                            taxid = int(parts[0].strip())
                        except ValueError:
                            continue
                        name = parts[1].strip()
                        name_class = parts[3].rstrip("\t|").strip()

                        # Index scientific names, common names, and synonyms
                        if name_class in (
                            "scientific name", "common name",
                            "synonym", "equivalent name",
                            "genbank common name",
                        ):
                            name_lower = name.lower()
                            # Prefer scientific names over common names
                            if (name_lower not in self._local_names
                                    or name_class == "scientific name"):
                                self._local_names[name_lower] = taxid
                            count += 1
                            if count % 500000 == 0:
                                logger.info("  ... loaded %d taxonomy entries so far", count)

            self._local_loaded = True
            logger.info(
                "NCBI taxonomy loaded: %d name entries, %d unique names",
                count, len(self._local_names),
            )
        except Exception as exc:
            logger.warning("Failed to load NCBI taxonomy: %s", exc)

    def get_taxid(self, organism: str) -> Optional[int]:
        """Return NCBI Taxonomy ID for a canonical organism name."""
        # Check hardcoded map first (fastest)
        taxid = NCBI_TAXIDS.get(organism)
        if taxid is not None:
            return taxid

        # Check cache
        if organism in self._cache:
            return self._cache[organism]

        # LOCAL LOOKUP (lazy-load on first use)
        self._ensure_local_loaded()
        if self._local_loaded:
            taxid = self._local_names.get(organism.lower())
            if taxid is not None:
                self._cache[organism] = taxid
                return taxid

        # FALLBACK: original NCBI API
        taxid = self._query_ncbi(organism)
        self._cache[organism] = taxid
        return taxid

    def validate(self, organism: str) -> bool:
        """Check if organism is a valid taxonomic name."""
        return self.get_taxid(organism) is not None

    def annotate_with_pubtator(self, pmid: str) -> List[Dict]:
        """Get species annotations from PubTator for a given PMID."""
        if not HAS_REQUESTS:
            return []

        url = f"{_PUBTATOR_API}/publications/export/biocjson"
        try:
            resp = requests.get(url, params={"pmids": pmid}, timeout=15)
            if resp.status_code != 200:
                return []

            data = resp.json()
            species = []
            for passage in data.get("passages", []):
                for ann in passage.get("annotations", []):
                    if ann.get("infons", {}).get("type") == "Species":
                        species.append({
                            "text": ann.get("text"),
                            "ncbi_taxid": ann.get("infons", {}).get("identifier"),
                            "section": passage.get("infons", {}).get("type"),
                        })
            return species
        except Exception as exc:
            logger.debug("PubTator query failed for PMID %s: %s", pmid, exc)
            return []

    # ------------------------------------------------------------------
    def _query_ncbi(self, name: str) -> Optional[int]:
        """Query NCBI Taxonomy for a name."""
        if not HAS_REQUESTS:
            return None

        try:
            url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            resp = requests.get(
                url,
                params={
                    "db": "taxonomy",
                    "term": f'"{name}"[Scientific Name]',
                    "retmode": "json",
                },
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                ids = data.get("esearchresult", {}).get("idlist", [])
                if ids:
                    return int(ids[0])
        except Exception as exc:
            logger.debug("NCBI Taxonomy lookup failed for '%s': %s", name, exc)

        return None
