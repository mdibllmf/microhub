"""
PubTator 3.0 supplemental extraction agent.

Uses NCBI's PubTator API to retrieve pre-computed NER annotations
for papers that have PMIDs.  PubTator covers ~36M PubMed abstracts
and ~6M PMC full-text articles with annotations for:
  - Species (organism names → NCBI TaxIDs)
  - Chemicals (fluorophores, dyes, reagents → MeSH/CHEBI IDs)
  - Cell lines (→ Cellosaurus IDs)
  - Genes, Diseases, Mutations

This agent supplements the regex-based agents — it finds entities
they may have missed, and provides database IDs for normalization.

Usage:
    agent = PubTatorAgent()
    extractions = agent.analyze_pmid("29355051")
"""

import logging
import time
from typing import Dict, List, Optional, Set

from .base_agent import BaseAgent, Extraction

logger = logging.getLogger(__name__)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# Maps PubTator entity types to our pipeline labels
_PUBTATOR_TYPE_MAP = {
    "Species": "ORGANISM",
    "Chemical": "CHEMICAL",
    "CellLine": "CELL_LINE",
    "Gene": "GENE",
    "Disease": "DISEASE",
    "Mutation": "MUTATION",
}

# Known fluorophore chemicals that PubTator might tag as "Chemical"
# — we re-label these as FLUOROPHORE for the pipeline
_FLUOROPHORE_CHEMICALS = {
    "gfp", "egfp", "eyfp", "ecfp", "mcherry", "tdtomato", "mtagbfp",
    "dapi", "hoechst", "propidium iodide", "calcein",
    "alexa fluor", "cy3", "cy5", "cy7", "atto",
    "fluo-4", "fura-2", "indo-1",
    "rhodamine", "fluorescein", "fitc", "tritc",
    "bodipy", "texas red", "oregon green",
}

# Map PubTator organism names (which may be common names) to scientific names
_ORGANISM_TO_SCIENTIFIC = {
    "mouse": "Mus musculus",
    "mice": "Mus musculus",
    "murine": "Mus musculus",
    "human": "Homo sapiens",
    "humans": "Homo sapiens",
    "patient": "Homo sapiens",
    "patients": "Homo sapiens",
    "rat": "Rattus norvegicus",
    "rats": "Rattus norvegicus",
    "zebrafish": "Danio rerio",
    "fruit fly": "Drosophila melanogaster",
    "fruit flies": "Drosophila melanogaster",
    "nematode": "Caenorhabditis elegans",
    "yeast": "Saccharomyces cerevisiae",
    "chicken": "Gallus gallus",
    "pig": "Sus scrofa",
    "dog": "Canis lupus familiaris",
    "rabbit": "Oryctolagus cuniculus",
    "monkey": "Macaca mulatta",
    "macaque": "Macaca mulatta",
    "frog": "Xenopus laevis",
    "maize": "Zea mays",
    "corn": "Zea mays",
    "rice": "Oryza sativa",
    "tobacco": "Nicotiana tabacum",
    # Already-scientific names that need standardization
    "drosophila": "Drosophila melanogaster",
    "xenopus": "Xenopus laevis",
    "arabidopsis": "Arabidopsis thaliana",
    "e. coli": "Escherichia coli",
    "c. elegans": "Caenorhabditis elegans",
}


class PubTatorAgent(BaseAgent):
    """Supplemental extraction via PubTator 3.0 API.

    Unlike other agents, this one doesn't operate on raw text.
    It uses the paper's PMID to fetch pre-computed annotations.

    Supports local-first lookup via PubTator entity summary files
    (downloaded by download_lookup_tables.sh).
    """

    name = "pubtator"

    def __init__(self, local_path: str = None):
        self._last_call = 0.0
        self._delay = 0.35  # PubTator rate limit: ~3 req/sec
        self._exhausted = False
        self._cache: Dict[str, List[Extraction]] = {}
        self._local_annotations: Dict[str, List[Dict]] = {}
        self._local_loaded = False

        if local_path:
            self._load_local(local_path)

    def _load_local(self, path: str):
        """Load PubTator entity summary files into a PMID-indexed lookup.

        The entity summary format (tab-separated, gzipped):
            PMID  Type  ConceptID  Mentions  Resource

        Only loads Species, CellLine, and Chemical types to limit memory.
        """
        import gzip
        import glob
        import os

        if not os.path.isdir(path):
            logger.warning("PubTator directory not found: %s", path)
            return

        entity_types_to_load = {"Species", "CellLine", "Chemical"}
        gz_files = glob.glob(os.path.join(path, "entity2pubtator3_*.gz"))

        if not gz_files:
            logger.warning("No PubTator entity files found in %s", path)
            return

        count = 0
        for gz_path in gz_files:
            try:
                with gzip.open(gz_path, "rt", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("#") or not line.strip():
                            continue
                        parts = line.strip().split("\t")
                        if len(parts) < 4:
                            continue

                        pmid = parts[0]
                        entity_type = parts[1]
                        concept_id = parts[2]
                        mentions = parts[3]

                        if entity_type not in entity_types_to_load:
                            continue

                        if pmid not in self._local_annotations:
                            self._local_annotations[pmid] = []

                        self._local_annotations[pmid].append({
                            "type": entity_type,
                            "concept_id": concept_id,
                            "mentions": mentions.split("|"),
                        })
                        count += 1
            except Exception as exc:
                logger.warning("Failed to parse %s: %s", gz_path, exc)

        if count > 0:
            self._local_loaded = True
            logger.info(
                "PubTator local loaded: %d annotations for %d PMIDs",
                count, len(self._local_annotations),
            )

    def _parse_local_annotations(self, pmid: str) -> List[Extraction]:
        """Convert local PubTator annotations to pipeline Extractions."""
        extractions: List[Extraction] = []
        seen: Set[str] = set()

        for ann in self._local_annotations.get(pmid, []):
            label = _PUBTATOR_TYPE_MAP.get(ann["type"])
            if not label:
                continue

            for mention in ann["mentions"]:
                mention = mention.strip()
                if not mention:
                    continue

                # Re-classify known fluorophores
                effective_label = label
                if effective_label == "CHEMICAL" and mention.lower() in _FLUOROPHORE_CHEMICALS:
                    effective_label = "FLUOROPHORE"

                # Normalize organism names
                canonical = mention
                if effective_label == "ORGANISM":
                    canonical = _ORGANISM_TO_SCIENTIFIC.get(mention.lower(), mention)
                    if canonical == mention and " " in mention:
                        parts = mention.split()
                        canonical = parts[0].capitalize() + " " + " ".join(
                            p.lower() for p in parts[1:]
                        )

                dedup_key = f"{effective_label}:{canonical.lower()}"
                if dedup_key in seen:
                    continue
                seen.add(dedup_key)

                extractions.append(Extraction(
                    text=mention,
                    label=effective_label,
                    start=0,
                    end=len(mention),
                    confidence=0.85,
                    source_agent=self.name,
                    section="abstract",
                    metadata={
                        "canonical": canonical,
                        "database_id": ann.get("concept_id", ""),
                        "source": "pubtator3_local",
                    },
                ))

        return extractions

    def analyze(self, text: str, section: str = None) -> List[Extraction]:
        """Not used directly — use analyze_pmid() instead."""
        return []

    def analyze_pmid(self, pmid: str) -> List[Extraction]:
        """Fetch PubTator annotations for a PMID.

        Returns Extractions with normalized database IDs in metadata.
        Checks local entity files first, falls back to API.
        """
        if not pmid:
            return []

        pmid = str(pmid).strip()
        if pmid in self._cache:
            return self._cache[pmid]

        # LOCAL FIRST
        if self._local_loaded and pmid in self._local_annotations:
            extractions = self._parse_local_annotations(pmid)
            self._cache[pmid] = extractions
            return extractions

        # FALLBACK: original API call
        if not HAS_REQUESTS or self._exhausted:
            return []

        data = self._fetch_pubtator(pmid)
        if data is None:
            return []

        extractions = self._parse_annotations(data)
        self._cache[pmid] = extractions
        return extractions

    def analyze_pmids_batch(self, pmids: List[str]) -> Dict[str, List[Extraction]]:
        """Batch fetch PubTator annotations for multiple PMIDs.

        PubTator accepts comma-separated PMIDs (up to ~100 per request).
        """
        if not HAS_REQUESTS or self._exhausted:
            return {}

        results: Dict[str, List[Extraction]] = {}

        # Check cache first
        uncached = []
        for pmid in pmids:
            pmid = str(pmid).strip()
            if not pmid:
                continue
            if pmid in self._cache:
                results[pmid] = self._cache[pmid]
            else:
                uncached.append(pmid)

        if not uncached:
            return results

        # Batch in groups of 50 (conservative limit)
        BATCH_SIZE = 50
        for i in range(0, len(uncached), BATCH_SIZE):
            batch = uncached[i:i + BATCH_SIZE]
            batch_data = self._fetch_pubtator_batch(batch)
            if batch_data is None:
                break  # Rate limited or error

            for pmid, annotations in batch_data.items():
                exts = self._parse_annotations(annotations)
                self._cache[pmid] = exts
                results[pmid] = exts

        return results

    # ------------------------------------------------------------------
    # API calls
    # ------------------------------------------------------------------

    def _fetch_pubtator(self, pmid: str) -> Optional[Dict]:
        """Fetch PubTator annotations for a single PMID."""
        elapsed = time.time() - self._last_call
        if elapsed < self._delay:
            time.sleep(self._delay - elapsed)

        try:
            resp = requests.get(
                "https://www.ncbi.nlm.nih.gov/research/pubtator3-api/"
                "publications/export/biocjson",
                params={"pmids": pmid},
                timeout=15,
            )
            self._last_call = time.time()

            if resp.status_code == 429:
                logger.warning("PubTator rate limited — stopping for this run")
                self._exhausted = True
                return None
            if resp.status_code != 200:
                return None

            return resp.json()

        except Exception as exc:
            logger.debug("PubTator error for %s: %s", pmid, exc)
            return None

    def _fetch_pubtator_batch(self, pmids: List[str]) -> Optional[Dict[str, Dict]]:
        """Fetch PubTator annotations for multiple PMIDs."""
        elapsed = time.time() - self._last_call
        if elapsed < self._delay:
            time.sleep(self._delay - elapsed)

        try:
            pmid_str = ",".join(pmids)
            resp = requests.get(
                "https://www.ncbi.nlm.nih.gov/research/pubtator3-api/"
                "publications/export/biocjson",
                params={"pmids": pmid_str},
                timeout=30,
            )
            self._last_call = time.time()

            if resp.status_code == 429:
                logger.warning("PubTator rate limited — stopping for this run")
                self._exhausted = True
                return None
            if resp.status_code != 200:
                return None

            # PubTator batch returns newline-delimited JSON
            text = resp.text.strip()
            results: Dict[str, Dict] = {}

            # Try parsing as single JSON first (single PMID)
            import json
            try:
                data = json.loads(text)
                if isinstance(data, dict) and "passages" in data:
                    pmid = data.get("pmid", pmids[0] if pmids else "")
                    results[str(pmid)] = data
                    return results
            except json.JSONDecodeError:
                pass

            # Try line-by-line (batch response)
            for line in text.split("\n"):
                line = line.strip()
                if not line:
                    continue
                try:
                    doc = json.loads(line)
                    pmid = str(doc.get("pmid", ""))
                    if pmid:
                        results[pmid] = doc
                except json.JSONDecodeError:
                    continue

            return results if results else None

        except Exception as exc:
            logger.debug("PubTator batch error: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Parse annotations
    # ------------------------------------------------------------------

    def _parse_annotations(self, data: Dict) -> List[Extraction]:
        """Parse PubTator BioC JSON into Extraction objects."""
        extractions: List[Extraction] = []
        seen: Set[str] = set()

        passages = data.get("passages", [])
        for passage in passages:
            # Determine section from passage type
            p_type = passage.get("infons", {}).get("type", "").lower()
            section = "abstract"
            if "title" in p_type:
                section = "title"
            elif "method" in p_type:
                section = "methods"
            elif "result" in p_type:
                section = "results"

            p_offset = passage.get("offset", 0)

            for ann in passage.get("annotations", []):
                infons = ann.get("infons", {})
                entity_type = infons.get("type", "")
                text = ann.get("text", "")
                if not text or not entity_type:
                    continue

                # Map PubTator type to our label
                label = _PUBTATOR_TYPE_MAP.get(entity_type)
                if not label:
                    continue

                # Re-classify known fluorophores
                if label == "CHEMICAL" and text.lower() in _FLUOROPHORE_CHEMICALS:
                    label = "FLUOROPHORE"

                # Normalize organism names to scientific names
                canonical = text
                if label == "ORGANISM":
                    canonical = _ORGANISM_TO_SCIENTIFIC.get(text.lower(), text)
                    # If PubTator returned a scientific name, keep it as-is
                    # but capitalize genus properly
                    if canonical == text and " " in text:
                        # Looks like a binomial — capitalize properly
                        parts = text.split()
                        canonical = parts[0].capitalize() + " " + " ".join(p.lower() for p in parts[1:])

                # Get database ID
                db_id = infons.get("identifier", "")

                # Deduplicate (same canonical + label)
                dedup_key = f"{label}:{canonical.lower()}"
                if dedup_key in seen:
                    continue
                seen.add(dedup_key)

                # Location info
                locations = ann.get("locations", [{}])
                start = locations[0].get("offset", p_offset) if locations else p_offset
                length = locations[0].get("length", len(text)) if locations else len(text)

                extractions.append(Extraction(
                    text=text,
                    label=label,
                    start=start,
                    end=start + length,
                    confidence=0.85,  # PubTator is well-validated
                    source_agent=self.name,
                    section=section,
                    metadata={
                        "canonical": canonical,
                        "database_id": db_id,
                        "source": "pubtator3",
                    },
                ))

        return extractions
