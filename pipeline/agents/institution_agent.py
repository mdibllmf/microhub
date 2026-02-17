"""
Institution extraction agent.

Extracts research institutions ONLY from author affiliation strings
(not from paper body text, which would cause false positives from
citation mentions).  Maps institutions to ROR IDs where known.
"""

import re
from typing import Dict, List, Optional

from .base_agent import BaseAgent, Extraction

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
}

# Patterns for extracting institution names from affiliation strings
_INSTITUTION_PATTERNS: List[tuple] = [
    # University of X
    (re.compile(r"\bUniversity\s+of\s+[\w\s]+(?=,|\.|;|\d)", re.I), None),
    # X University
    (re.compile(r"\b[\w]+\s+University\b", re.I), None),
    # X Institute / X Laboratory
    (re.compile(r"\b[\w\s]+(?:Institute|Laboratory|Lab)\s+(?:of|for)\s+[\w\s]+(?=,|\.|;)", re.I), None),
    # Hospital / Medical Center
    (re.compile(r"\b[\w\s]+(?:Hospital|Medical\s+Center|Medical\s+School)\b", re.I), None),
]


class InstitutionAgent(BaseAgent):
    """Extract institutions from author affiliations (NOT from paper body)."""

    name = "institution"

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
                extractions.append(Extraction(
                    text=name,
                    label="INSTITUTION",
                    start=m.start(), end=m.end(),
                    confidence=0.7,
                    source_agent=self.name,
                    section=section or "",
                    metadata={"canonical": name},
                ))

        return extractions
