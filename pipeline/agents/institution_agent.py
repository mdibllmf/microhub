"""
Institution extraction agent.

Extracts research institutions ONLY from author affiliation strings
(not from paper body text, which would cause false positives from
citation mentions).  Maps institutions to ROR IDs where known.
"""

import logging
import os
import re
import time
from typing import Dict, List, Optional

from .base_agent import BaseAgent, Extraction

logger = logging.getLogger(__name__)

try:
    import requests as _requests_lib
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

# ======================================================================
# Known institutions with ROR IDs
# ======================================================================

INSTITUTION_ROR_IDS: Dict[str, str] = {
    "Harvard University": "03vek6s52",
    "Harvard Medical School": "03vek6s52",
    "MIT": "042nb2s44",
    "Massachusetts Institute of Technology": "042nb2s44",
    "Stanford University": "00f54p054",
    "Yale University": "03v76x132",
    "University of Oxford": "052gg0110",
    "University of Cambridge": "013meh722",
    "EMBL": "03mstc592",
    "European Molecular Biology Laboratory": "03mstc592",
    "Max Planck Institute": "01hhn8329",
    "Max Planck": "01hhn8329",
    "NIH": "01cwqze88",
    "National Institutes of Health": "01cwqze88",
    "Janelia Research Campus": "013sk6x84",
    "Janelia Farm": "013sk6x84",
    "Howard Hughes Medical Institute": "006w34k90",
    "HHMI": "006w34k90",
    "Broad Institute": "05a0ya142",
    "Allen Institute": "03cpe7c52",
    "Salk Institute": "03xez1567",
    "Scripps Research": "02dxx6824",
    "Caltech": "05dxps055",
    "California Institute of Technology": "05dxps055",
    "UC Berkeley": "01an7q238",
    "University of California Berkeley": "01an7q238",
    "UCLA": "046rm7j60",
    "UCSF": "043mz5j54",
    "UC San Diego": "0168r3w48",
    "UCSD": "0168r3w48",
    "Johns Hopkins University": "00za53h95",
    "Columbia University": "00hj8s172",
    "University of Pennsylvania": "00b30xv10",
    "UPenn": "00b30xv10",
    "Princeton University": "00hx57361",
    "Duke University": "00py81415",
    "University of Chicago": "024mw5h28",
    "University of Michigan": "00jmfr291",
    "University of Wisconsin": "01y2jtd41",
    "Cornell University": "05bnh6r87",
    "University of Washington": "00cvxb145",
    "Washington University": "01yc7t268",
    "Rockefeller University": "0420db125",
    "Cold Spring Harbor Laboratory": "02qz8b764",
    "CSHL": "02qz8b764",
    "ETH Zurich": "05a28rw58",
    "University of Zurich": "02crff812",
    "Karolinska Institute": "056d84691",
    "MRC Laboratory of Molecular Biology": "00tw3jy02",
    "MRC LMB": "00tw3jy02",
    "Francis Crick Institute": "055x5mt09",
    "Pasteur Institute": "0495fxg12",
    "Institut Pasteur": "0495fxg12",
    "University of Tokyo": "057zh3y96",
    "Kyoto University": "02kpeqv85",
    "RIKEN": "01sjwvz98",
    "National University of Singapore": "01tgyzw49",
    "NUS": "01tgyzw49",
    "Peking University": "02v51f717",
    "Tsinghua University": "03cve4549",
    "Chinese Academy of Sciences": "034t30j35",
    "CAS": "034t30j35",
    "University of Toronto": "03dbr7087",
    "McGill University": "01pxwe438",
    "University of British Columbia": "03rmrcq20",
    "Imperial College London": "041kmwe10",
    "UCL": "02jx3x895",
    "University College London": "02jx3x895",
    "King's College London": "0220mzb33",
    "University of Edinburgh": "01nrxwf90",
    "University of Glasgow": "00vtgdb53",
    "Heidelberg University": "038t36y30",
    "LMU Munich": "05591te55",
    "Technical University of Munich": "02kkvpp62",
    "University of Gottingen": "01y9bpm73",
    "Charite": "001w7jn25",
    "Leiden University": "027bh9e22",
    "Utrecht University": "04pp8hn57",
    "Erasmus MC": "018906e22",
    "Weizmann Institute": "0316ej306",
    "Hebrew University": "03qxff017",
    "Monash University": "02bfwt286",
    "University of Melbourne": "01ej9dk98",
    "University of Queensland": "00rqy9422",
    # Additional US institutions
    "Northwestern University": "000e0be47",
    "New York University": "0190ak572",
    "NYU": "0190ak572",
    "University of Texas at Austin": "00hj54h04",
    "UT Austin": "00hj54h04",
    "UT Southwestern Medical Center": "00a4bsz29",
    "MD Anderson Cancer Center": "04twxam07",
    "Mayo Clinic": "02qp3tb03",
    "Whitehead Institute": "00x0k6167",
    "Stowers Institute": "00h0r6t62",
    "University of Virginia": "0153tk833",
    "University of Pittsburgh": "01an3r305",
    "University of Minnesota": "017zqws13",
    "University of North Carolina": "0130frc33",
    "Vanderbilt University": "02vm5rt34",
    "Baylor College of Medicine": "02pttbw34",
    # Additional UK institutions
    "University of Manchester": "027m9bs27",
    "Wellcome Sanger Institute": "05cy4wa09",
    "Sanger Institute": "05cy4wa09",
    "University of Bristol": "0524sp257",
    "University of Sheffield": "05krs5044",
    # Additional European institutions
    "EPFL": "02s376052",
    "Institut Curie": "04t0gwh46",
    "CNRS": "02feahw73",
    "INSERM": "02vjkv261",
    "University of Geneva": "01swzsf04",
    "University of Basel": "02s6k3f65",
    # Additional Asia-Pacific institutions
    "University of Sydney": "0384j8v12",
    "Australian National University": "019wvm592",
    "ANU": "019wvm592",
    "Osaka University": "035t8zc32",
    "Seoul National University": "04h9pn542",
    # Additional Canadian institutions
    "SickKids Research Institute": "04374qe70",
    "University of Alberta": "0160cpw27",
    "University of Ottawa": "03c4mmv16",
}

# Patterns for extracting institution names from affiliation strings
_INSTITUTION_PATTERNS: List[tuple] = [
    # University of X
    (re.compile(r"\bUniversity\s+of\s+[\w\s]+(?=,|\.|;|\d)", re.I), None),
    # X University
    (re.compile(r"\b[\w]+\s+University\b", re.I), None),
    # European university formats (Universität, Université, Universiteit)
    (re.compile(r"\bUniversit[äeéiay]\w*\s+[\w\s]+(?=,|\.|;|\d)", re.I), None),
    # X Institute / X Laboratory
    (re.compile(r"\b[\w\s]+(?:Institute|Laboratory|Lab)\s+(?:of|for)\s+[\w\s]+(?=,|\.|;)", re.I), None),
    # Hospital / Medical Center
    (re.compile(r"\b[\w\s]+(?:Hospital|Medical\s+Center|Medical\s+School)\b", re.I), None),
    # X College
    (re.compile(r"\b[\w]+\s+College\b(?!\s+of\s+(?:the|a)\b)", re.I), None),
    # National Laboratory / Research Center
    (re.compile(r"\b[\w\s]+National\s+Laborator\w*\b", re.I), None),
    (re.compile(r"\b[\w\s]+Research\s+Center\b", re.I), None),
    (re.compile(r"\b[\w\s]+Cancer\s+Center\b", re.I), None),
    (re.compile(r"\b[\w\s]+Children(?:'s)?\s+Hospital\b", re.I), None),
]

# Patterns to exclude from institution extraction (acknowledgment noise)
_ACKNOWLEDGMENT_EXCLUSIONS = re.compile(
    r"\b(?:funded?\s+by|grant|supported?\s+by|acknowledg|thank)\b",
    re.IGNORECASE,
)


class InstitutionAgent(BaseAgent):
    """Extract institutions from author affiliations (NOT from paper body).

    Supports local-first ROR lookup via a downloaded ROR data dump JSON
    file (downloaded by download_lookup_tables.sh).  Falls back to the
    live ROR API for institutions not in the local dump.
    """

    name = "institution"

    def __init__(self, ror_local_path: str = None):
        super().__init__()
        self._ror_local_index: Dict[str, str] = {}
        self._ror_local_names: Dict[str, str] = {}  # lowercase name -> official name
        self._ror_loaded = False
        if ror_local_path:
            self._load_ror(ror_local_path)

    def _load_ror(self, path: str):
        """Load ROR data dump JSON for local institution name -> ROR ID matching."""
        import glob
        import json
        json_path = path
        if os.path.isdir(path):
            candidates = glob.glob(os.path.join(path, "v*.json"))
            if not candidates:
                candidates = glob.glob(os.path.join(path, "*.json"))
            if not candidates:
                logger.warning("No ROR JSON found in %s", path)
                return
            json_path = candidates[0]

        if not os.path.exists(json_path):
            logger.warning("ROR dump not found at %s", json_path)
            return

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                orgs = json.load(f)

            for org in orgs:
                ror_id = org.get("id", "").replace("https://ror.org/", "")
                name = org.get("name", "")
                if not ror_id or not name:
                    continue
                self._ror_local_index[name.lower()] = ror_id
                self._ror_local_names[name.lower()] = name
                for name_obj in org.get("names", []):
                    alt = name_obj.get("value", "")
                    if alt:
                        alt_lower = alt.lower()
                        if alt_lower not in self._ror_local_index:
                            self._ror_local_index[alt_lower] = ror_id
                            self._ror_local_names[alt_lower] = name

            self._ror_loaded = True
            logger.info("InstitutionAgent ROR local: %d lookup keys",
                        len(self._ror_local_index))
        except Exception as exc:
            logger.warning("Failed to load ROR dump: %s", exc)

    def analyze(self, text: str, section: str = None) -> List[Extraction]:
        """Only runs on affiliation strings, not general paper text."""
        # This agent is designed to be called with affiliation text
        return self._extract_institutions(text, section)

    def analyze_affiliations(self, affiliations: List[str]) -> List[Extraction]:
        """Extract institutions from a list of affiliation strings."""
        results: List[Extraction] = []
        for aff in affiliations:
            results.extend(self._extract_institutions(aff, "affiliation"))
        return self._deduplicate(results)

    # ------------------------------------------------------------------
    def _extract_institutions(self, text: str,
                              section: str = None) -> List[Extraction]:
        extractions: List[Extraction] = []
        if not text:
            return extractions

        # 1. Match against known institutions with ROR IDs
        for inst_name, ror_id in INSTITUTION_ROR_IDS.items():
            pattern = re.compile(r"\b" + re.escape(inst_name) + r"\b", re.I)
            for m in pattern.finditer(text):
                extractions.append(Extraction(
                    text=m.group(0),
                    label="INSTITUTION",
                    start=m.start(), end=m.end(),
                    confidence=0.95,
                    source_agent=self.name,
                    section=section or "",
                    metadata={
                        "canonical": inst_name,
                        "ror_id": ror_id,
                        "ror_url": f"https://ror.org/{ror_id}",
                    },
                ))

        # 2. Pattern-based extraction for institutions not in the dictionary
        #    Skip text that looks like acknowledgment/funding context
        if _ACKNOWLEDGMENT_EXCLUSIONS.search(text):
            return extractions

        for pattern, _ in _INSTITUTION_PATTERNS:
            for m in pattern.finditer(text):
                name = m.group(0).strip().rstrip(",.")
                # Skip if already found by known institutions
                if any(e.metadata.get("canonical", "").lower() == name.lower()
                       for e in extractions):
                    continue
                # Skip very short matches (likely false positives)
                if len(name) < 5:
                    continue

                metadata = {"canonical": name}
                conf = 0.7

                # LOCAL FIRST: check ROR dump for this institution
                if self._ror_loaded:
                    local_ror_id = self._ror_local_index.get(name.lower())
                    if local_ror_id:
                        official_name = self._ror_local_names.get(
                            name.lower(), name)
                        metadata["ror_id"] = local_ror_id
                        metadata["ror_url"] = f"https://ror.org/{local_ror_id}"
                        metadata["canonical"] = official_name
                        conf = 0.90
                    else:
                        # FALLBACK: ROR v2 API lookup
                        ror_result = self.resolve_ror_via_api(name)
                        if ror_result:
                            metadata["ror_id"] = ror_result["ror_id"]
                            metadata["ror_url"] = f"https://ror.org/{ror_result['ror_id']}"
                            metadata["canonical"] = ror_result["name"]
                            conf = 0.85
                else:
                    # No local dump — try ROR v2 API lookup
                    ror_result = self.resolve_ror_via_api(name)
                    if ror_result:
                        metadata["ror_id"] = ror_result["ror_id"]
                        metadata["ror_url"] = f"https://ror.org/{ror_result['ror_id']}"
                        metadata["canonical"] = ror_result["name"]
                        conf = 0.85

                extractions.append(Extraction(
                    text=name,
                    label="INSTITUTION",
                    start=m.start(), end=m.end(),
                    confidence=conf,
                    source_agent=self.name,
                    section=section or "",
                    metadata=metadata,
                ))

        return extractions

    # ------------------------------------------------------------------
    # ROR v2 API fallback for institutions not in the hardcoded map
    # ------------------------------------------------------------------

    _ror_api_cache: Dict[str, Optional[Dict]] = {}
    _last_ror_call: float = 0.0
    _ROR_DELAY: float = 0.15  # 2000 req/5min = ~6.6/sec

    def resolve_ror_via_api(self, institution_name: str) -> Optional[Dict]:
        """Look up ROR ID for an institution name via ROR v2 API.

        Only called for institutions NOT in the hardcoded INSTITUTION_ROR_IDS.
        Results are cached for the lifetime of this agent instance.
        """
        if not _HAS_REQUESTS:
            return None

        cache_key = institution_name.lower().strip()
        if cache_key in self._ror_api_cache:
            return self._ror_api_cache[cache_key]

        elapsed = time.time() - self._last_ror_call
        if elapsed < self._ROR_DELAY:
            time.sleep(self._ROR_DELAY - elapsed)

        try:
            resp = _requests_lib.get(
                "https://api.ror.org/v2/organizations",
                params={"query": institution_name},
                timeout=10,
            )
            InstitutionAgent._last_ror_call = time.time()

            if resp.status_code != 200:
                self._ror_api_cache[cache_key] = None
                return None

            data = resp.json()
            items = data.get("items", [])
            if not items:
                self._ror_api_cache[cache_key] = None
                return None

            # Take the top result — ROR's search is relevance-ranked
            top = items[0]
            ror_id_full = top.get("id", "")  # e.g. "https://ror.org/0xxxxxxxx"
            ror_id = ror_id_full.replace("https://ror.org/", "").strip()
            official_name = ""
            for name_entry in top.get("names", []):
                if "ror_display" in name_entry.get("types", []):
                    official_name = name_entry.get("value", "")
                    break
            if not official_name:
                names = top.get("names", [])
                official_name = names[0].get("value", institution_name) if names else institution_name

            result = {"ror_id": ror_id, "name": official_name}
            self._ror_api_cache[cache_key] = result
            return result

        except Exception as exc:
            logger.debug("ROR API error for '%s': %s", institution_name, exc)
            self._ror_api_cache[cache_key] = None
            return None
