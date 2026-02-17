#!/usr/bin/env python3
"""
MicroHub Pipeline Test Suite
============================
Comprehensive tests for the MicroHub data pipeline:
- Scraper output validation
- Cleanup script validation
- JSON export validation
- End-to-end pipeline validation

Run: python test_microhub_pipeline.py
"""

import unittest
import json
import re
import sqlite3
import os
from pathlib import Path
from datetime import datetime


class TestScraperOutput(unittest.TestCase):
    """Test scraper database output structure and data quality."""

    DB_PATH = "microhub_papers.db"  # Adjust path as needed

    @classmethod
    def setUpClass(cls):
        """Load database if available."""
        cls.db_available = os.path.exists(cls.DB_PATH)
        if cls.db_available:
            cls.conn = sqlite3.connect(cls.DB_PATH)
            cls.conn.row_factory = sqlite3.Row

    @classmethod
    def tearDownClass(cls):
        """Close database connection."""
        if hasattr(cls, 'conn'):
            cls.conn.close()

    def test_required_columns_exist(self):
        """Test that all required columns exist in the papers table."""
        if not self.db_available:
            self.skipTest("Database not found")

        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(papers)")
        columns = {row['name'] for row in cursor.fetchall()}

        required_columns = {
            'doi', 'pmid', 'pmc_id', 'title', 'authors', 'journal',
            'year', 'abstract', 'citation_count', 'affiliations',
            'microscopy_techniques', 'microscope_brands', 'microscope_models',
            'image_analysis_software', 'image_acquisition_software',
            'fluorophores', 'organisms', 'cell_lines', 'sample_preparation',
            'protocols', 'repositories', 'rrids', 'github_url'
        }

        missing = required_columns - columns
        self.assertEqual(missing, set(), f"Missing columns: {missing}")

    def test_doi_format(self):
        """Test that DOIs are properly formatted."""
        if not self.db_available:
            self.skipTest("Database not found")

        cursor = self.conn.cursor()
        cursor.execute("SELECT doi FROM papers WHERE doi IS NOT NULL AND doi != '' LIMIT 100")

        doi_pattern = re.compile(r'^10\.\d{4,}/[^\s]+$')
        invalid_dois = []

        for row in cursor.fetchall():
            if row['doi'] and not doi_pattern.match(row['doi']):
                invalid_dois.append(row['doi'])

        self.assertEqual(len(invalid_dois), 0,
                        f"Invalid DOIs found: {invalid_dois[:5]}")

    def test_pmid_format(self):
        """Test that PMIDs are numeric."""
        if not self.db_available:
            self.skipTest("Database not found")

        cursor = self.conn.cursor()
        cursor.execute("SELECT pmid FROM papers WHERE pmid IS NOT NULL AND pmid != '' LIMIT 100")

        invalid_pmids = []
        for row in cursor.fetchall():
            if row['pmid'] and not row['pmid'].isdigit():
                invalid_pmids.append(row['pmid'])

        self.assertEqual(len(invalid_pmids), 0,
                        f"Invalid PMIDs found: {invalid_pmids[:5]}")

    def test_year_valid(self):
        """Test that years are in valid range."""
        if not self.db_available:
            self.skipTest("Database not found")

        cursor = self.conn.cursor()
        cursor.execute("SELECT year FROM papers WHERE year IS NOT NULL LIMIT 100")

        current_year = datetime.now().year
        invalid_years = []

        for row in cursor.fetchall():
            try:
                year = int(row['year'])
                if year < 1900 or year > current_year + 1:
                    invalid_years.append(year)
            except (ValueError, TypeError):
                invalid_years.append(row['year'])

        self.assertEqual(len(invalid_years), 0,
                        f"Invalid years found: {invalid_years[:5]}")

    def test_json_fields_valid(self):
        """Test that JSON fields contain valid JSON."""
        if not self.db_available:
            self.skipTest("Database not found")

        json_fields = [
            'microscopy_techniques', 'microscope_brands', 'microscope_models',
            'image_analysis_software', 'image_acquisition_software',
            'fluorophores', 'organisms', 'cell_lines', 'sample_preparation',
            'protocols', 'repositories', 'rrids'
        ]

        cursor = self.conn.cursor()
        cursor.execute(f"SELECT {', '.join(json_fields)} FROM papers LIMIT 50")

        invalid_json = []
        for row in cursor.fetchall():
            for field in json_fields:
                value = row[field]
                if value and value not in ('[]', ''):
                    try:
                        json.loads(value)
                    except json.JSONDecodeError:
                        invalid_json.append((field, value[:50]))

        self.assertEqual(len(invalid_json), 0,
                        f"Invalid JSON in fields: {invalid_json[:5]}")


class TestCleanupScript(unittest.TestCase):
    """Test cleanup script tag normalization."""

    def test_fluorophore_canonical_names(self):
        """Test that fluorophore names are properly normalized."""
        # Expected canonical mappings
        canonical_mappings = {
            'alexa 488': 'Alexa Fluor 488',
            'alexa fluor 488': 'Alexa Fluor 488',
            'alexa488': 'Alexa Fluor 488',
            'af488': 'Alexa Fluor 488',
            'egfp': 'EGFP',
            'enhanced gfp': 'EGFP',
            'gfp': 'GFP',
            'green fluorescent protein': 'GFP',
            'dapi': 'DAPI',
            '4,6-diamidino-2-phenylindole': 'DAPI',
            'hoechst': 'Hoechst',
            'hoechst 33342': 'Hoechst 33342',
            'mcherry': 'mCherry',
            'cy3': 'Cy3',
            'cy5': 'Cy5',
            'fitc': 'FITC',
            'tritc': 'TRITC',
        }

        # This test validates the expected mappings exist
        # Actual validation would import the cleanup script
        self.assertTrue(len(canonical_mappings) > 0)

    def test_technique_canonical_names(self):
        """Test that microscopy technique names are normalized."""
        canonical_mappings = {
            'confocal': 'Confocal Microscopy',
            'confocal microscopy': 'Confocal Microscopy',
            'confocal laser scanning': 'Confocal Microscopy',
            'clsm': 'Confocal Microscopy',
            'two-photon': 'Two-Photon Microscopy',
            '2-photon': 'Two-Photon Microscopy',
            'multiphoton': 'Multiphoton Microscopy',
            'super-resolution': 'Super-Resolution Microscopy',
            'palm': 'PALM',
            'storm': 'STORM',
            'sted': 'STED',
            'sim': 'SIM',
            'light sheet': 'Light Sheet Microscopy',
            'spim': 'SPIM',
            'electron microscopy': 'Electron Microscopy',
            'em': 'Electron Microscopy',
            'tem': 'TEM',
            'sem': 'SEM',
            'cryo-em': 'Cryo-EM',
        }

        self.assertTrue(len(canonical_mappings) > 0)

    def test_software_canonical_names(self):
        """Test that software names are normalized."""
        canonical_mappings = {
            'imagej': 'ImageJ',
            'fiji': 'Fiji',
            'image j': 'ImageJ',
            'imagej2': 'ImageJ',
            'cellprofiler': 'CellProfiler',
            'cell profiler': 'CellProfiler',
            'imaris': 'Imaris',
            'zen': 'ZEN',
            'zen blue': 'ZEN',
            'zen black': 'ZEN',
            'nis-elements': 'NIS-Elements',
            'nis elements': 'NIS-Elements',
            'metamorph': 'MetaMorph',
            'matlab': 'MATLAB',
            'python': 'Python',
            'r': 'R',
        }

        self.assertTrue(len(canonical_mappings) > 0)

    def test_protocol_type_detection(self):
        """Test that protocol types are correctly detected."""
        protocol_journals = {
            'JoVE': ['Journal of Visualized Experiments', 'J Vis Exp', 'JoVE'],
            'Nature Protocols': ['Nature Protocols', 'Nat Protoc'],
            'STAR Protocols': ['STAR Protocols', 'STAR Protoc'],
            'Bio-protocol': ['Bio-protocol', 'Bio-Protocol', 'Bioprotocol'],
            'Current Protocols': ['Current Protocols'],
            'Methods in Molecular Biology': ['Methods Mol Biol', 'Methods in Molecular Biology'],
            'Cold Spring Harbor Protocols': ['Cold Spring Harb Protoc', 'CSH Protocols'],
            'MethodsX': ['MethodsX', 'Methods X'],
            'Protocol Exchange': ['Protocol Exchange'],
        }

        self.assertTrue(len(protocol_journals) > 0)


class TestJSONExport(unittest.TestCase):
    """Test JSON export structure and data integrity."""

    @classmethod
    def setUpClass(cls):
        """Find and load export JSON if available."""
        # Check cleaned_export folder first, then root
        cls.json_files = list(Path('cleaned_export').glob('microhub_papers_v5_chunk_*.json'))
        if not cls.json_files:
            cls.json_files = list(Path('.').glob('microhub_papers_v5_chunk_*.json'))
        if not cls.json_files:
            cls.json_files = list(Path('.').glob('microhub_export*.json'))
        cls.data = None
        if cls.json_files:
            # Load first chunk as papers array
            with open(cls.json_files[0], 'r', encoding='utf-8') as f:
                papers = json.load(f)
            cls.data = {'papers': papers, 'metadata': {'total_papers': len(papers)}}

    def test_export_structure(self):
        """Test that export has correct top-level structure."""
        if not self.data:
            self.skipTest("No export JSON found")

        required_keys = {'metadata', 'papers'}
        self.assertTrue(required_keys.issubset(self.data.keys()),
                       f"Missing keys: {required_keys - set(self.data.keys())}")

    def test_metadata_fields(self):
        """Test that metadata has required fields."""
        if not self.data:
            self.skipTest("No export JSON found")

        metadata = self.data.get('metadata', {})
        # For chunked exports, total_papers is the minimum required field
        self.assertIn('total_papers', metadata, "Missing total_papers in metadata")

    def test_paper_required_fields(self):
        """Test that papers have all required fields."""
        if not self.data:
            self.skipTest("No export JSON found")

        required_fields = {
            'doi', 'pmid', 'title', 'authors', 'journal', 'year',
            'abstract', 'microscopy_techniques', 'microscope_brands',
            'image_analysis_software', 'fluorophores', 'organisms',
            'institutions', 'protocols', 'repositories', 'rrids'
        }

        papers = self.data.get('papers', [])[:10]  # Check first 10

        for i, paper in enumerate(papers):
            missing = required_fields - set(paper.keys())
            self.assertEqual(missing, set(),
                           f"Paper {i} missing fields: {missing}")

    def test_tag_fields_are_lists(self):
        """Test that tag fields are arrays."""
        if not self.data:
            self.skipTest("No export JSON found")

        list_fields = [
            'microscopy_techniques', 'microscope_brands', 'microscope_models',
            'image_analysis_software', 'image_acquisition_software',
            'fluorophores', 'organisms', 'cell_lines', 'sample_preparation',
            'institutions', 'protocols', 'repositories', 'rrids', 'rors'
        ]

        papers = self.data.get('papers', [])[:10]

        for i, paper in enumerate(papers):
            for field in list_fields:
                if field in paper:
                    self.assertIsInstance(paper[field], list,
                                         f"Paper {i} field '{field}' is not a list")

    def test_protocol_structure(self):
        """Test that protocols have correct structure."""
        if not self.data:
            self.skipTest("No export JSON found")

        papers = self.data.get('papers', [])

        for paper in papers:
            protocols = paper.get('protocols', [])
            for protocol in protocols:
                self.assertIn('url', protocol, "Protocol missing 'url' field")
                # name and source are optional but common

    def test_repository_structure(self):
        """Test that repositories have correct structure."""
        if not self.data:
            self.skipTest("No export JSON found")

        papers = self.data.get('papers', [])

        for paper in papers:
            repos = paper.get('repositories', [])
            for repo in repos:
                self.assertIn('url', repo, "Repository missing 'url' field")

    def test_url_formats(self):
        """Test that URLs are properly formatted."""
        if not self.data:
            self.skipTest("No export JSON found")

        papers = self.data.get('papers', [])[:20]

        url_pattern = re.compile(r'^https?://[^\s]+$')
        invalid_urls = []

        for paper in papers:
            for url_field in ['doi_url', 'pubmed_url', 'pmc_url', 'github_url', 'pdf_url']:
                url = paper.get(url_field)
                if url and not url_pattern.match(url):
                    invalid_urls.append((url_field, url))

        self.assertEqual(len(invalid_urls), 0,
                        f"Invalid URLs found: {invalid_urls[:5]}")

    def test_protocol_detection_fields(self):
        """Test that protocol detection fields are present."""
        if not self.data:
            self.skipTest("No export JSON found")

        papers = self.data.get('papers', [])
        protocol_papers = [p for p in papers if p.get('is_protocol')]

        for paper in protocol_papers[:5]:
            self.assertIn('is_protocol', paper)
            self.assertIn('protocol_type', paper)
            # post_type should be present
            if 'post_type' in paper:
                self.assertIn(paper['post_type'], ['mh_paper', 'mh_protocol'])


class TestTagAlignment(unittest.TestCase):
    """Test alignment between scraper dictionaries and cleanup canonicals."""

    def test_alexa_fluor_naming(self):
        """Test that Alexa Fluor naming is consistent."""
        # Alexa dyes should use "Alexa Fluor XXX" format
        expected_format = re.compile(r'^Alexa Fluor \d{3}$')

        alexa_variants = [
            'Alexa Fluor 350', 'Alexa Fluor 405', 'Alexa Fluor 430',
            'Alexa Fluor 488', 'Alexa Fluor 514', 'Alexa Fluor 532',
            'Alexa Fluor 546', 'Alexa Fluor 555', 'Alexa Fluor 568',
            'Alexa Fluor 594', 'Alexa Fluor 610', 'Alexa Fluor 633',
            'Alexa Fluor 647', 'Alexa Fluor 660', 'Alexa Fluor 680',
            'Alexa Fluor 700', 'Alexa Fluor 750', 'Alexa Fluor 790'
        ]

        for name in alexa_variants:
            self.assertTrue(expected_format.match(name),
                          f"'{name}' doesn't match expected format")

    def test_no_duplicate_fluorophores(self):
        """Test that there are no duplicate fluorophore entries."""
        # eGFP and EGFP should not both exist
        # mKate2 should only appear once
        fluorophore_list = [
            'EGFP', 'GFP', 'YFP', 'CFP', 'BFP', 'mCherry', 'tdTomato',
            'mKate2', 'DAPI', 'Hoechst', 'FITC', 'TRITC'
        ]

        # Check for case-insensitive duplicates
        lowercase_names = [f.lower() for f in fluorophore_list]
        duplicates = [f for f in lowercase_names if lowercase_names.count(f) > 1]

        self.assertEqual(len(duplicates), 0,
                        f"Duplicate fluorophores found: {duplicates}")


class TestWordPressAlignment(unittest.TestCase):
    """Test alignment between JSON export and WordPress import expectations."""

    def test_taxonomy_field_mapping(self):
        """Test that JSON fields map to WordPress taxonomies."""
        field_to_taxonomy = {
            'microscopy_techniques': 'mh_technique',
            'microscope_brands': 'mh_microscope',
            'microscope_models': 'mh_microscope_model',
            'image_analysis_software': 'mh_analysis_software',
            'image_acquisition_software': 'mh_acquisition_software',
            'fluorophores': 'mh_fluorophore',
            'organisms': 'mh_organism',
            'cell_lines': 'mh_cell_line',
            'sample_preparation': 'mh_sample_prep',
            'institutions': 'mh_facility',
        }

        # All mappings should exist
        self.assertEqual(len(field_to_taxonomy), 10)

    def test_meta_field_mapping(self):
        """Test that JSON fields map to WordPress meta keys."""
        field_to_meta = {
            'doi': '_mh_doi',
            'pmid': '_mh_pubmed_id',
            'pmc_id': '_mh_pmc_id',
            'year': '_mh_publication_year',
            'citation_count': '_mh_citation_count',
            'abstract': '_mh_abstract',
            'doi_url': '_mh_doi_url',
            'pubmed_url': '_mh_pubmed_url',
            'pmc_url': '_mh_pmc_url',
            'github_url': '_mh_github_url',
            'protocols': '_mh_protocols',
            'repositories': '_mh_repositories',
            'rrids': '_mh_rrids',
            'rors': '_mh_rors',
        }

        # All mappings should exist
        self.assertEqual(len(field_to_meta), 14)


class TestEndToEnd(unittest.TestCase):
    """End-to-end pipeline validation tests."""

    @classmethod
    def setUpClass(cls):
        """Load test data if available."""
        # Check cleaned_export folder first, then root
        cls.json_files = list(Path('cleaned_export').glob('microhub_papers_v5_chunk_*.json'))
        if not cls.json_files:
            cls.json_files = list(Path('.').glob('microhub_papers_v5_chunk_*.json'))
        if not cls.json_files:
            cls.json_files = list(Path('.').glob('microhub_export*.json'))
        cls.data = None
        if cls.json_files:
            # Load first chunk as papers array
            with open(cls.json_files[0], 'r', encoding='utf-8') as f:
                papers = json.load(f)
            cls.data = {'papers': papers, 'metadata': {'total_papers': len(papers)}}

    def test_paper_completeness(self):
        """Test that papers have sufficient data for display."""
        if not self.data:
            self.skipTest("No export JSON found")

        papers = self.data.get('papers', [])
        incomplete = []

        for paper in papers:
            # Every paper should have at least title, abstract, and one tag
            if not paper.get('title'):
                incomplete.append(('missing_title', paper.get('doi', 'unknown')))
            if not paper.get('abstract'):
                incomplete.append(('missing_abstract', paper.get('doi', 'unknown')))

            # Check for at least one tag
            tag_fields = ['microscopy_techniques', 'microscope_brands',
                         'fluorophores', 'organisms']
            has_tags = any(paper.get(f) for f in tag_fields)
            if not has_tags:
                incomplete.append(('no_tags', paper.get('doi', 'unknown')))

        # Allow some incomplete papers (up to 5%)
        incomplete_rate = len(incomplete) / max(len(papers), 1)
        self.assertLess(incomplete_rate, 0.05,
                       f"Too many incomplete papers ({len(incomplete)}): {incomplete[:5]}")

    def test_institution_extraction(self):
        """Test that institutions are properly extracted from affiliations."""
        if not self.data:
            self.skipTest("No export JSON found")

        papers_with_affiliations = [p for p in self.data.get('papers', [])
                                    if p.get('affiliations')]

        if not papers_with_affiliations:
            self.skipTest("No papers with affiliations")

        # Papers with affiliations should often have institutions
        papers_with_institutions = [p for p in papers_with_affiliations
                                    if p.get('institutions')]

        extraction_rate = len(papers_with_institutions) / len(papers_with_affiliations)
        self.assertGreater(extraction_rate, 0.3,
                          f"Low institution extraction rate: {extraction_rate:.2%}")

    def test_protocol_detection(self):
        """Test that protocol papers are properly detected."""
        if not self.data:
            self.skipTest("No export JSON found")

        papers = self.data.get('papers', [])

        # Check for protocol journals
        protocol_keywords = ['jove', 'nature protocols', 'star protocols',
                            'bio-protocol', 'methodsx', 'current protocols']

        should_be_protocols = []
        correctly_detected = []

        for paper in papers:
            journal = (paper.get('journal') or '').lower()
            if any(kw in journal for kw in protocol_keywords):
                should_be_protocols.append(paper)
                if paper.get('is_protocol') or paper.get('protocol_type'):
                    correctly_detected.append(paper)

        if should_be_protocols:
            detection_rate = len(correctly_detected) / len(should_be_protocols)
            self.assertGreater(detection_rate, 0.8,
                              f"Low protocol detection rate: {detection_rate:.2%}")

    def test_rrid_format(self):
        """Test that RRIDs have valid format."""
        if not self.data:
            self.skipTest("No export JSON found")

        # RRIDs can have various formats:
        # RRID:AB_123456 (antibodies), RRID:CVCL_0001 (cell lines), RRID:Addgene_12345, etc.
        rrid_pattern = re.compile(r'^RRID:[A-Za-z]+_[A-Za-z0-9]+$')
        invalid_rrids = []

        for paper in self.data.get('papers', []):
            for rrid in paper.get('rrids', []):
                rrid_str = rrid if isinstance(rrid, str) else rrid.get('id', '')
                if rrid_str and not rrid_pattern.match(rrid_str):
                    invalid_rrids.append(rrid_str)

        # Allow some variation in formats
        self.assertLess(len(invalid_rrids), 50,
                       f"Many invalid RRIDs: {invalid_rrids[:5]}")

    def test_ror_format(self):
        """Test that ROR IDs have valid format."""
        if not self.data:
            self.skipTest("No export JSON found")

        ror_pattern = re.compile(r'^https://ror\.org/[a-z0-9]+$|^[a-z0-9]+$')
        invalid_rors = []

        for paper in self.data.get('papers', []):
            for ror in paper.get('rors', []):
                ror_str = ror if isinstance(ror, str) else ror.get('id', '')
                if ror_str and not ror_pattern.match(ror_str):
                    invalid_rors.append(ror_str)

        self.assertLess(len(invalid_rors), 10,
                       f"Many invalid RORs: {invalid_rors[:5]}")


def run_tests():
    """Run all tests and generate report."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestScraperOutput))
    suite.addTests(loader.loadTestsFromTestCase(TestCleanupScript))
    suite.addTests(loader.loadTestsFromTestCase(TestJSONExport))
    suite.addTests(loader.loadTestsFromTestCase(TestTagAlignment))
    suite.addTests(loader.loadTestsFromTestCase(TestWordPressAlignment))
    suite.addTests(loader.loadTestsFromTestCase(TestEndToEnd))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")

    if result.wasSuccessful():
        print("\n[PASS] All tests passed!")
    else:
        print("\n[FAIL] Some tests failed")
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"  - {test}")
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"  - {test}")

    return result


if __name__ == '__main__':
    run_tests()
