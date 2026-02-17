"""
MicroHub Multi-Agent NLP Pipeline for Microscopy Paper Metadata Extraction.

Architecture:
  - parsing/    : GROBID PDF parsing + PubMed/PMC section extraction
  - agents/     : Specialized entity extraction agents
  - validation/ : FPbase, NCBI Taxonomy, SciCrunch, tag dictionary validation
  - export/     : WordPress-compatible JSON export (identical output format)
"""

__version__ = "6.0.0"
