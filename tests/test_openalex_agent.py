"""Tests for the OpenAlex enrichment agent."""

import pytest

from pipeline.agents.openalex_agent import OpenAlexAgent


class TestOpenAlexAgent:
    """Test OpenAlex agent (non-network tests)."""

    def test_clean_doi(self):
        assert OpenAlexAgent._clean_doi("10.1038/s41592") == "10.1038/s41592"
        assert OpenAlexAgent._clean_doi("https://doi.org/10.1038/s41592") == "10.1038/s41592"
        assert OpenAlexAgent._clean_doi("DOI:10.1038/s41592") == "10.1038/s41592"

    def test_parse_work_basic(self):
        data = {
            "id": "https://openalex.org/W123",
            "ids": {
                "doi": "https://doi.org/10.1038/s41592",
                "pmid": "https://pubmed.ncbi.nlm.nih.gov/12345",
                "pmcid": "PMC1234567",
            },
            "title": "Super-resolution microscopy of cells",
            "publication_year": 2023,
            "type": "article",
            "cited_by_count": 42,
            "fwci": 3.5,
            "open_access": {
                "is_oa": True,
                "oa_status": "gold",
                "oa_url": "https://example.com/paper",
            },
            "authorships": [
                {
                    "author": {
                        "display_name": "Jane Smith",
                        "orcid": "https://orcid.org/0000-0001-1234-5678",
                    },
                    "institutions": [
                        {
                            "display_name": "MIT",
                            "ror": "https://ror.org/042nb2s44",
                            "country_code": "US",
                            "type": "education",
                        }
                    ],
                }
            ],
            "topics": [
                {
                    "display_name": "Super-Resolution Fluorescence Microscopy",
                    "score": 0.98,
                    "domain": {"display_name": "Physical Sciences"},
                    "field": {"display_name": "Physics and Astronomy"},
                    "subfield": {"display_name": "Atomic and Molecular Physics"},
                }
            ],
            "referenced_works": ["https://openalex.org/W456"],
            "related_works": ["https://openalex.org/W789"],
        }

        result = OpenAlexAgent._parse_work(data)

        assert result["openalex_id"] == "https://openalex.org/W123"
        assert result["doi"] == "10.1038/s41592"
        assert result["pmcid"] == "PMC1234567"
        assert result["title"] == "Super-resolution microscopy of cells"
        assert result["publication_year"] == 2023
        assert result["cited_by_count"] == 42
        assert result["fwci"] == 3.5
        assert result["is_oa"] is True
        assert result["oa_status"] == "gold"

        # Authors
        assert len(result["authors"]) == 1
        assert result["authors"][0]["name"] == "Jane Smith"

        # Institutions with ROR
        assert len(result["institutions"]) == 1
        assert result["institutions"][0]["name"] == "MIT"
        assert result["institutions"][0]["ror_id"] == "https://ror.org/042nb2s44"

        # Topics
        assert len(result["topics"]) == 1
        assert "Fluorescence Microscopy" in result["topics"][0]["name"]
        assert result["topics"][0]["domain"] == "Physical Sciences"

    def test_parse_work_minimal(self):
        data = {
            "id": "https://openalex.org/W999",
            "title": "A paper",
        }
        result = OpenAlexAgent._parse_work(data)
        assert result["openalex_id"] == "https://openalex.org/W999"
        assert result["title"] == "A paper"
        assert result["authors"] == []
        assert result["institutions"] == []
        assert result["topics"] == []

    def test_cache_behavior(self):
        agent = OpenAlexAgent()
        agent._cache["10.1038/test"] = {"title": "cached"}
        result = agent.enrich_paper(doi="10.1038/test")
        assert result["title"] == "cached"

    def test_enrich_paper_no_identifier(self):
        agent = OpenAlexAgent()
        result = agent.enrich_paper()
        assert result is None
