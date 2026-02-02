#!/usr/bin/env python3
"""
MICROHUB JSON TO TEXT CONVERTER
===============================
Convert JSON paper files to plain text format for AI training, search indexing, or analysis.

Usage:
  python microhub_json_to_text.py                           # Convert all chunk files
  python microhub_json_to_text.py --input my_papers.json    # Convert specific file
  python microhub_json_to_text.py --format markdown         # Output as markdown
  python microhub_json_to_text.py --format simple           # Simple text format
  python microhub_json_to_text.py --chunk-size 500          # Papers per text file (default: 1000)
  python microhub_json_to_text.py --one-file                # Combine all into one file
"""

import json
import argparse
import glob
import os
import logging
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


def safe_get(paper: Dict, key: str, default: Any = '') -> Any:
    """Safely get a value from paper dict."""
    value = paper.get(key)
    return value if value is not None else default


def format_list(items: List, separator: str = ', ') -> str:
    """Format a list as a string."""
    if not items:
        return ''
    if isinstance(items, list):
        # Handle list of dicts
        if items and isinstance(items[0], dict):
            return separator.join(str(item.get('name', item.get('title', str(item)))) for item in items)
        return separator.join(str(item) for item in items)
    return str(items)


def paper_to_simple_text(paper: Dict) -> str:
    """Convert paper to simple text format."""
    lines = []
    
    # Title
    title = safe_get(paper, 'title', 'Untitled')
    lines.append(f"TITLE: {title}")
    
    # Authors
    authors = safe_get(paper, 'authors', '')
    if authors:
        lines.append(f"AUTHORS: {authors}")
    
    # Journal and Year
    journal = safe_get(paper, 'journal', '')
    year = safe_get(paper, 'year', '')
    if journal or year:
        lines.append(f"JOURNAL: {journal} ({year})" if year else f"JOURNAL: {journal}")
    
    # Identifiers
    pmid = safe_get(paper, 'pmid')
    doi = safe_get(paper, 'doi')
    if pmid:
        lines.append(f"PMID: {pmid}")
    if doi:
        lines.append(f"DOI: {doi}")
    
    # Citations
    citations = safe_get(paper, 'citation_count', 0)
    if citations:
        lines.append(f"CITATIONS: {citations}")
    
    # Abstract
    abstract = safe_get(paper, 'abstract', '')
    if abstract:
        lines.append(f"\nABSTRACT:\n{abstract}")
    
    # Methods
    methods = safe_get(paper, 'methods', '')
    if methods and len(methods) > 50:
        lines.append(f"\nMETHODS:\n{methods}")
    
    # Microscopy Techniques
    techniques = safe_get(paper, 'microscopy_techniques', [])
    if techniques:
        lines.append(f"\nMICROSCOPY TECHNIQUES: {format_list(techniques)}")
    
    # Software
    software = safe_get(paper, 'software', [])
    if software:
        lines.append(f"SOFTWARE: {format_list(software)}")
    
    # Microscope Info
    brands = safe_get(paper, 'microscope_brands', [])
    models = safe_get(paper, 'microscope_models', [])
    if brands:
        lines.append(f"MICROSCOPE BRANDS: {format_list(brands)}")
    if models:
        lines.append(f"MICROSCOPE MODELS: {format_list(models)}")
    
    # Fluorophores
    fluorophores = safe_get(paper, 'fluorophores', [])
    if fluorophores:
        lines.append(f"FLUOROPHORES: {format_list(fluorophores)}")
    
    # Organisms
    organisms = safe_get(paper, 'organisms', [])
    if organisms:
        lines.append(f"ORGANISMS: {format_list(organisms)}")
    
    # Sample Preparation
    sample_prep = safe_get(paper, 'sample_preparation', [])
    if sample_prep:
        lines.append(f"SAMPLE PREPARATION: {format_list(sample_prep)}")
    
    # URLs
    doi_url = safe_get(paper, 'doi_url')
    pubmed_url = safe_get(paper, 'pubmed_url')
    github_url = safe_get(paper, 'github_url')
    if doi_url:
        lines.append(f"DOI URL: {doi_url}")
    if pubmed_url:
        lines.append(f"PUBMED URL: {pubmed_url}")
    if github_url:
        lines.append(f"GITHUB: {github_url}")
    
    lines.append("\n" + "=" * 80 + "\n")
    
    return '\n'.join(lines)


def paper_to_markdown(paper: Dict) -> str:
    """Convert paper to markdown format."""
    lines = []
    
    # Title as heading
    title = safe_get(paper, 'title', 'Untitled')
    lines.append(f"# {title}\n")
    
    # Authors
    authors = safe_get(paper, 'authors', '')
    if authors:
        lines.append(f"**Authors:** {authors}\n")
    
    # Journal and Year
    journal = safe_get(paper, 'journal', '')
    year = safe_get(paper, 'year', '')
    citations = safe_get(paper, 'citation_count', 0)
    
    meta = []
    if journal:
        meta.append(f"*{journal}*")
    if year:
        meta.append(f"({year})")
    if citations:
        meta.append(f"| **{citations} citations**")
    if meta:
        lines.append(' '.join(meta) + '\n')
    
    # Identifiers
    pmid = safe_get(paper, 'pmid')
    doi = safe_get(paper, 'doi')
    doi_url = safe_get(paper, 'doi_url')
    
    ids = []
    if pmid:
        ids.append(f"PMID: [{pmid}](https://pubmed.ncbi.nlm.nih.gov/{pmid}/)")
    if doi and doi_url:
        ids.append(f"DOI: [{doi}]({doi_url})")
    elif doi:
        ids.append(f"DOI: {doi}")
    if ids:
        lines.append(' | '.join(ids) + '\n')
    
    # Abstract
    abstract = safe_get(paper, 'abstract', '')
    if abstract:
        lines.append(f"## Abstract\n\n{abstract}\n")
    
    # Methods
    methods = safe_get(paper, 'methods', '')
    if methods and len(methods) > 50:
        lines.append(f"## Methods\n\n{methods}\n")
    
    # Microscopy Details
    techniques = safe_get(paper, 'microscopy_techniques', [])
    software = safe_get(paper, 'software', [])
    brands = safe_get(paper, 'microscope_brands', [])
    fluorophores = safe_get(paper, 'fluorophores', [])
    
    if techniques or software or brands or fluorophores:
        lines.append("## Microscopy Details\n")
        if techniques:
            lines.append(f"- **Techniques:** {format_list(techniques)}")
        if software:
            lines.append(f"- **Software:** {format_list(software)}")
        if brands:
            lines.append(f"- **Microscope Brands:** {format_list(brands)}")
        if fluorophores:
            lines.append(f"- **Fluorophores:** {format_list(fluorophores)}")
        lines.append("")
    
    # Organisms and Samples
    organisms = safe_get(paper, 'organisms', [])
    sample_prep = safe_get(paper, 'sample_preparation', [])
    cell_lines = safe_get(paper, 'cell_lines', [])
    
    if organisms or sample_prep or cell_lines:
        lines.append("## Biological Details\n")
        if organisms:
            lines.append(f"- **Organisms:** {format_list(organisms)}")
        if cell_lines:
            lines.append(f"- **Cell Lines:** {format_list(cell_lines)}")
        if sample_prep:
            lines.append(f"- **Sample Preparation:** {format_list(sample_prep)}")
        lines.append("")
    
    # Resources
    github_url = safe_get(paper, 'github_url')
    protocols = safe_get(paper, 'protocols', [])
    repositories = safe_get(paper, 'repositories', [])
    
    if github_url or protocols or repositories:
        lines.append("## Resources\n")
        if github_url:
            lines.append(f"- **GitHub:** [{github_url}]({github_url})")
        if protocols:
            lines.append(f"- **Protocols:** {format_list(protocols)}")
        if repositories:
            lines.append(f"- **Repositories:** {format_list(repositories)}")
        lines.append("")
    
    lines.append("---\n")
    
    return '\n'.join(lines)


def convert_json_to_text(input_files: List[str], output_dir: str, format_type: str = 'simple', 
                         one_file: bool = False, chunk_size: int = 1000) -> int:
    """Convert JSON files to text format with chunking."""
    
    logger.info(f"Converting {len(input_files)} JSON file(s) to {format_type} text format")
    logger.info(f"Chunk size: {chunk_size:,} papers per text file")
    
    os.makedirs(output_dir, exist_ok=True)
    
    total_papers = 0
    all_text = []
    chunk_num = 1
    current_chunk = []
    created_files = []
    ext = '.md' if format_type == 'markdown' else '.txt'
    
    def save_chunk(texts: List[str], chunk_number: int) -> str:
        """Save a chunk of text to file."""
        filename = os.path.join(output_dir, f"microhub_papers_chunk_{chunk_number}{ext}")
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(texts))
        return filename
    
    for json_file in input_files:
        logger.info(f"Processing: {json_file}")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            papers = json.load(f)
        
        if not isinstance(papers, list):
            papers = [papers]
        
        for paper in papers:
            if format_type == 'markdown':
                text = paper_to_markdown(paper)
            else:
                text = paper_to_simple_text(paper)
            
            total_papers += 1
            
            if one_file:
                all_text.append(text)
            else:
                current_chunk.append(text)
                
                # Save chunk if full
                if len(current_chunk) >= chunk_size:
                    filename = save_chunk(current_chunk, chunk_num)
                    size_mb = os.path.getsize(filename) / 1024 / 1024
                    logger.info(f"  Saved chunk {chunk_num}: {filename} ({len(current_chunk):,} papers, {size_mb:.1f} MB)")
                    created_files.append(filename)
                    chunk_num += 1
                    current_chunk = []
    
    # Save remaining papers
    if current_chunk and not one_file:
        filename = save_chunk(current_chunk, chunk_num)
        size_mb = os.path.getsize(filename) / 1024 / 1024
        logger.info(f"  Saved chunk {chunk_num}: {filename} ({len(current_chunk):,} papers, {size_mb:.1f} MB)")
        created_files.append(filename)
    
    # Save combined file if requested
    if one_file and all_text:
        ext = '.md' if format_type == 'markdown' else '.txt'
        output_file = os.path.join(output_dir, f"microhub_all_papers{ext}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(all_text))
        
        size_mb = os.path.getsize(output_file) / 1024 / 1024
        logger.info(f"Saved combined file: {output_file} ({total_papers:,} papers, {size_mb:.1f} MB)")
    
    logger.info(f"\nTotal papers converted: {total_papers:,}")
    return total_papers


def main():
    parser = argparse.ArgumentParser(description='Convert MicroHub JSON files to text format')
    parser.add_argument('--input', '-i', help='Input JSON file (default: all chunk files)')
    parser.add_argument('--output-dir', '-o', default='text_export', help='Output directory')
    parser.add_argument('--format', '-f', choices=['simple', 'markdown'], default='simple',
                        help='Output format: simple (plain text) or markdown')
    parser.add_argument('--chunk-size', type=int, default=1000,
                        help='Papers per text file (default: 1000)')
    parser.add_argument('--one-file', action='store_true', 
                        help='Combine all papers into one file')
    parser.add_argument('--pattern', default='microhub_papers_v4_chunk_*.json',
                        help='Glob pattern to find JSON files')
    
    args = parser.parse_args()
    
    # Find input files
    if args.input:
        input_files = [args.input]
    else:
        input_files = sorted(glob.glob(args.pattern))
        if not input_files:
            # Try other common patterns
            input_files = sorted(glob.glob('*_chunk_*.json'))
        if not input_files:
            input_files = sorted(glob.glob('microhub*.json'))
    
    if not input_files:
        logger.error("No JSON files found! Use --input to specify a file or --pattern for a glob pattern.")
        return
    
    logger.info("=" * 60)
    logger.info("MICROHUB JSON TO TEXT CONVERTER")
    logger.info("=" * 60)
    logger.info(f"Found {len(input_files)} JSON file(s)")
    logger.info(f"Output format: {args.format}")
    logger.info(f"Output directory: {args.output_dir}")
    logger.info("")
    
    convert_json_to_text(
        input_files=input_files,
        output_dir=args.output_dir,
        format_type=args.format,
        one_file=args.one_file,
        chunk_size=args.chunk_size
    )


if __name__ == '__main__':
    main()
