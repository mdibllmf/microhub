"""
MicroHub Multi-Agent NLP Pipeline for Microscopy Paper Metadata Extraction.

Architecture:
  - parsing/    : Three-tier full-text acquisition (Europe PMC, Unpaywall+GROBID, abstract)
  - agents/     : 17 specialized entity extraction agents (incl. OpenAlex, DataCite)
  - validation/ : FPbase, NCBI Taxonomy, SciCrunch, ROR v2, tag dictionary validation
  - export/     : WordPress-compatible JSON export (identical output format)
  - role_classifier: Multi-stage over-tagging prevention (USED vs REFERENCED)
"""

__version__ = "6.1.0"
