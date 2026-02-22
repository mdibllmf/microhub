#!/usr/bin/env python3
"""
MicroHub Data Validation Suite v1.0

Validates the integrity of scraped/cleaned data before WordPress import.
Checks for:
- Required fields
- Field format consistency
- Tag value validity
- URL accessibility (optional)
- Cross-reference consistency

Usage:
    python validate_microhub_data.py --input exports/ --output validation_report.md
    python validate_microhub_data.py --input exports/ --check-links --sample 100
"""

import argparse
import json
import glob
import os
import re
import random
import logging
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# =============================================================================
# VALID TAG VALUES - Must match MASTER_TAG_DICTIONARY.json
# =============================================================================

VALID_MICROSCOPY_TECHNIQUES = {
    "3D Imaging", "4D Imaging", "AFM", "Airyscan", "Array Tomography", "Brightfield",
    "CARS", "Calcium Imaging", "Confocal", "Cryo-EM", "Cryo-ET", "CLEM", "DIC",
    "DNA-PAINT", "Darkfield", "Deconvolution", "Electron Tomography", "Epifluorescence",
    "Expansion Microscopy", "FCS", "FCCS", "FIB-SEM", "FLIM", "FLIP", "FRAP", "FRET",
    "Fluorescence Microscopy", "High-Content Screening", "Holographic", "Immuno-EM",
    "Immunofluorescence", "Intravital", "Lattice Light Sheet", "Light Sheet",
    "Live Cell Imaging", "MINFLUX", "MesoSPIM", "Multiphoton", "Negative Stain EM",
    "OCT", "Optical Sectioning", "Optogenetics", "PALM", "Phase Contrast", "Photoacoustic",
    "Polarization", "RESOLFT", "Raman", "SEM", "SHG", "SIM", "SMLM", "SOFI", "SRS",
    "Serial Block-Face SEM", "Single Molecule", "Single Particle", "Spinning Disk",
    "STED", "STORM", "Super-Resolution", "TEM", "TIRF", "Three-Photon", "Two-Photon",
    "Voltage Imaging", "Volume EM", "Widefield", "Z-Stack", "dSTORM", "Second Harmonic",
}

VALID_MICROSCOPE_BRANDS = {
    "3i (Intelligent Imaging)", "ASI", "Abberior", "Andor", "Becker & Hickl", "Bruker",
    "Chroma", "Coherent", "Edmund Optics", "Evident (Olympus)", "Hamamatsu", "JEOL",
    "LaVision BioTec", "Leica", "Luxendo", "Miltenyi", "Molecular Devices", "Newport",
    "Nikon", "Olympus", "PCO", "PerkinElmer", "Photometrics", "Photron", "PicoQuant",
    "Princeton Instruments", "Prior Scientific", "QImaging", "Roper", "Semrock",
    "Spectra-Physics", "Sutter", "Thermo Fisher", "Thorlabs", "Till Photonics",
    "Visitech", "Yokogawa", "Zeiss", "Applied Scientific Instrumentation", "Prior",
}

VALID_ORGANISMS = {
    "Arabidopsis", "Bacteria", "C. elegans", "Chicken", "Dog", "Drosophila",
    "E. coli", "Human", "Maize", "Monkey", "Mouse", "Organoid", "Pig", "Plant",
    "Rabbit", "Rat", "Spheroid", "Tobacco", "Xenopus", "Yeast", "Zebrafish",
}

VALID_PROTOCOL_TYPES = {
    "Bio-protocol", "Biotechniques", "Cold Spring Harbor Protocols",
    "Current Protocols", "JoVE", "MethodsX", "Methods in Enzymology",
    "Methods in Molecular Biology", "Nature Protocols", "Protocol Exchange",
    "STAR Protocols",
}

VALID_REPOSITORY_TYPES = {
    "ArrayExpress", "BioImage Archive", "BioStudies", "Code Ocean", "Dryad",
    "EMDB", "EMPIAR", "Figshare", "GEO", "GitHub", "GitLab", "IDR",
    "IDR Dataset", "IDR Image", "IDR Project", "Mendeley Data", "OMERO",
    "OMERO Public", "OSF", "PDB", "PRIDE", "SRA", "SSBD", "Zenodo",
}


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def load_json_file(filepath: str) -> List[Dict]:
    """Load a JSON file and return list of papers."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'papers' in data:
                return data['papers']
            else:
                return [data]
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {filepath}: {e}")
        return []
    except Exception as e:
        logger.error(f"Error loading {filepath}: {e}")
        return []


def validate_paper(paper: Dict) -> List[str]:
    """Validate a single paper's data integrity. Returns list of issues."""
    issues = []
    pmid = paper.get('pmid', 'UNKNOWN')

    # =========================
    # Required Fields
    # =========================
    required_fields = ['title', 'pmid']
    for field in required_fields:
        if not paper.get(field):
            issues.append(f"[{pmid}] Missing required field: {field}")

    # =========================
    # DOI Validation
    # =========================
    doi = paper.get('doi')
    if doi:
        # DOI should start with 10.
        if not str(doi).startswith('10.'):
            issues.append(f"[{pmid}] Invalid DOI format (should start with '10.'): {doi}")
        # DOI should not contain URL prefix
        if 'doi.org' in str(doi).lower():
            issues.append(f"[{pmid}] DOI contains URL prefix (should be just the DOI): {doi}")

    # =========================
    # Year Validation
    # =========================
    year = paper.get('year')
    if year:
        try:
            year_int = int(year)
            if year_int < 1900 or year_int > 2030:
                issues.append(f"[{pmid}] Invalid year (out of range 1900-2030): {year}")
        except (ValueError, TypeError):
            issues.append(f"[{pmid}] Invalid year format: {year}")

    # =========================
    # PMID Validation
    # =========================
    if pmid and pmid != 'UNKNOWN':
        if not str(pmid).isdigit():
            issues.append(f"[{pmid}] PMID should be numeric: {pmid}")

    # =========================
    # URL Validation (format only)
    # =========================
    url_fields = ['doi_url', 'pubmed_url', 'pmc_url', 'github_url', 'pdf_url']
    for field in url_fields:
        url = paper.get(field)
        if url and not str(url).startswith('http'):
            issues.append(f"[{pmid}] Invalid URL format in {field}: {url}")

    # DOI URL should match DOI
    if doi and paper.get('doi_url'):
        expected_doi_url = f"https://doi.org/{doi}"
        if paper['doi_url'] != expected_doi_url:
            # Allow http vs https difference
            if paper['doi_url'].replace('http://', 'https://') != expected_doi_url:
                issues.append(f"[{pmid}] DOI URL doesn't match DOI: {paper['doi_url']} vs {expected_doi_url}")

    # =========================
    # Array Fields Should Be Arrays
    # =========================
    array_fields = [
        'microscopy_techniques', 'microscope_brands', 'microscope_models',
        'fluorophores', 'organisms', 'cell_lines', 'sample_preparation',
        'image_analysis_software', 'image_acquisition_software',
        'protocols', 'repositories', 'rrids', 'rors',
        'affiliations', 'institutions', 'figures',
    ]
    for field in array_fields:
        value = paper.get(field)
        if value is not None and not isinstance(value, list):
            # Try to parse if it's a JSON string
            if isinstance(value, str):
                try:
                    parsed = json.loads(value)
                    if not isinstance(parsed, list):
                        issues.append(f"[{pmid}] Field {field} should be array, got {type(parsed).__name__}")
                except json.JSONDecodeError:
                    issues.append(f"[{pmid}] Field {field} should be array, got unparseable string")
            else:
                issues.append(f"[{pmid}] Field {field} should be array, got {type(value).__name__}")

    # =========================
    # Protocol Objects Validation
    # =========================
    protocols = paper.get('protocols', [])
    if isinstance(protocols, list):
        for i, protocol in enumerate(protocols):
            if not isinstance(protocol, dict):
                issues.append(f"[{pmid}] Protocol {i} should be dict: {protocol}")
            elif not protocol.get('url') and not protocol.get('name'):
                issues.append(f"[{pmid}] Protocol {i} missing both URL and name: {protocol}")

    # =========================
    # Repository Objects Validation
    # =========================
    repositories = paper.get('repositories', [])
    if isinstance(repositories, list):
        for i, repo in enumerate(repositories):
            if not isinstance(repo, dict):
                issues.append(f"[{pmid}] Repository {i} should be dict: {repo}")
            elif not repo.get('url') and not repo.get('id') and not repo.get('accession_id'):
                issues.append(f"[{pmid}] Repository {i} missing URL/ID: {repo}")

    # =========================
    # RRID Objects Validation
    # =========================
    rrids = paper.get('rrids', [])
    if isinstance(rrids, list):
        for i, rrid in enumerate(rrids):
            if isinstance(rrid, dict):
                rrid_id = rrid.get('id', '')
                if rrid_id and not rrid_id.startswith('RRID:'):
                    # Check if it has a valid prefix
                    valid_prefixes = ['AB_', 'SCR_', 'CVCL_', 'Addgene_', 'IMSR_', 'BDSC_', 'ZFIN_']
                    if not any(rrid_id.startswith(p) for p in valid_prefixes):
                        issues.append(f"[{pmid}] RRID {i} has invalid format: {rrid_id}")
            elif isinstance(rrid, str):
                if not rrid.startswith('RRID:'):
                    issues.append(f"[{pmid}] RRID {i} should start with 'RRID:': {rrid}")

    # =========================
    # Cross-Reference Validation
    # =========================
    if paper.get('has_protocols') and not paper.get('protocols') and not paper.get('is_protocol'):
        issues.append(f"[{pmid}] has_protocols=True but no protocols found and not a protocol paper")

    if paper.get('has_github') and not paper.get('github_url'):
        issues.append(f"[{pmid}] has_github=True but no github_url")

    if paper.get('has_data') and not paper.get('repositories'):
        issues.append(f"[{pmid}] has_data=True but no repositories")

    # =========================
    # Post Type Validation
    # =========================
    post_type = paper.get('post_type')
    if post_type and post_type not in ['mh_paper', 'mh_protocol']:
        issues.append(f"[{pmid}] Invalid post_type: {post_type}")

    # Protocol type should exist if is_protocol
    if paper.get('is_protocol') and not paper.get('protocol_type'):
        # This is a warning, not error - some protocol papers might not have detected type
        pass  # issues.append(f"[{pmid}] is_protocol=True but no protocol_type set")

    return issues


def validate_tag_values(papers: List[Dict]) -> List[str]:
    """Validate that all tag values are in allowed sets. Returns list of issues."""
    issues = []
    unknown_tags = defaultdict(set)

    tag_validators = {
        'microscopy_techniques': VALID_MICROSCOPY_TECHNIQUES,
        'microscope_brands': VALID_MICROSCOPE_BRANDS,
        'organisms': VALID_ORGANISMS,
        'protocol_type': VALID_PROTOCOL_TYPES,
    }

    for paper in papers:
        pmid = paper.get('pmid', 'UNKNOWN')

        for field, valid_values in tag_validators.items():
            values = paper.get(field, [])

            # Handle single value fields
            if isinstance(values, str):
                values = [values] if values else []
            elif not isinstance(values, list):
                continue

            for value in values:
                if value and value not in valid_values:
                    unknown_tags[field].add(value)
                    # Only report first occurrence per tag

    # Report unknown tags
    for field, tags in unknown_tags.items():
        for tag in sorted(tags):
            issues.append(f"[TAG] Unknown {field}: '{tag}'")

    return issues


def validate_links(papers: List[Dict], sample_size: int = 50) -> List[str]:
    """Validate a sample of links are accessible. Returns list of issues."""
    try:
        import requests
    except ImportError:
        logger.warning("requests library not available, skipping link validation")
        return ["[LINK] requests library not installed, cannot validate links"]

    issues = []

    # Sample papers
    if len(papers) > sample_size:
        sampled = random.sample(papers, sample_size)
    else:
        sampled = papers

    logger.info(f"Validating links for {len(sampled)} papers...")

    def check_url(url: str, pmid: str, field: str) -> Optional[str]:
        """Check if URL is accessible."""
        try:
            response = requests.head(url, timeout=10, allow_redirects=True)
            if response.status_code >= 400:
                return f"[{pmid}] {field} link broken (HTTP {response.status_code}): {url}"
        except requests.exceptions.Timeout:
            return f"[{pmid}] {field} link timeout: {url}"
        except requests.exceptions.ConnectionError:
            return f"[{pmid}] {field} link connection error: {url}"
        except Exception as e:
            return f"[{pmid}] {field} link error: {url} - {str(e)[:50]}"
        return None

    # Check DOI and GitHub links (most important)
    urls_to_check = []
    for paper in sampled:
        pmid = paper.get('pmid', 'UNKNOWN')

        doi_url = paper.get('doi_url')
        if doi_url:
            urls_to_check.append((doi_url, pmid, 'DOI'))

        github_url = paper.get('github_url')
        if github_url:
            urls_to_check.append((github_url, pmid, 'GitHub'))

    # Use thread pool for parallel checking
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(check_url, url, pmid, field): (url, pmid, field)
            for url, pmid, field in urls_to_check
        }

        for future in as_completed(futures):
            result = future.result()
            if result:
                issues.append(result)

    return issues


def calculate_statistics(papers: List[Dict]) -> Dict[str, Any]:
    """Calculate comprehensive statistics about the dataset."""
    stats = {
        'total_papers': len(papers),
        'with_doi': 0,
        'with_pmc': 0,
        'with_abstract': 0,
        'with_methods': 0,
        'with_citations': 0,
        'total_citations': 0,
        'with_techniques': 0,
        'with_brands': 0,
        'with_fluorophores': 0,
        'with_organisms': 0,
        'with_protocols': 0,
        'with_repositories': 0,
        'with_github': 0,
        'with_rrids': 0,
        'with_affiliations': 0,
        'with_institutions': 0,
        'protocol_papers': 0,
        'by_year': defaultdict(int),
        'by_protocol_type': defaultdict(int),
        'technique_counts': defaultdict(int),
        'organism_counts': defaultdict(int),
    }

    for paper in papers:
        if paper.get('doi'):
            stats['with_doi'] += 1
        if paper.get('pmc_id'):
            stats['with_pmc'] += 1
        if paper.get('abstract') and len(str(paper.get('abstract', ''))) > 50:
            stats['with_abstract'] += 1
        if paper.get('methods') and len(str(paper.get('methods', ''))) > 100:
            stats['with_methods'] += 1

        citations = paper.get('citation_count', 0) or paper.get('citations', 0) or 0
        if citations:
            stats['with_citations'] += 1
            stats['total_citations'] += int(citations)

        if paper.get('microscopy_techniques'):
            stats['with_techniques'] += 1
            for tech in paper.get('microscopy_techniques', []):
                stats['technique_counts'][tech] += 1

        if paper.get('microscope_brands'):
            stats['with_brands'] += 1
        if paper.get('fluorophores'):
            stats['with_fluorophores'] += 1

        if paper.get('organisms'):
            stats['with_organisms'] += 1
            for org in paper.get('organisms', []):
                stats['organism_counts'][org] += 1

        if paper.get('protocols') or paper.get('has_protocols'):
            stats['with_protocols'] += 1
        if paper.get('repositories') or paper.get('has_data'):
            stats['with_repositories'] += 1
        if paper.get('github_url') or paper.get('has_github'):
            stats['with_github'] += 1
        if paper.get('rrids'):
            stats['with_rrids'] += 1
        if paper.get('affiliations'):
            stats['with_affiliations'] += 1
        if paper.get('institutions'):
            stats['with_institutions'] += 1

        if paper.get('is_protocol'):
            stats['protocol_papers'] += 1
            ptype = paper.get('protocol_type', 'Unknown')
            stats['by_protocol_type'][ptype] += 1

        year = paper.get('year')
        if year:
            stats['by_year'][int(year)] += 1

    return stats


def generate_report(issues: List[str], stats: Dict, output_file: str):
    """Generate a comprehensive validation report in Markdown format."""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# MicroHub Data Validation Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Summary
        f.write("## Summary\n\n")
        f.write(f"- **Total Papers:** {stats['total_papers']:,}\n")
        f.write(f"- **Total Issues Found:** {len(issues)}\n")
        f.write(f"- **Validation Status:** {'PASSED' if len(issues) == 0 else 'ISSUES FOUND'}\n\n")

        # Statistics
        f.write("## Dataset Statistics\n\n")
        f.write("### Coverage\n\n")
        f.write(f"| Field | Count | Percentage |\n")
        f.write(f"|-------|-------|------------|\n")

        total = stats['total_papers']
        coverage_fields = [
            ('DOI', 'with_doi'),
            ('PMC ID', 'with_pmc'),
            ('Abstract', 'with_abstract'),
            ('Methods', 'with_methods'),
            ('Citations', 'with_citations'),
            ('Techniques', 'with_techniques'),
            ('Microscope Brands', 'with_brands'),
            ('Fluorophores', 'with_fluorophores'),
            ('Organisms', 'with_organisms'),
            ('Protocols', 'with_protocols'),
            ('Repositories', 'with_repositories'),
            ('GitHub', 'with_github'),
            ('RRIDs', 'with_rrids'),
            ('Affiliations', 'with_affiliations'),
            ('Institutions', 'with_institutions'),
        ]

        for label, key in coverage_fields:
            count = stats.get(key, 0)
            pct = (count / total * 100) if total > 0 else 0
            f.write(f"| {label} | {count:,} | {pct:.1f}% |\n")

        f.write(f"\n**Total Citations:** {stats['total_citations']:,}\n")
        f.write(f"**Protocol Papers:** {stats['protocol_papers']:,}\n\n")

        # Top techniques
        if stats['technique_counts']:
            f.write("### Top Microscopy Techniques\n\n")
            sorted_techs = sorted(stats['technique_counts'].items(), key=lambda x: -x[1])[:15]
            for tech, count in sorted_techs:
                f.write(f"- {tech}: {count:,}\n")
            f.write("\n")

        # Top organisms
        if stats['organism_counts']:
            f.write("### Top Organisms\n\n")
            sorted_orgs = sorted(stats['organism_counts'].items(), key=lambda x: -x[1])[:10]
            for org, count in sorted_orgs:
                f.write(f"- {org}: {count:,}\n")
            f.write("\n")

        # Protocol types
        if stats['by_protocol_type']:
            f.write("### Protocol Types\n\n")
            for ptype, count in sorted(stats['by_protocol_type'].items(), key=lambda x: -x[1]):
                f.write(f"- {ptype}: {count:,}\n")
            f.write("\n")

        # Years distribution (last 10 years)
        if stats['by_year']:
            f.write("### Papers by Year (Recent)\n\n")
            sorted_years = sorted(stats['by_year'].items(), key=lambda x: -x[0])[:10]
            for year, count in sorted_years:
                f.write(f"- {year}: {count:,}\n")
            f.write("\n")

        # Issues
        f.write(f"## Issues Found: {len(issues)}\n\n")

        if not issues:
            f.write("No issues found.\n\n")
        else:
            # Group issues by type
            grouped = defaultdict(list)
            for issue in issues:
                # Extract issue type from message
                if '] Missing required' in issue:
                    issue_type = 'Missing Required Fields'
                elif '] Invalid DOI' in issue:
                    issue_type = 'Invalid DOI Format'
                elif '] Invalid year' in issue:
                    issue_type = 'Invalid Year'
                elif '] Invalid URL' in issue:
                    issue_type = 'Invalid URL Format'
                elif '] Field ' in issue and 'should be array' in issue:
                    issue_type = 'Invalid Field Type'
                elif '[TAG]' in issue:
                    issue_type = 'Unknown Tag Values'
                elif '[LINK]' in issue:
                    issue_type = 'Broken Links'
                elif 'has_protocols=True' in issue or 'has_github=True' in issue or 'has_data=True' in issue:
                    issue_type = 'Cross-Reference Mismatch'
                else:
                    issue_type = 'Other'

                grouped[issue_type].append(issue)

            for issue_type, type_issues in sorted(grouped.items()):
                f.write(f"### {issue_type} ({len(type_issues)})\n\n")

                # Show first 20 issues of each type
                for issue in type_issues[:20]:
                    f.write(f"- {issue}\n")

                if len(type_issues) > 20:
                    f.write(f"- ... and {len(type_issues) - 20} more\n")

                f.write("\n")

        # Recommendations
        f.write("## Recommendations\n\n")

        if stats['with_doi'] < total * 0.9:
            f.write("- Consider enriching papers without DOIs\n")
        if stats['with_techniques'] < total * 0.5:
            f.write("- Many papers lack microscopy technique tags - consider re-running extraction\n")
        if stats['with_affiliations'] < total * 0.7:
            f.write("- Many papers lack affiliations - verify scraper is extracting from PubMed XML\n")
        if stats['with_institutions'] < stats['with_affiliations'] * 0.8:
            f.write("- Institution extraction rate is low - review KNOWN_INSTITUTIONS dictionary\n")

        if len(issues) == 0:
            f.write("- Data looks good! Ready for WordPress import.\n")

        f.write("\n---\n")
        f.write(f"*Report generated by validate_microhub_data.py v1.0*\n")

    logger.info(f"Report saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='MicroHub Data Validation Suite - Validate scraped data before WordPress import'
    )
    parser.add_argument('--input', '-i', required=True,
                        help='Input directory containing JSON files or single JSON file')
    parser.add_argument('--output', '-o', default='validation_report.md',
                        help='Output report file (default: validation_report.md)')
    parser.add_argument('--check-links', action='store_true',
                        help='Validate URLs are accessible (slower)')
    parser.add_argument('--sample', type=int, default=50,
                        help='Number of papers to sample for link checking (default: 50)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load all papers
    papers = []

    if os.path.isfile(args.input):
        logger.info(f"Loading {args.input}...")
        papers = load_json_file(args.input)
    elif os.path.isdir(args.input):
        json_files = glob.glob(os.path.join(args.input, '*.json'))
        logger.info(f"Found {len(json_files)} JSON files in {args.input}")

        for json_file in json_files:
            logger.info(f"Loading {os.path.basename(json_file)}...")
            file_papers = load_json_file(json_file)
            papers.extend(file_papers)
    else:
        logger.error(f"Input not found: {args.input}")
        return 1

    if not papers:
        logger.error("No papers loaded!")
        return 1

    logger.info(f"Loaded {len(papers):,} papers total")

    # Run validations
    all_issues = []

    # 1. Validate individual papers
    logger.info("Validating paper data...")
    for paper in papers:
        issues = validate_paper(paper)
        all_issues.extend(issues)

    # 2. Validate tag values
    logger.info("Validating tag values...")
    tag_issues = validate_tag_values(papers)
    all_issues.extend(tag_issues)

    # 3. Validate links (optional)
    if args.check_links:
        logger.info("Validating links (this may take a while)...")
        link_issues = validate_links(papers, args.sample)
        all_issues.extend(link_issues)

    # 4. Calculate statistics
    logger.info("Calculating statistics...")
    stats = calculate_statistics(papers)

    # 5. Generate report
    logger.info("Generating report...")
    generate_report(all_issues, stats, args.output)

    # Print summary
    print(f"\n{'='*60}")
    print(f"VALIDATION COMPLETE")
    print(f"{'='*60}")
    print(f"Total papers: {len(papers):,}")
    print(f"Issues found: {len(all_issues)}")
    print(f"Report saved: {args.output}")
    print(f"{'='*60}\n")

    return 0 if len(all_issues) == 0 else 1


if __name__ == '__main__':
    exit(main())
