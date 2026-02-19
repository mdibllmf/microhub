"""Tests for the Europe PMC JATS XML full-text fetcher."""

import xml.etree.ElementTree as ET

import pytest

from pipeline.parsing.europepmc_fetcher import (
    EuropePMCFetcher,
    _classify_heading,
    _element_text,
)


# ======================================================================
# JATS XML parsing tests
# ======================================================================

SAMPLE_JATS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<article>
  <front>
    <article-meta>
      <title-group>
        <article-title>Super-resolution imaging of live cells</article-title>
      </title-group>
      <abstract>
        <p>We developed a novel STED microscopy approach for live cell imaging.</p>
      </abstract>
    </article-meta>
  </front>
  <body>
    <sec sec-type="intro">
      <title>Introduction</title>
      <p>Super-resolution microscopy has revolutionized biological imaging.</p>
    </sec>
    <sec sec-type="methods">
      <title>Materials and Methods</title>
      <p>We used a Leica SP8 STED microscope with a 100x objective.</p>
      <p>Samples were fixed with 4% PFA and stained with DAPI.</p>
    </sec>
    <sec sec-type="results">
      <title>Results</title>
      <p>STED imaging revealed nanoscale structures in live HeLa cells.</p>
    </sec>
    <sec>
      <title>Discussion</title>
      <p>Unlike confocal microscopy, STED provides resolution below 50nm.</p>
    </sec>
    <sec sec-type="data-availability">
      <title>Data Availability</title>
      <p>Raw data deposited at EMPIAR-12345 and Zenodo (doi:10.5281/zenodo.123).</p>
    </sec>
  </body>
  <back>
    <fig id="fig1">
      <label>Figure 1</label>
      <caption><p>STED image of actin filaments in HeLa cells.</p></caption>
    </fig>
    <table-wrap id="table1">
      <label>Table 1</label>
      <caption><p>Imaging parameters used in this study.</p></caption>
    </table-wrap>
  </back>
</article>
"""


class TestJATSParsing:
    """Test JATS XML parsing into structured sections."""

    def test_parse_jats_xml_returns_sections(self):
        sections = EuropePMCFetcher.parse_jats_xml(SAMPLE_JATS_XML)
        assert len(sections) > 0

    def test_parse_jats_xml_abstract(self):
        sections = EuropePMCFetcher.parse_jats_xml(SAMPLE_JATS_XML)
        abstracts = [s for s in sections if s["type"] == "abstract"]
        assert len(abstracts) == 1
        assert "STED microscopy" in abstracts[0]["text"]

    def test_parse_jats_xml_methods(self):
        sections = EuropePMCFetcher.parse_jats_xml(SAMPLE_JATS_XML)
        methods = [s for s in sections if s["type"] == "methods"]
        assert len(methods) == 1
        assert "Leica SP8" in methods[0]["text"]
        assert "DAPI" in methods[0]["text"]

    def test_parse_jats_xml_results(self):
        sections = EuropePMCFetcher.parse_jats_xml(SAMPLE_JATS_XML)
        results = [s for s in sections if s["type"] == "results"]
        assert len(results) == 1
        assert "HeLa cells" in results[0]["text"]

    def test_parse_jats_xml_discussion(self):
        sections = EuropePMCFetcher.parse_jats_xml(SAMPLE_JATS_XML)
        discussions = [s for s in sections if s["type"] == "discussion"]
        assert len(discussions) == 1
        assert "confocal" in discussions[0]["text"]

    def test_parse_jats_xml_data_availability(self):
        sections = EuropePMCFetcher.parse_jats_xml(SAMPLE_JATS_XML)
        data_avail = [s for s in sections if s["type"] == "data_availability"]
        assert len(data_avail) == 1
        assert "EMPIAR-12345" in data_avail[0]["text"]

    def test_parse_jats_xml_figure_captions(self):
        sections = EuropePMCFetcher.parse_jats_xml(SAMPLE_JATS_XML)
        figures = [s for s in sections if s["type"] == "figures"]
        assert any("actin filaments" in f["text"] for f in figures)

    def test_parse_jats_xml_table_captions(self):
        sections = EuropePMCFetcher.parse_jats_xml(SAMPLE_JATS_XML)
        figures = [s for s in sections if s["type"] == "figures"]
        assert any("Imaging parameters" in f["text"] for f in figures)

    def test_parse_jats_xml_invalid_xml(self):
        sections = EuropePMCFetcher.parse_jats_xml("not valid xml")
        assert sections == []


class TestHeadingClassification:
    """Test section heading classification heuristics."""

    def test_methods_headings(self):
        assert _classify_heading("Materials and Methods") == "methods"
        assert _classify_heading("Experimental Procedures") == "methods"
        assert _classify_heading("Microscopy methods") == "methods"
        assert _classify_heading("Imaging Protocol") == "methods"

    def test_results_headings(self):
        assert _classify_heading("Results") == "results"
        assert _classify_heading("Key Findings") == "results"

    def test_introduction_headings(self):
        assert _classify_heading("Introduction") == "introduction"
        assert _classify_heading("Background") == "introduction"

    def test_discussion_headings(self):
        assert _classify_heading("Discussion") == "discussion"
        assert _classify_heading("Conclusions") == "discussion"

    def test_data_availability_headings(self):
        assert _classify_heading("Data Availability") == "data_availability"
        assert _classify_heading("Code Availability") == "data_availability"
        assert _classify_heading("Accession Codes") == "data_availability"

    def test_unknown_heading(self):
        assert _classify_heading("Acknowledgements") == "other"
        assert _classify_heading("Funding") == "other"


class TestEuropePMCFetcher:
    """Test fetcher instance methods (non-network)."""

    def test_normalize_pmcid(self):
        fetcher = EuropePMCFetcher()
        assert fetcher._normalize_pmcid("PMC1234567") == "PMC1234567"
        assert fetcher._normalize_pmcid("1234567") == "PMC1234567"
        assert fetcher._normalize_pmcid("pmc1234567") == "PMC1234567"
        assert fetcher._normalize_pmcid("") is None
        assert fetcher._normalize_pmcid(None) is None
