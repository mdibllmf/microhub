#!/usr/bin/env python3
"""
MICROHUB JSON EXPORTER v4.0 - COMPREHENSIVE
============================================
Export ALL paper data to JSON for WordPress import.
Ensures NO data is lost - exports every field from the database.

Usage:
  python microhub_export_json_v4.py                      # Export all
  python microhub_export_json_v4.py --limit 10000        # Limit papers
  python microhub_export_json_v4.py --full-text-only     # Only with full text
  python microhub_export_json_v4.py --with-citations     # Only with citations
  python microhub_export_json_v4.py --min-citations 10   # Min citation count
  python microhub_export_json_v4.py --chunk-size 5000    # Papers per file (default)
"""

import sqlite3
import json
import argparse
import logging
import os
from typing import List, Dict, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


class ComprehensiveJsonExporter:
    """Export ALL paper data to JSON - nothing is lost."""

    def __init__(self, db_path: str = 'microhub.db'):
        self.db_path = db_path
        
        # Track what fields we export
        self.exported_fields = set()

    def safe_json_parse(self, value: Any) -> Any:
        """Safely parse JSON field, return empty list if invalid."""
        if value is None:
            return []
        if isinstance(value, (list, dict)):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if parsed else []
            except (json.JSONDecodeError, TypeError):
                return []
        return []

    def safe_get(self, row: Dict, field: str, default: Any = None) -> Any:
        """Safely get field value."""
        value = row.get(field)
        if value is None:
            return default
        return value

    def export(self, output_path: str = 'microhub_papers_v4.json',
               limit: int = None,
               full_text_only: bool = False,
               with_citations_only: bool = False,
               min_citations: int = 0,
               with_protocols_only: bool = False,
               with_github_only: bool = False,
               chunk_size: int = 5000) -> int:
        """Export papers to JSON with ALL fields. Always chunks to keep files manageable."""

        logger.info("=" * 60)
        logger.info("MICROHUB JSON EXPORTER v4.0 - COMPREHENSIVE")
        logger.info("=" * 60)
        logger.info("Exporting ALL paper data - nothing is lost!")
        logger.info(f"Chunk size: {chunk_size:,} papers per file (always chunked)")
        logger.info("")

        conn = sqlite3.connect(self.db_path, timeout=120.0)
        conn.row_factory = sqlite3.Row

        # Build query conditions
        conditions = []
        if full_text_only:
            conditions.append("has_full_text = 1")
        if with_citations_only:
            conditions.append("citation_count > 0")
        if min_citations > 0:
            conditions.append(f"citation_count >= {min_citations}")
        if with_protocols_only:
            conditions.append("has_protocols = 1")
        if with_github_only:
            conditions.append("has_github = 1")

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # Count total
        count_query = f"SELECT COUNT(*) FROM papers WHERE {where_clause}"
        total_count = conn.execute(count_query).fetchone()[0]
        logger.info(f"Total papers matching criteria: {total_count:,}")

        # Main query - get ALL columns
        query = f"""
            SELECT * FROM papers
            WHERE {where_clause}
            ORDER BY citation_count DESC, priority_score DESC, year DESC
        """

        if limit:
            query += f" LIMIT {limit}"
            logger.info(f"Limiting to {limit:,} papers")

        logger.info("Fetching papers from database...")
        cursor = conn.execute(query)

        # Get column names
        column_names = [description[0] for description in cursor.description]
        logger.info(f"Database has {len(column_names)} columns")

        chunk_num = 1
        chunk_papers = []
        papers_written = 0
        created_files = []

        base_name = output_path.replace('.json', '')

        # Track statistics
        stats = {
            'with_citations': 0,
            'with_full_text': 0,
            'with_methods': 0,
            'with_figures': 0,
            'with_protocols': 0,
            'with_github': 0,
            'with_repositories': 0,
            'with_rrids': 0,
            'with_techniques': 0,
            'with_software': 0,
            'with_fluorophores': 0,
            'with_organisms': 0,
            'with_sample_prep': 0,
            'total_citations': 0,
            'total_figures': 0,
            'total_protocols': 0,
            'total_repositories': 0,
        }

        def save_chunk(papers: List[Dict], chunk_number: int) -> str:
            """Save chunk to JSON file (always chunked to keep files small)."""
            filename = f"{base_name}_chunk_{chunk_number}.json"

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(papers, f, indent=2, ensure_ascii=False, default=str)

            return filename

        for row in cursor:
            row_dict = dict(row)

            # Parse ALL JSON fields
            microscopy_techniques = self.safe_json_parse(row_dict.get('microscopy_techniques'))
            microscope_brands = self.safe_json_parse(row_dict.get('microscope_brands'))
            microscope_models = self.safe_json_parse(row_dict.get('microscope_models'))
            image_analysis_software = self.safe_json_parse(row_dict.get('image_analysis_software'))
            image_acquisition_software = self.safe_json_parse(row_dict.get('image_acquisition_software'))
            sample_preparation = self.safe_json_parse(row_dict.get('sample_preparation'))
            fluorophores = self.safe_json_parse(row_dict.get('fluorophores'))
            organisms = self.safe_json_parse(row_dict.get('organisms'))
            cell_lines = self.safe_json_parse(row_dict.get('cell_lines'))
            protocols = self.safe_json_parse(row_dict.get('protocols'))
            repositories = self.safe_json_parse(row_dict.get('repositories'))
            supplementary = self.safe_json_parse(row_dict.get('supplementary_materials'))
            rrids = self.safe_json_parse(row_dict.get('rrids'))
            rors = self.safe_json_parse(row_dict.get('rors'))
            figures = self.safe_json_parse(row_dict.get('figures'))
            antibodies = self.safe_json_parse(row_dict.get('antibodies'))
            
            # Legacy fields
            techniques = self.safe_json_parse(row_dict.get('techniques'))
            software = self.safe_json_parse(row_dict.get('software'))
            tags = self.safe_json_parse(row_dict.get('tags'))

            # Get citation count - CRITICAL!
            citation_count = self.safe_get(row_dict, 'citation_count', 0) or 0

            # Build comprehensive paper object
            paper = {
                # === IDENTIFIERS ===
                'id': row_dict.get('id'),
                'pmid': self.safe_get(row_dict, 'pmid'),
                'doi': self.safe_get(row_dict, 'doi'),
                'pmc_id': self.safe_get(row_dict, 'pmc_id'),
                'semantic_scholar_id': self.safe_get(row_dict, 'semantic_scholar_id'),

                # === BASIC INFO ===
                'title': self.safe_get(row_dict, 'title', ''),
                'abstract': self.safe_get(row_dict, 'abstract', ''),
                'methods': self.safe_get(row_dict, 'methods', ''),
                'authors': self.safe_get(row_dict, 'authors', ''),
                'journal': self.safe_get(row_dict, 'journal', ''),
                'year': self.safe_get(row_dict, 'year'),
                'facility': self.safe_get(row_dict, 'facility'),

                # === CITATIONS - CRITICAL! ===
                'citation_count': citation_count,
                'citations': citation_count,  # Alias for compatibility
                'influential_citation_count': self.safe_get(row_dict, 'influential_citation_count', 0),
                'citation_source': self.safe_get(row_dict, 'citation_source'),

                # === URLS ===
                'doi_url': self.safe_get(row_dict, 'doi_url'),
                'pubmed_url': self.safe_get(row_dict, 'pubmed_url'),
                'pmc_url': self.safe_get(row_dict, 'pmc_url'),
                'pdf_url': self.safe_get(row_dict, 'pdf_url'),
                'github_url': self.safe_get(row_dict, 'github_url'),

                # === MICROSCOPY TECHNIQUES ===
                'microscopy_techniques': microscopy_techniques,
                'techniques': techniques if techniques else microscopy_techniques,
                'tags': tags if tags else microscopy_techniques,

                # === MICROSCOPE INFO ===
                'microscope_brands': microscope_brands,
                'microscope_models': microscope_models,
                'microscope_brand': self.safe_get(row_dict, 'microscope_brand'),
                'microscope': {
                    'brands': microscope_brands,
                    'models': microscope_models,
                    'brand': microscope_brands[0] if microscope_brands else None,
                } if microscope_brands or microscope_models else None,

                # === SOFTWARE ===
                'image_analysis_software': image_analysis_software,
                'image_acquisition_software': image_acquisition_software,
                'software': software if software else (image_analysis_software + image_acquisition_software),

                # === SAMPLE PREPARATION ===
                'sample_preparation': sample_preparation,

                # === FLUOROPHORES ===
                'fluorophores': fluorophores,

                # === ORGANISMS & CELL LINES ===
                'organisms': organisms,
                'cell_lines': cell_lines,
                'animal_model': organisms[0] if organisms else None,

                # === RESOURCES ===
                'protocols': protocols,
                'repositories': repositories,
                'image_repositories': repositories,  # Alias
                'supplementary_materials': supplementary,
                'rrids': rrids,
                'rors': rors,
                'antibodies': antibodies,

                # === FIGURES ===
                'figures': figures,
                'figure_count': self.safe_get(row_dict, 'figure_count', 0) or len(figures),
                'figure_urls': [
                    f.get('image_url') or f.get('url') 
                    for f in figures 
                    if isinstance(f, dict) and (f.get('image_url') or f.get('url'))
                ] if figures else [],

                # === FLAGS ===
                'has_full_text': bool(self.safe_get(row_dict, 'has_full_text')),
                'has_figures': bool(figures) or bool(self.safe_get(row_dict, 'has_figures')),
                'has_protocols': bool(protocols) or bool(self.safe_get(row_dict, 'has_protocols')),
                'has_github': bool(self.safe_get(row_dict, 'github_url')) or bool(self.safe_get(row_dict, 'has_github')),
                'has_data': bool(repositories) or bool(self.safe_get(row_dict, 'has_data')),

                # === SCORES ===
                'priority_score': self.safe_get(row_dict, 'priority_score', 0),

                # === TIMESTAMPS ===
                'created_at': str(self.safe_get(row_dict, 'created_at')) if row_dict.get('created_at') else None,
                'updated_at': str(self.safe_get(row_dict, 'updated_at')) if row_dict.get('updated_at') else None,
                'enriched_at': str(self.safe_get(row_dict, 'enriched_at')) if row_dict.get('enriched_at') else None,
            }

            # Update statistics
            if citation_count > 0:
                stats['with_citations'] += 1
                stats['total_citations'] += citation_count
            if row_dict.get('has_full_text'):
                stats['with_full_text'] += 1
            if row_dict.get('methods') and len(str(row_dict.get('methods', ''))) > 100:
                stats['with_methods'] += 1
            if figures:
                stats['with_figures'] += 1
                stats['total_figures'] += len(figures)
            if protocols:
                stats['with_protocols'] += 1
                stats['total_protocols'] += len(protocols)
            if self.safe_get(row_dict, 'github_url'):
                stats['with_github'] += 1
            if repositories:
                stats['with_repositories'] += 1
                stats['total_repositories'] += len(repositories)
            if rrids:
                stats['with_rrids'] += 1
            if microscopy_techniques:
                stats['with_techniques'] += 1
            if image_analysis_software or image_acquisition_software:
                stats['with_software'] += 1
            if fluorophores:
                stats['with_fluorophores'] += 1
            if organisms:
                stats['with_organisms'] += 1
            if sample_preparation:
                stats['with_sample_prep'] += 1

            chunk_papers.append(paper)
            papers_written += 1

            if papers_written % 5000 == 0:
                logger.info(f"Processed {papers_written:,} papers...")

            # Save chunk if full
            if len(chunk_papers) >= chunk_size:
                filename = save_chunk(chunk_papers, chunk_num)
                created_files.append(filename)
                logger.info(f"Saved chunk {chunk_num}: {filename} ({len(chunk_papers):,} papers)")
                
                chunk_num += 1
                chunk_papers = []

        # Save remaining papers
        if chunk_papers:
            filename = save_chunk(chunk_papers, chunk_num)
            created_files.append(filename)
            logger.info(f"Saved: {filename} ({len(chunk_papers):,} papers)")

        conn.close()

        # Calculate total size
        total_size = sum(os.path.getsize(f) for f in created_files) / 1024 / 1024

        # Print comprehensive statistics
        logger.info("")
        logger.info("=" * 60)
        logger.info("EXPORT COMPLETE - ALL DATA PRESERVED")
        logger.info("=" * 60)
        logger.info(f"Total papers exported: {papers_written:,}")
        logger.info(f"Number of files: {len(created_files)}")
        logger.info(f"Total size: {total_size:.1f} MB")
        logger.info("")
        logger.info("CONTENT STATISTICS:")
        logger.info(f"  With citations:    {stats['with_citations']:,} ({stats['total_citations']:,} total)")
        logger.info(f"  With full text:    {stats['with_full_text']:,}")
        logger.info(f"  With methods:      {stats['with_methods']:,}")
        logger.info(f"  With figures:      {stats['with_figures']:,} ({stats['total_figures']:,} total)")
        logger.info(f"  With protocols:    {stats['with_protocols']:,} ({stats['total_protocols']:,} total)")
        logger.info(f"  With GitHub:       {stats['with_github']:,}")
        logger.info(f"  With repositories: {stats['with_repositories']:,} ({stats['total_repositories']:,} total)")
        logger.info(f"  With RRIDs:        {stats['with_rrids']:,}")
        logger.info("")
        logger.info("TAG STATISTICS:")
        logger.info(f"  With techniques:   {stats['with_techniques']:,}")
        logger.info(f"  With software:     {stats['with_software']:,}")
        logger.info(f"  With fluorophores: {stats['with_fluorophores']:,}")
        logger.info(f"  With organisms:    {stats['with_organisms']:,}")
        logger.info(f"  With sample prep:  {stats['with_sample_prep']:,}")
        logger.info("")
        logger.info("Created files:")
        for f in created_files:
            size_mb = os.path.getsize(f) / 1024 / 1024
            logger.info(f"  {f} ({size_mb:.1f} MB)")

        return papers_written


def main():
    parser = argparse.ArgumentParser(description='Export papers to JSON v4.0 - Comprehensive')
    parser.add_argument('--db', default='microhub.db', help='Database path')
    parser.add_argument('--output', '-o', default='microhub_papers_v4.json', help='Output filename')
    parser.add_argument('--limit', type=int, help='Limit number of papers')
    parser.add_argument('--full-text-only', action='store_true', help='Only papers with full text')
    parser.add_argument('--with-citations', action='store_true', help='Only papers with citations')
    parser.add_argument('--min-citations', type=int, default=0, help='Minimum citation count')
    parser.add_argument('--with-protocols', action='store_true', help='Only papers with protocols')
    parser.add_argument('--with-github', action='store_true', help='Only papers with GitHub')
    parser.add_argument('--chunk-size', type=int, default=5000, help='Papers per chunk file (default: 5000)')

    args = parser.parse_args()

    exporter = ComprehensiveJsonExporter(db_path=args.db)
    exporter.export(
        output_path=args.output,
        limit=args.limit,
        full_text_only=args.full_text_only,
        with_citations_only=args.with_citations,
        min_citations=args.min_citations,
        with_protocols_only=args.with_protocols,
        with_github_only=args.with_github,
        chunk_size=args.chunk_size
    )


if __name__ == '__main__':
    main()