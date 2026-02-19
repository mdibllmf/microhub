"""Tests for the Unpaywall OA discovery client."""

import pytest

from pipeline.parsing.unpaywall_client import UnpaywallClient


class TestUnpaywallClient:
    """Test Unpaywall client (non-network tests)."""

    def test_clean_doi(self):
        assert UnpaywallClient._clean_doi("10.1038/s41592") == "10.1038/s41592"
        assert UnpaywallClient._clean_doi("https://doi.org/10.1038/s41592") == "10.1038/s41592"
        assert UnpaywallClient._clean_doi("http://doi.org/10.1038/s41592") == "10.1038/s41592"
        assert UnpaywallClient._clean_doi("doi:10.1038/s41592") == "10.1038/s41592"
        assert UnpaywallClient._clean_doi("DOI:10.1038/s41592") == "10.1038/s41592"
        assert UnpaywallClient._clean_doi("  10.1038/s41592  ") == "10.1038/s41592"
        assert UnpaywallClient._clean_doi("") == ""
        assert UnpaywallClient._clean_doi(None) == ""

    def test_parse_response_oa(self):
        data = {
            "is_oa": True,
            "oa_status": "gold",
            "best_oa_location": {
                "url_for_pdf": "https://example.com/paper.pdf",
                "version": "publishedVersion",
                "url_for_landing_page": "https://example.com/paper",
                "host_type": "publisher",
                "license": "cc-by",
            },
            "journal_name": "Nature Methods",
            "title": "Super-resolution imaging",
            "year": 2023,
            "doi": "10.1038/s41592",
        }
        result = UnpaywallClient._parse_response(data)
        assert result["is_oa"] is True
        assert result["oa_status"] == "gold"
        assert result["pdf_url"] == "https://example.com/paper.pdf"
        assert result["pdf_version"] == "publishedVersion"
        assert result["license"] == "cc-by"

    def test_parse_response_closed(self):
        data = {
            "is_oa": False,
            "oa_status": "closed",
            "best_oa_location": None,
            "journal_name": "Cell",
            "title": "A study",
            "year": 2022,
            "doi": "10.1016/j.cell.2022",
        }
        result = UnpaywallClient._parse_response(data)
        assert result["is_oa"] is False
        assert result["oa_status"] == "closed"
        assert result["pdf_url"] is None

    def test_cache_behavior(self):
        client = UnpaywallClient()
        # Manually populate cache
        client._cache["10.1038/test"] = {"is_oa": True, "pdf_url": "cached"}
        result = client.lookup("10.1038/test")
        assert result["pdf_url"] == "cached"

    def test_find_pdf_url_empty(self):
        client = UnpaywallClient()
        # Empty DOI
        assert client.find_pdf_url("") is None
        assert client.find_pdf_url(None) is None
