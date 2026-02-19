"""Integration tests for the enrichment pipeline additions."""

import pytest

from pipeline.enrichment import Enricher


class TestEnricherInitialization:
    """Test that the Enricher properly initializes with new agents."""

    def test_enricher_creates(self):
        enricher = Enricher()
        assert enricher is not None

    def test_openalex_agent_lazy_init(self):
        enricher = Enricher()
        # Should not be initialized yet
        assert enricher._openalex_agent is None
        # Accessing the property should initialize it
        agent = enricher.openalex_agent
        assert agent is not None
        assert enricher._openalex_agent is not None

    def test_datacite_agent_lazy_init(self):
        enricher = Enricher()
        assert enricher._datacite_agent is None
        agent = enricher.datacite_agent
        assert agent is not None
        assert enricher._datacite_agent is not None

    def test_ror_client_lazy_init(self):
        enricher = Enricher()
        assert enricher._ror_client is None
        client = enricher.ror_client
        assert client is not None
        assert enricher._ror_client is not None


class TestApplyOpenAlexData:
    """Test OpenAlex data application to paper dicts."""

    def test_apply_citations(self):
        paper = {"doi": "10.1038/test", "citation_count": 10}
        oa_data = {"cited_by_count": 42, "fwci": 3.5}
        Enricher._apply_openalex_data(paper, oa_data)
        assert paper["citation_count"] == 42
        assert paper["citation_source"] == "openalex"
        assert paper["fwci"] == 3.5

    def test_apply_citations_lower_count_not_overwritten(self):
        paper = {"doi": "10.1038/test", "citation_count": 50}
        oa_data = {"cited_by_count": 42}
        Enricher._apply_openalex_data(paper, oa_data)
        assert paper["citation_count"] == 50  # kept higher value

    def test_apply_oa_status(self):
        paper = {"doi": "10.1038/test"}
        oa_data = {
            "is_oa": True,
            "oa_status": "gold",
            "oa_url": "https://example.com/paper",
        }
        Enricher._apply_openalex_data(paper, oa_data)
        assert paper["oa_status"] == "gold"
        assert paper["oa_url"] == "https://example.com/paper"

    def test_apply_institutions_with_ror(self):
        paper = {"doi": "10.1038/test"}
        oa_data = {
            "institutions": [
                {
                    "name": "MIT",
                    "ror_id": "042nb2s44",
                    "country_code": "US",
                }
            ],
        }
        Enricher._apply_openalex_data(paper, oa_data)
        assert paper["openalex_institutions"] == oa_data["institutions"]
        assert len(paper["rors"]) == 1
        assert paper["rors"][0]["id"] == "042nb2s44"
        assert paper["rors"][0]["source"] == "openalex"

    def test_apply_topics(self):
        paper = {"doi": "10.1038/test"}
        oa_data = {
            "topics": [
                {
                    "name": "Microscopy",
                    "field": "Physics",
                    "subfield": "Optics",
                    "domain": "Physical Sciences",
                }
            ],
        }
        Enricher._apply_openalex_data(paper, oa_data)
        assert paper["openalex_topics"] == oa_data["topics"]
        assert paper["fields_of_study"] == ["Physics"]

    def test_apply_pmcid(self):
        paper = {"doi": "10.1038/test"}
        oa_data = {"pmcid": "PMC1234567"}
        Enricher._apply_openalex_data(paper, oa_data)
        assert paper["pmc_id"] == "PMC1234567"


class TestEnrichDataCite:
    """Test DataCite enrichment."""

    def test_enrich_datacite_no_doi(self):
        enricher = Enricher()
        paper = {"title": "Test paper"}
        enricher._enrich_datacite(paper)
        # No error should occur
        assert "repositories" not in paper or paper.get("repositories") is None

    def test_enrich_datacite_with_data_availability(self):
        enricher = Enricher()
        paper = {
            "title": "Test paper",
            "data_availability": "Data deposited at EMPIAR-12345 and GSE654321.",
        }
        enricher._enrich_datacite(paper)
        repos = paper.get("repositories", [])
        assert len(repos) >= 2
        names = [r["name"] for r in repos]
        assert "EMPIAR" in names
        assert "GEO" in names


class TestEnrichROR:
    """Test ROR affiliation enrichment (non-network)."""

    def test_enrich_ror_no_affiliations(self):
        enricher = Enricher()
        paper = {"title": "Test paper"}
        enricher._enrich_ror_affiliations(paper)
        # Should not fail

    def test_enrich_ror_empty_affiliations(self):
        enricher = Enricher()
        paper = {"title": "Test paper", "affiliations": []}
        enricher._enrich_ror_affiliations(paper)
        # Should not fail

    def test_clean_doi_str(self):
        assert Enricher._clean_doi_str("https://doi.org/10.1038/s41592") == "10.1038/s41592"
        assert Enricher._clean_doi_str("10.1038/s41592") == "10.1038/s41592"
        assert Enricher._clean_doi_str("") == ""
