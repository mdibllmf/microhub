"""Tests for the DataCite + OpenAIRE dataset linker agent."""

import pytest

from pipeline.agents.datacite_linker_agent import DataCiteLinkerAgent


class TestAccessionExtraction:
    """Test regex-based accession extraction from text."""

    def setup_method(self):
        self.agent = DataCiteLinkerAgent()

    def test_empiar_accession(self):
        text = "Data deposited at EMPIAR-12345."
        links = self.agent._extract_accessions(text)
        assert any(l["repository"] == "EMPIAR" for l in links)
        assert any(l["accession"] == "EMPIAR-12345" for l in links)

    def test_emdb_accession(self):
        text = "The map was deposited in EMDB under accession EMD-1234."
        links = self.agent._extract_accessions(text)
        assert any(l["repository"] == "EMDB" for l in links)

    def test_geo_accession(self):
        text = "RNA-seq data available at GEO accession GSE123456."
        links = self.agent._extract_accessions(text)
        assert any(l["repository"] == "GEO" for l in links)
        assert any("GSE123456" in l["accession"] for l in links)

    def test_sra_accessions(self):
        text = "Sequencing data: SRP123456, SRR654321, SRX111111."
        links = self.agent._extract_accessions(text)
        repos = [l["repository"] for l in links]
        assert repos.count("SRA") == 3

    def test_bioproject_accession(self):
        text = "Registered under BioProject PRJNA123456."
        links = self.agent._extract_accessions(text)
        assert any(l["repository"] == "BioProject" for l in links)

    def test_biostudies_accession(self):
        text = "Deposited at BioStudies under S-BSST123."
        links = self.agent._extract_accessions(text)
        assert any(l["repository"] == "BioStudies" for l in links)

    def test_bioimage_archive_accession(self):
        text = "Images are available at S-BIAD456."
        links = self.agent._extract_accessions(text)
        assert any(l["repository"] == "BioImage Archive" and l["accession"] == "S-BIAD456"
                    for l in links)

    def test_proteomexchange_accession(self):
        text = "Proteomics data deposited at PXD012345."
        links = self.agent._extract_accessions(text)
        assert any(l["repository"] == "ProteomeXchange" for l in links)

    def test_arrayexpress_accession(self):
        text = "ArrayExpress accession E-MTAB-1234."
        links = self.agent._extract_accessions(text)
        assert any(l["repository"] == "ArrayExpress" for l in links)

    def test_multiple_accessions(self):
        text = ("Data deposited at EMPIAR-12345 and GEO GSE123456. "
                "Sequences at SRP654321.")
        links = self.agent._extract_accessions(text)
        assert len(links) == 3

    def test_no_accessions(self):
        text = "This is a regular paragraph with no accession numbers."
        links = self.agent._extract_accessions(text)
        assert len(links) == 0

    def test_deduplication(self):
        text = "Data at EMPIAR-12345. See also EMPIAR-12345."
        links = self.agent._extract_accessions(text)
        empiar = [l for l in links if l["repository"] == "EMPIAR"]
        assert len(empiar) == 1


class TestDOIClassification:
    """Test DOI prefix classification."""

    def setup_method(self):
        self.agent = DataCiteLinkerAgent()

    def test_zenodo_doi(self):
        assert self.agent._repo_from_doi_prefix("10.5281/zenodo.123456") == "Zenodo"

    def test_figshare_doi(self):
        assert self.agent._repo_from_doi_prefix("10.6084/m9.figshare.123") == "Figshare"

    def test_dryad_doi(self):
        assert self.agent._repo_from_doi_prefix("10.5061/dryad.abc123") == "Dryad"

    def test_unknown_doi(self):
        assert self.agent._repo_from_doi_prefix("10.1038/s41592") == "Unknown"

    def test_clean_doi(self):
        assert self.agent._clean_doi("https://doi.org/10.1038/s41592") == "10.1038/s41592"
