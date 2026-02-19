"""Tests for the ROR v2 API client."""

import pytest

from pipeline.validation.ror_v2_client import RORv2Client


class TestRORIDValidation:
    """Test ROR ID format validation and extraction."""

    def test_valid_ror_ids(self):
        assert RORv2Client.validate_ror_id("03yrm5c26") is True
        assert RORv2Client.validate_ror_id("042nb2s44") is True
        assert RORv2Client.validate_ror_id("00f54p054") is True

    def test_valid_ror_urls(self):
        assert RORv2Client.validate_ror_id("https://ror.org/03yrm5c26") is True
        assert RORv2Client.validate_ror_id("ror.org/042nb2s44") is True

    def test_invalid_ror_ids(self):
        # Too short
        assert RORv2Client.validate_ror_id("03yrm5c") is False
        # Contains invalid chars (I, L, O, U are excluded)
        assert RORv2Client.validate_ror_id("") is False
        assert RORv2Client.validate_ror_id(None) is False
        # Doesn't start with 0
        assert RORv2Client.validate_ror_id("13yrm5c26") is False

    def test_extract_ror_id_from_url(self):
        assert RORv2Client.extract_ror_id("https://ror.org/03yrm5c26") == "03yrm5c26"
        assert RORv2Client.extract_ror_id("http://ror.org/042nb2s44") == "042nb2s44"

    def test_extract_ror_id_bare(self):
        assert RORv2Client.extract_ror_id("03yrm5c26") == "03yrm5c26"
        assert RORv2Client.extract_ror_id("042nb2s44") == "042nb2s44"

    def test_extract_ror_id_domain_path(self):
        assert RORv2Client.extract_ror_id("ror.org/03yrm5c26") == "03yrm5c26"

    def test_extract_ror_id_invalid(self):
        assert RORv2Client.extract_ror_id("") is None
        assert RORv2Client.extract_ror_id(None) is None
        assert RORv2Client.extract_ror_id("not-a-ror-id") is None


class TestRORv2Client:
    """Test ROR v2 client (non-network tests)."""

    def test_parse_org_v2_format(self):
        data = {
            "id": "https://ror.org/042nb2s44",
            "names": [
                {"value": "Massachusetts Institute of Technology", "types": ["ror_display"]},
                {"value": "MIT", "types": ["acronym"]},
            ],
            "locations": [
                {
                    "geonames_details": {
                        "country_name": "United States",
                        "country_code": "US",
                    }
                }
            ],
            "types": ["education"],
            "status": "active",
            "relationships": [
                {
                    "type": "child",
                    "id": "https://ror.org/03yrm5c26",
                    "label": "Lincoln Laboratory",
                }
            ],
        }
        result = RORv2Client._parse_org(data)
        assert result["ror_id"] == "042nb2s44"
        assert result["name"] == "Massachusetts Institute of Technology"
        assert result["country"] == "United States"
        assert result["country_code"] == "US"
        assert result["status"] == "active"
        assert len(result["relationships"]) == 1

    def test_parse_org_minimal(self):
        data = {
            "id": "https://ror.org/00f54p054",
            "name": "Stanford University",
            "status": "active",
        }
        result = RORv2Client._parse_org(data)
        assert result["ror_id"] == "00f54p054"
        assert result["name"] == "Stanford University"

    def test_cache_behavior(self):
        client = RORv2Client()
        client._cache["mit, cambridge"] = {
            "ror_id": "042nb2s44",
            "name": "MIT",
        }
        result = client.match_affiliation("MIT, Cambridge")
        assert result["ror_id"] == "042nb2s44"

    def test_match_affiliation_empty(self):
        client = RORv2Client()
        assert client.match_affiliation("") is None
        assert client.match_affiliation(None) is None
        assert client.match_affiliation("   ") is None
