#!/usr/bin/env python3
"""
MicroHub Metrics Update Script
==============================

Updates citation counts and GitHub metrics for existing papers without
re-scraping everything. Designed to run periodically (cron job) or manually.

Usage:
    python update_metrics.py papers.json --output updated_papers.json
    python update_metrics.py papers.json --in-place
    python update_metrics.py papers.json --citations-only
    python update_metrics.py papers.json --github-only

Environment Variables:
    GITHUB_TOKEN - GitHub API token for higher rate limits (5000/hour vs 60/hour)
    SEMANTIC_SCHOLAR_API_KEY - Optional API key for Semantic Scholar

Features:
    - Updates citation counts from Semantic Scholar API
    - Updates GitHub repository metrics (stars, forks, health, last commit)
    - Preserves all existing tags and enrichment data
    - Progress tracking and resumable updates
    - Rate limiting to respect API limits
"""

import json
import os
import sys
import time
import argparse
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Try to import requests
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("Error: 'requests' library required. Install with: pip install requests")
    sys.exit(1)

# API Configuration
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
SEMANTIC_SCHOLAR_API_KEY = os.environ.get('SEMANTIC_SCHOLAR_API_KEY', '')

# Rate limiting
GITHUB_DELAY = 0.5  # seconds between GitHub API calls
CITATION_DELAY = 1.0  # seconds between citation API calls

# Statistics
stats = {
    'papers_processed': 0,
    'citations_updated': 0,
    'github_updated': 0,
    'errors': 0,
    'skipped': 0,
}


def log(message: str, level: str = 'INFO'):
    """Print timestamped log message."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] [{level}] {message}")


# ============================================================================
# CITATION UPDATES
# ============================================================================

def fetch_citations_semantic_scholar(doi: str = None, pubmed_id: str = None) -> Optional[int]:
    """
    Fetch citation count from Semantic Scholar API.

    Supports lookup by DOI or PubMed ID.
    """
    if not doi and not pubmed_id:
        return None

    headers = {}
    if SEMANTIC_SCHOLAR_API_KEY:
        headers['x-api-key'] = SEMANTIC_SCHOLAR_API_KEY

    # Try DOI first
    if doi:
        url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=citationCount"
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                return data.get('citationCount')
            elif resp.status_code == 429:
                log("Semantic Scholar rate limited, waiting...", "WARN")
                time.sleep(60)
                return fetch_citations_semantic_scholar(doi, pubmed_id)
        except Exception as e:
            log(f"Semantic Scholar DOI lookup error: {e}", "ERROR")

    # Try PubMed ID
    if pubmed_id:
        url = f"https://api.semanticscholar.org/graph/v1/paper/PMID:{pubmed_id}?fields=citationCount"
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                return data.get('citationCount')
        except Exception as e:
            log(f"Semantic Scholar PMID lookup error: {e}", "ERROR")

    return None


def fetch_citations_crossref(doi: str) -> Optional[int]:
    """
    Fetch citation count from CrossRef API (fallback).
    """
    if not doi:
        return None

    url = f"https://api.crossref.org/works/{doi}"
    headers = {'User-Agent': 'MicroHub/1.0 (https://microhub.io; mailto:admin@microhub.io)'}

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            return data.get('message', {}).get('is-referenced-by-count')
    except Exception as e:
        log(f"CrossRef lookup error for {doi}: {e}", "ERROR")

    return None


def update_paper_citations(paper: Dict) -> Tuple[Dict, bool]:
    """
    Update citation count for a paper.

    Returns:
        Tuple of (updated_paper, was_updated)
    """
    doi = paper.get('doi', '').strip()
    pubmed_id = paper.get('pubmed_id', '').strip()
    current_citations = int(paper.get('citation_count', 0) or 0)

    if not doi and not pubmed_id:
        return paper, False

    # Try Semantic Scholar first (more comprehensive)
    new_citations = fetch_citations_semantic_scholar(doi, pubmed_id)

    # Fallback to CrossRef if Semantic Scholar fails
    if new_citations is None and doi:
        new_citations = fetch_citations_crossref(doi)

    if new_citations is not None and new_citations != current_citations:
        paper['citation_count'] = new_citations
        paper['citations_updated'] = datetime.now().isoformat()
        log(f"  Citations: {current_citations} -> {new_citations}")
        return paper, True

    return paper, False


# ============================================================================
# GITHUB UPDATES
# ============================================================================

def fetch_github_repo_metrics(full_name: str) -> Optional[Dict]:
    """
    Fetch repository metrics from GitHub API.

    Args:
        full_name: Repository full name (e.g., "owner/repo")

    Returns:
        Dict with metrics or None if failed
    """
    if not full_name or '/' not in full_name:
        return None

    headers = {'Accept': 'application/vnd.github.v3+json'}
    if GITHUB_TOKEN:
        headers['Authorization'] = f'token {GITHUB_TOKEN}'

    try:
        # Main repo info
        resp = requests.get(
            f'https://api.github.com/repos/{full_name}',
            headers=headers,
            timeout=15
        )

        if resp.status_code == 404:
            return {'exists': False, 'is_archived': True}

        if resp.status_code == 403:
            log(f"GitHub rate limited for {full_name}", "WARN")
            time.sleep(60)
            return fetch_github_repo_metrics(full_name)

        if resp.status_code != 200:
            return None

        data = resp.json()

        metrics = {
            'exists': True,
            'full_name': data.get('full_name', full_name),
            'description': (data.get('description') or '')[:500],
            'stars': data.get('stargazers_count', 0),
            'forks': data.get('forks_count', 0),
            'open_issues': data.get('open_issues_count', 0),
            'language': data.get('language') or '',
            'license': data.get('license', {}).get('spdx_id') if data.get('license') else '',
            'topics': data.get('topics', []),
            'is_archived': data.get('archived', False),
            'updated_at': data.get('updated_at', ''),
            'pushed_at': data.get('pushed_at', ''),
        }

        # Get last commit date
        try:
            commits_resp = requests.get(
                f'https://api.github.com/repos/{full_name}/commits',
                headers=headers,
                params={'per_page': 1},
                timeout=10
            )
            if commits_resp.status_code == 200:
                commits = commits_resp.json()
                if commits:
                    metrics['last_commit_date'] = commits[0].get('commit', {}).get('committer', {}).get('date', '')
        except:
            pass

        # Get latest release
        try:
            release_resp = requests.get(
                f'https://api.github.com/repos/{full_name}/releases/latest',
                headers=headers,
                timeout=10
            )
            if release_resp.status_code == 200:
                release = release_resp.json()
                metrics['last_release'] = release.get('tag_name', '')
                metrics['last_release_date'] = release.get('published_at', '')
        except:
            pass

        # Compute health score
        metrics['health_score'] = compute_health_score(metrics)

        return metrics

    except Exception as e:
        log(f"GitHub API error for {full_name}: {e}", "ERROR")
        return None


def compute_health_score(metrics: Dict) -> int:
    """Compute repository health score (0-100)."""
    if not metrics.get('exists', True):
        return 0
    if metrics.get('is_archived', False):
        return 10

    score = 0

    # Stars (up to 25 points)
    stars = metrics.get('stars', 0)
    if stars >= 1000: score += 25
    elif stars >= 500: score += 22
    elif stars >= 100: score += 18
    elif stars >= 50: score += 14
    elif stars >= 10: score += 10
    elif stars >= 1: score += 5

    # Recent activity (up to 30 points)
    last_commit = metrics.get('last_commit_date', '') or metrics.get('pushed_at', '')
    if last_commit:
        try:
            commit_date = datetime.fromisoformat(last_commit.replace('Z', '+00:00'))
            now = datetime.now(commit_date.tzinfo) if commit_date.tzinfo else datetime.now()
            days_since = (now - commit_date).days

            if days_since <= 30: score += 30
            elif days_since <= 90: score += 25
            elif days_since <= 180: score += 20
            elif days_since <= 365: score += 12
            elif days_since <= 730: score += 5
        except:
            pass

    # Forks (up to 15 points)
    forks = metrics.get('forks', 0)
    if forks >= 100: score += 15
    elif forks >= 50: score += 12
    elif forks >= 10: score += 8
    elif forks >= 1: score += 3

    # Has description (5 points)
    if metrics.get('description'):
        score += 5

    # Has license (5 points)
    if metrics.get('license'):
        score += 5

    # Has topics (5 points)
    if metrics.get('topics'):
        score += 5

    # Has release (10 points)
    if metrics.get('last_release'):
        score += 10

    return min(100, score)


def update_github_tools(paper: Dict) -> Tuple[Dict, bool]:
    """
    Update GitHub tool metrics for a paper.

    Returns:
        Tuple of (updated_paper, was_updated)
    """
    github_tools = paper.get('github_tools', [])
    if not github_tools:
        return paper, False

    updated = False

    for tool in github_tools:
        full_name = tool.get('full_name', '')
        if not full_name:
            continue

        metrics = fetch_github_repo_metrics(full_name)
        if not metrics:
            continue

        # Update tool with new metrics
        old_stars = tool.get('stars', 0)
        new_stars = metrics.get('stars', old_stars)

        tool['stars'] = new_stars
        tool['forks'] = metrics.get('forks', tool.get('forks', 0))
        tool['open_issues'] = metrics.get('open_issues', tool.get('open_issues', 0))
        tool['health_score'] = metrics.get('health_score', tool.get('health_score', 0))
        tool['is_archived'] = metrics.get('is_archived', tool.get('is_archived', False))
        tool['last_commit_date'] = metrics.get('last_commit_date', tool.get('last_commit_date', ''))
        tool['last_release'] = metrics.get('last_release', tool.get('last_release', ''))

        # Update description/language if missing
        if not tool.get('description') and metrics.get('description'):
            tool['description'] = metrics['description']
        if not tool.get('language') and metrics.get('language'):
            tool['language'] = metrics['language']
        if not tool.get('license') and metrics.get('license'):
            tool['license'] = metrics['license']
        if not tool.get('topics') and metrics.get('topics'):
            tool['topics'] = metrics['topics']

        if new_stars != old_stars:
            log(f"    {full_name}: {old_stars} -> {new_stars} stars")
            updated = True

        time.sleep(GITHUB_DELAY)

    if updated:
        paper['github_tools'] = github_tools
        paper['github_updated'] = datetime.now().isoformat()

    return paper, updated


# ============================================================================
# MAIN UPDATE LOGIC
# ============================================================================

def update_paper(paper: Dict, update_citations: bool = True, update_github: bool = True) -> Dict:
    """
    Update a single paper's metrics.
    """
    title = paper.get('title', 'Unknown')[:50]
    log(f"Processing: {title}...")

    stats['papers_processed'] += 1

    # Update citations
    if update_citations:
        paper, citations_updated = update_paper_citations(paper)
        if citations_updated:
            stats['citations_updated'] += 1
        time.sleep(CITATION_DELAY)

    # Update GitHub tools
    if update_github:
        paper, github_updated = update_github_tools(paper)
        if github_updated:
            stats['github_updated'] += 1

    return paper


def update_papers_file(
    input_file: str,
    output_file: str = None,
    update_citations: bool = True,
    update_github: bool = True,
    limit: int = None,
    skip: int = 0
) -> None:
    """
    Update all papers in a JSON file.
    """
    # Load papers
    log(f"Loading papers from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle both array and object formats
    if isinstance(data, list):
        papers = data
        is_array = True
    elif isinstance(data, dict) and 'papers' in data:
        papers = data['papers']
        is_array = False
    else:
        log("Unknown file format", "ERROR")
        return

    total = len(papers)
    log(f"Found {total} papers")

    if skip > 0:
        log(f"Skipping first {skip} papers")
        papers = papers[skip:]

    if limit:
        log(f"Limiting to {limit} papers")
        papers = papers[:limit]

    # Update each paper
    updated_papers = []
    for i, paper in enumerate(papers):
        try:
            updated_paper = update_paper(paper, update_citations, update_github)
            updated_papers.append(updated_paper)
        except Exception as e:
            log(f"Error updating paper: {e}", "ERROR")
            stats['errors'] += 1
            updated_papers.append(paper)  # Keep original on error

        # Progress update every 10 papers
        if (i + 1) % 10 == 0:
            log(f"Progress: {i + 1}/{len(papers)} papers processed")

    # Reconstruct output data
    if is_array:
        output_data = updated_papers
    else:
        data['papers'] = updated_papers
        data['last_updated'] = datetime.now().isoformat()
        output_data = data

    # Write output
    output_path = output_file or input_file
    log(f"Writing updated papers to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    # Print summary
    log("=" * 50)
    log("UPDATE COMPLETE")
    log(f"Papers processed: {stats['papers_processed']}")
    log(f"Citations updated: {stats['citations_updated']}")
    log(f"GitHub tools updated: {stats['github_updated']}")
    log(f"Errors: {stats['errors']}")


def main():
    parser = argparse.ArgumentParser(
        description='Update citation counts and GitHub metrics for MicroHub papers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Update all metrics, save to new file
    python update_metrics.py papers.json --output updated_papers.json

    # Update in place
    python update_metrics.py papers.json --in-place

    # Only update citations
    python update_metrics.py papers.json --citations-only --output updated.json

    # Only update GitHub metrics
    python update_metrics.py papers.json --github-only --output updated.json

    # Process first 100 papers
    python update_metrics.py papers.json --limit 100 --output updated.json

    # Resume from paper 500
    python update_metrics.py papers.json --skip 500 --output updated.json

Environment Variables:
    GITHUB_TOKEN              GitHub API token for higher rate limits
    SEMANTIC_SCHOLAR_API_KEY  Semantic Scholar API key (optional)
        """
    )

    parser.add_argument('input_file', help='Input JSON file with papers')
    parser.add_argument('--output', '-o', help='Output JSON file (default: prints to stdout)')
    parser.add_argument('--in-place', '-i', action='store_true', help='Update input file in place')
    parser.add_argument('--citations-only', action='store_true', help='Only update citation counts')
    parser.add_argument('--github-only', action='store_true', help='Only update GitHub metrics')
    parser.add_argument('--limit', type=int, help='Limit number of papers to process')
    parser.add_argument('--skip', type=int, default=0, help='Skip first N papers')

    args = parser.parse_args()

    # Validate arguments
    if not os.path.exists(args.input_file):
        print(f"Error: Input file not found: {args.input_file}")
        sys.exit(1)

    output_file = args.input_file if args.in_place else args.output
    if not output_file:
        print("Error: Must specify --output or --in-place")
        sys.exit(1)

    update_citations = not args.github_only
    update_github = not args.citations_only

    # Check for API tokens
    if update_github and not GITHUB_TOKEN:
        log("Warning: No GITHUB_TOKEN set. Rate limited to 60 requests/hour.", "WARN")

    # Run update
    update_papers_file(
        args.input_file,
        output_file,
        update_citations=update_citations,
        update_github=update_github,
        limit=args.limit,
        skip=args.skip
    )


if __name__ == '__main__':
    main()
