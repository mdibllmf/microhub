"""
WordPress-compatible JSON exporter v6.0.

CRITICAL: The output JSON structure MUST remain identical to the v5.1
exporter to prevent WordPress upload issues.  Every field, alias, and
boolean flag is preserved exactly as-is.

This exporter reads from the SQLite database, optionally re-runs the
agent pipeline for enrichment, and writes chunked JSON files.
"""

import json
import logging
import os
import re
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ======================================================================
# Protocol classification (ported from cleanup_and_retag.py v3.7)
# ======================================================================

PROTOCOL_JOURNALS = [
    r'\bnature\s+protocols?\b',
    r'\bnat\.?\s*protoc',
    r'\bjove\b',
    r'\bjournal\s+of\s+visualized\s+experiments\b',
    r'\bj\.\s*vis\.\s*exp\b',
    r'\bstar\s+protocols?\b',
    r'\bbio.?protocol\b',
    r'\bcurrent\s+protocols?\b',
    r'\bcurr\.?\s*protoc',
    r'\bmethods\s+in\s+molecular\s+biology\b',
    r'\bmethods\s+mol\.?\s*biol\b',
    r'\bmethods\s+in\s+enzymology\b',
    r'\bmeth\.?\s*enzymol',
    r'\bcold\s+spring\s+harbor\s+protocols?\b',
    r'\bcsh\s+protocols?\b',
    r'\bcshprotocols\b',
    r'\bprotocol\s+exchange\b',
    r'\bmethodsx\b',
    r'\bmethods\s*x\b',
    r'\bbiotechniques\b',
]


def is_protocol_paper(paper: Dict) -> bool:
    """Check if a paper is from a protocol journal."""
    journal = str(paper.get('journal', '') or '').lower()
    title = str(paper.get('title', '') or '').lower()
    doi = str(paper.get('doi', '') or '').lower()
    combined = f"{journal} {title}"

    for pattern in PROTOCOL_JOURNALS:
        if re.search(pattern, combined, re.IGNORECASE):
            return True

    protocol_doi_patterns = [
        r'10\.1038/nprot', r'10\.1038/s41596', r'10\.3791/',
        r'10\.1016/j\.xpro', r'10\.21769/bioprotoc', r'10\.1002/cp',
        r'10\.1007/978-1-', r'10\.1016/bs\.mie', r'10\.1101/pdb\.prot',
        r'10\.1016/j\.mex',
    ]
    for pattern in protocol_doi_patterns:
        if re.search(pattern, doi, re.IGNORECASE):
            return True

    return False


def get_protocol_type(paper: Dict) -> Optional[str]:
    """Determine the type/source of protocol."""
    journal = str(paper.get('journal', '') or '').lower()
    doi = str(paper.get('doi', '') or '').lower()
    combined = f"{journal} {doi}"

    type_mapping = [
        (r'nature\s+protocols?|10\.1038/nprot|10\.1038/s41596', 'Nature Protocols'),
        (r'jove|journal\s+of\s+visualized|10\.3791/', 'JoVE'),
        (r'star\s+protocols?|10\.1016/j\.xpro', 'STAR Protocols'),
        (r'bio.?protocol|10\.21769/bioprotoc', 'Bio-protocol'),
        (r'current\s+protocols?|10\.1002/cp', 'Current Protocols'),
        (r'methods\s+in\s+molecular\s+biology|10\.1007/978-1-', 'Methods in Molecular Biology'),
        (r'methods\s+in\s+enzymology|10\.1016/bs\.mie', 'Methods in Enzymology'),
        (r'cold\s+spring\s+harbor|cshprotocols|10\.1101/pdb', 'Cold Spring Harbor Protocols'),
        (r'methodsx|methods\s*x|10\.1016/j\.mex', 'MethodsX'),
        (r'protocol\s+exchange', 'Protocol Exchange'),
        (r'biotechniques', 'Biotechniques'),
    ]
    for pattern, ptype in type_mapping:
        if re.search(pattern, combined, re.IGNORECASE):
            return ptype
    return None


class JsonExporter:
    """Export papers to chunked JSON matching the existing WordPress format."""

    def __init__(self, db_path: str = None):
        if db_path is None:
            script_dir = os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)
            ))
            db_path = os.path.join(script_dir, "microhub.db")
        self.db_path = db_path

    # ------------------------------------------------------------------
    # JSON helpers (carried over verbatim from v5.1)
    # ------------------------------------------------------------------

    @staticmethod
    def safe_json_parse(value: Any) -> Any:
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

    @staticmethod
    def safe_get(row: Dict, field: str, default: Any = None) -> Any:
        value = row.get(field)
        if value is None:
            return default
        return value

    # ------------------------------------------------------------------
    # Main export
    # ------------------------------------------------------------------

    def export(
        self,
        output_path: str = "microhub_papers_v5.json",
        limit: int = None,
        full_text_only: bool = False,
        with_citations_only: bool = False,
        min_citations: int = 0,
        with_protocols_only: bool = False,
        with_github_only: bool = False,
        methods_only: bool = False,
        chunk_size: int = 500,
        enricher=None,
    ) -> int:
        """Export papers to JSON with ALL fields.

        Parameters
        ----------
        enricher : PipelineOrchestrator, optional
            If provided, re-runs the agent pipeline on each paper to refresh
            tag extractions.  Pass ``None`` to export existing DB values.
        """
        logger.info("=" * 60)
        logger.info("MICROHUB JSON EXPORTER v6.0 - AGENT PIPELINE")
        logger.info("=" * 60)
        logger.info("Chunk size: %d papers per file", chunk_size)

        conn = sqlite3.connect(self.db_path, timeout=120.0)
        conn.row_factory = sqlite3.Row

        # GitHub tools (same logic as v5.1)
        github_tools_map, github_tools_summary = self._load_github_tools(conn)

        # Build query
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
        if methods_only:
            conditions.append("tag_source = 'methods'")

        where = " AND ".join(conditions) if conditions else "1=1"

        total = conn.execute(f"SELECT COUNT(*) FROM papers WHERE {where}").fetchone()[0]
        logger.info("Total papers matching criteria: %d", total)

        query = f"""
            SELECT * FROM papers WHERE {where}
            ORDER BY citation_count DESC, priority_score DESC, year DESC
        """
        if limit:
            query += f" LIMIT {limit}"

        cursor = conn.execute(query)

        base_name = output_path.replace(".json", "")
        chunk_num = 1
        chunk_papers: List[Dict] = []
        papers_written = 0
        created_files: List[str] = []

        stats = self._init_stats()

        for row in cursor:
            row_dict = dict(row)

            # Optionally re-run agents for fresh tags
            if enricher is not None:
                agent_results = enricher.process_paper(row_dict)
                row_dict = self._merge_agent_results(row_dict, agent_results)

            paper = self._build_paper_dict(row_dict, github_tools_map)
            self._update_stats(stats, paper, row_dict)

            chunk_papers.append(paper)
            papers_written += 1

            if papers_written % 5000 == 0:
                logger.info("Processed %d papers...", papers_written)

            if len(chunk_papers) >= chunk_size:
                fn = f"{base_name}_chunk_{chunk_num}.json"
                self._save_chunk(chunk_papers, fn)
                created_files.append(fn)
                logger.info("Saved chunk %d: %s (%d papers)", chunk_num, fn, len(chunk_papers))
                chunk_num += 1
                chunk_papers = []

        if chunk_papers:
            fn = f"{base_name}_chunk_{chunk_num}.json"
            self._save_chunk(chunk_papers, fn)
            created_files.append(fn)
            logger.info("Saved: %s (%d papers)", fn, len(chunk_papers))

        conn.close()

        # GitHub tools summary
        tools_fn = f"{base_name}_github_tools.json"
        if github_tools_summary:
            with open(tools_fn, "w", encoding="utf-8") as f:
                json.dump(github_tools_summary, f, indent=2, ensure_ascii=False, default=str)
            created_files.append(tools_fn)
            logger.info("Saved GitHub tools: %s (%d tools)", tools_fn, len(github_tools_summary))

        self._print_stats(stats, papers_written, created_files)
        return papers_written

    # ------------------------------------------------------------------
    # Build the EXACT paper dict that WordPress expects
    # ------------------------------------------------------------------

    def _build_paper_dict(self, row_dict: Dict, github_tools_map: Dict) -> Dict:
        """Construct paper JSON matching the v5.1 schema exactly."""
        # Parse all JSON array fields
        microscopy_techniques = self.safe_json_parse(row_dict.get("microscopy_techniques"))
        microscope_brands = self.safe_json_parse(row_dict.get("microscope_brands"))
        microscope_models = self.safe_json_parse(row_dict.get("microscope_models"))
        reagent_suppliers = self.safe_json_parse(row_dict.get("reagent_suppliers"))
        image_analysis_software = self.safe_json_parse(row_dict.get("image_analysis_software"))
        image_acquisition_software = self.safe_json_parse(row_dict.get("image_acquisition_software"))
        general_software = self.safe_json_parse(row_dict.get("general_software"))
        sample_preparation = self.safe_json_parse(row_dict.get("sample_preparation"))
        fluorophores = self.safe_json_parse(row_dict.get("fluorophores"))
        organisms = self.safe_json_parse(row_dict.get("organisms"))
        antibody_sources = self.safe_json_parse(row_dict.get("antibody_sources"))
        cell_lines = self.safe_json_parse(row_dict.get("cell_lines"))
        protocols = self.safe_json_parse(row_dict.get("protocols"))
        repositories = self.safe_json_parse(row_dict.get("repositories"))
        supplementary = self.safe_json_parse(row_dict.get("supplementary_materials"))
        rrids = self.safe_json_parse(row_dict.get("rrids"))
        rors = self.safe_json_parse(row_dict.get("rors"))
        references = self.safe_json_parse(row_dict.get("references"))
        figures = self.safe_json_parse(row_dict.get("figures"))
        antibodies = self.safe_json_parse(row_dict.get("antibodies"))
        affiliations = self.safe_json_parse(row_dict.get("affiliations"))
        institutions = self.safe_json_parse(row_dict.get("institutions"))
        if not institutions:
            institutions = self.safe_json_parse(row_dict.get("facilities"))
        imaging_modalities = self.safe_json_parse(row_dict.get("imaging_modalities"))
        staining_methods = self.safe_json_parse(row_dict.get("staining_methods"))
        lasers = self.safe_json_parse(row_dict.get("lasers"))
        detectors = self.safe_json_parse(row_dict.get("detectors"))
        objectives = self.safe_json_parse(row_dict.get("objectives"))
        filters = self.safe_json_parse(row_dict.get("filters"))
        embedding_methods = self.safe_json_parse(row_dict.get("embedding_methods"))
        fixation_methods = self.safe_json_parse(row_dict.get("fixation_methods"))
        mounting_media = self.safe_json_parse(row_dict.get("mounting_media"))
        techniques = self.safe_json_parse(row_dict.get("techniques"))
        software = self.safe_json_parse(row_dict.get("software"))
        tags = self.safe_json_parse(row_dict.get("tags"))

        citation_count = self.safe_get(row_dict, "citation_count", 0) or 0
        tag_source = self.safe_get(row_dict, "tag_source", "unknown")

        # ---- Build the output dict (IDENTICAL key order to v5.1) ----
        paper = {
            # === IDENTIFIERS ===
            "id": row_dict.get("id"),
            "pmid": self.safe_get(row_dict, "pmid"),
            "doi": self.safe_get(row_dict, "doi"),
            "pmc_id": self.safe_get(row_dict, "pmc_id"),
            "semantic_scholar_id": self.safe_get(row_dict, "semantic_scholar_id"),

            # === BASIC INFO ===
            "title": self.safe_get(row_dict, "title", ""),
            "abstract": self.safe_get(row_dict, "abstract", ""),
            "methods": self.safe_get(row_dict, "methods", ""),
            "full_text": self.safe_get(row_dict, "full_text", ""),
            "authors": self.safe_get(row_dict, "authors", ""),
            "journal": self.safe_get(row_dict, "journal", ""),
            "year": self.safe_get(row_dict, "year"),

            # === AFFILIATIONS & INSTITUTIONS ===
            "affiliations": affiliations,
            "institutions": institutions,
            "facility": institutions[0] if institutions else self.safe_get(row_dict, "facility"),
            "facilities": institutions,
            "imaging_facility": self.safe_get(row_dict, "imaging_facility", ""),

            # === CITATIONS ===
            "citation_count": citation_count,
            "citations": citation_count,
            "influential_citation_count": self.safe_get(row_dict, "influential_citation_count", 0),
            "citation_source": self.safe_get(row_dict, "citation_source"),

            # === URLS ===
            "doi_url": self.safe_get(row_dict, "doi_url"),
            "pubmed_url": self.safe_get(row_dict, "pubmed_url"),
            "pmc_url": self.safe_get(row_dict, "pmc_url"),
            "pdf_url": self.safe_get(row_dict, "pdf_url"),
            "github_url": self.safe_get(row_dict, "github_url"),

            # === GITHUB TOOLS ===
            "github_tools": github_tools_map.get(row_dict.get("id"), []),

            # === MICROSCOPY TECHNIQUES ===
            "microscopy_techniques": microscopy_techniques,
            "techniques": techniques if techniques else microscopy_techniques,
            "tags": tags if tags else microscopy_techniques,

            # === MICROSCOPE INFO ===
            "microscope_brands": microscope_brands,
            "microscope_models": microscope_models,
            "microscope_brand": self.safe_get(row_dict, "microscope_brand"),
            "microscope": {
                "brands": microscope_brands,
                "models": microscope_models,
                "brand": microscope_brands[0] if microscope_brands else None,
            } if microscope_brands or microscope_models else None,

            # === REAGENT SUPPLIERS ===
            "reagent_suppliers": reagent_suppliers,

            # === SOFTWARE ===
            "image_analysis_software": image_analysis_software,
            "image_acquisition_software": image_acquisition_software,
            "general_software": general_software,
            "software": software if software else (
                image_analysis_software + image_acquisition_software + general_software
            ),

            # === SAMPLE PREPARATION ===
            "sample_preparation": sample_preparation,

            # === FLUOROPHORES ===
            "fluorophores": fluorophores,

            # === ORGANISMS & CELL LINES ===
            "organisms": organisms,
            "antibody_sources": antibody_sources,
            "cell_lines": cell_lines,
            "animal_model": organisms[0] if organisms else None,

            # === ADDITIONAL MICROSCOPY DETAILS ===
            "imaging_modalities": imaging_modalities,
            "staining_methods": staining_methods,
            "lasers": lasers,
            "detectors": detectors,
            "objectives": objectives,
            "filters": filters,
            "embedding_methods": embedding_methods,
            "fixation_methods": fixation_methods,
            "mounting_media": mounting_media,

            # === RESOURCES ===
            "protocols": protocols,
            "repositories": repositories,
            "image_repositories": repositories,
            "supplementary_materials": supplementary,
            "rrids": rrids,
            "rors": rors,
            "references": references,
            "antibodies": antibodies,

            # === FIGURES ===
            "figures": figures,
            "figure_count": self.safe_get(row_dict, "figure_count", 0) or len(figures),
            "figure_urls": [
                f.get("image_url") or f.get("url")
                for f in figures
                if isinstance(f, dict) and (f.get("image_url") or f.get("url"))
            ] if figures else [],

            # === FLAGS ===
            "has_full_text": bool(self.safe_get(row_dict, "has_full_text")) or bool(self.safe_get(row_dict, "full_text")),
            "has_figures": bool(figures) or bool(self.safe_get(row_dict, "has_figures")),
            "has_protocols": bool(protocols) or bool(self.safe_get(row_dict, "has_protocols")),
            "has_github": bool(self.safe_get(row_dict, "github_url")) or bool(self.safe_get(row_dict, "has_github")),
            "has_data": bool(repositories) or bool(self.safe_get(row_dict, "has_data")),
            "has_rrids": bool(rrids),
            "has_rors": bool(rors),
            "has_fluorophores": bool(fluorophores),
            "has_cell_lines": bool(cell_lines),
            "has_sample_prep": bool(sample_preparation),
            "has_antibody_sources": bool(antibody_sources),
            "has_reagent_suppliers": bool(reagent_suppliers),
            "has_general_software": bool(general_software),
            "has_methods": bool(self.safe_get(row_dict, "methods")) and len(str(self.safe_get(row_dict, "methods", ""))) > 100,
            "has_antibodies": bool(antibodies),
            "has_affiliations": bool(affiliations) or bool(self.safe_get(row_dict, "has_affiliations")),
            "has_institutions": bool(institutions) or bool(self.safe_get(row_dict, "has_institutions")),
            "has_supplementary_materials": bool(supplementary),
            "has_objectives": bool(objectives),
            "has_lasers": bool(lasers),
            "has_detectors": bool(detectors),
            "has_filters": bool(filters),
            "links_validated": bool(self.safe_get(row_dict, "links_validated")),

            # === TAG EXTRACTION METADATA ===
            "tag_source": tag_source,
            "tags_from_methods": tag_source == "methods",

            # === SCORES ===
            "priority_score": self.safe_get(row_dict, "priority_score", 0),

            # === TIMESTAMPS ===
            "created_at": str(self.safe_get(row_dict, "created_at")) if row_dict.get("created_at") else None,
            "updated_at": str(self.safe_get(row_dict, "updated_at")) if row_dict.get("updated_at") else None,
            "enriched_at": str(self.safe_get(row_dict, "enriched_at")) if row_dict.get("enriched_at") else None,
            "citations_updated_at": str(self.safe_get(row_dict, "citations_updated_at")) if row_dict.get("citations_updated_at") else None,
            "validated_at": str(self.safe_get(row_dict, "validated_at")) if row_dict.get("validated_at") else None,
            "full_text_fetched_at": str(self.safe_get(row_dict, "full_text_fetched_at")) if row_dict.get("full_text_fetched_at") else None,
        }

        # === CLEANUP FINALIZATION (from cleanup_and_retag.py v3.7) ===
        # Protocol classification
        paper["is_protocol"] = is_protocol_paper(paper) or bool(protocols)
        if is_protocol_paper(paper):
            paper["post_type"] = "mh_protocol"
            paper["protocol_type"] = get_protocol_type(paper)
        else:
            paper["post_type"] = "mh_paper"
            paper["protocol_type"] = None

        # Additional boolean flags (matching cleaned_export)
        paper["has_github_tools"] = bool(paper.get("github_tools"))
        paper["has_facility"] = paper["has_institutions"]

        # Extract data_availability and code_availability from full_text
        # BEFORE stripping it — step 3 needs these for repository extraction
        if paper.get("full_text") and not paper.get("data_availability"):
            from pipeline.parsing.section_extractor import _extract_data_availability
            paper["data_availability"] = _extract_data_availability(paper["full_text"])

        # Remove full_text from output (tags already extracted)
        if "full_text" in paper:
            del paper["full_text"]

        return paper

    # ------------------------------------------------------------------
    # Merge agent results back into DB row
    # ------------------------------------------------------------------

    @staticmethod
    def _merge_agent_results(row_dict: Dict, agent: Dict) -> Dict:
        """Merge agent extraction results with DB row values.

        For list fields: unions both sources (scraper + agent) and
        deduplicates.  For scalar fields: keeps DB value if agent
        returns empty.  Metadata (title, DOI, etc.) is always kept
        from the database.
        """
        merged = dict(row_dict)

        tag_fields = [
            "microscopy_techniques", "microscope_brands", "microscope_models",
            "reagent_suppliers", "image_analysis_software",
            "image_acquisition_software", "general_software",
            "fluorophores", "organisms", "antibody_sources",
            "cell_lines", "sample_preparation", "protocols",
            "repositories", "rrids", "rors", "institutions",
            "objectives", "lasers", "detectors", "filters",
            "imaging_modalities", "staining_methods",
            "embedding_methods", "fixation_methods", "mounting_media",
            "antibodies", "affiliations",
            "github_url", "tag_source",
        ]

        # Fields where scraper data is authoritative and should never
        # be replaced with empty agent results
        preserve_if_empty = {"github_url", "tag_source"}

        for field in tag_fields:
            if field not in agent:
                continue
            agent_val = agent[field]

            if isinstance(agent_val, list):
                # Union: combine DB values + agent values, deduplicate
                db_raw = merged.get(field, "[]")
                if isinstance(db_raw, str):
                    try:
                        db_list = json.loads(db_raw)
                    except (json.JSONDecodeError, TypeError):
                        db_list = []
                elif isinstance(db_raw, list):
                    db_list = db_raw
                else:
                    db_list = []

                # Deduplicate: for dicts use canonical/id/url key, for strings use value
                seen = set()
                combined = []
                for item in db_list + agent_val:
                    if isinstance(item, dict):
                        key = item.get("canonical") or item.get("id") or item.get("url") or json.dumps(item, sort_keys=True)
                    else:
                        key = str(item)
                    if key not in seen:
                        seen.add(key)
                        combined.append(item)

                merged[field] = json.dumps(combined, ensure_ascii=False)

            elif isinstance(agent_val, dict) and agent_val:
                merged[field] = json.dumps(agent_val, ensure_ascii=False)

            else:
                # Scalar: only overwrite if agent has a value
                if field in preserve_if_empty and not agent_val:
                    continue
                if agent_val is not None:
                    merged[field] = agent_val

        return merged

    # ------------------------------------------------------------------
    # GitHub tools loading (same as v5.1)
    # ------------------------------------------------------------------

    def _load_github_tools(self, conn):
        github_tools_map = {}
        github_tools_summary = []

        try:
            cursor_check = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name IN ('github_tools', 'paper_github_tools')"
            )
            existing = {r[0] for r in cursor_check.fetchall()}
            if "github_tools" not in existing or "paper_github_tools" not in existing:
                return github_tools_map, github_tools_summary

            rows = conn.execute("""
                SELECT pgt.paper_id, gt.full_name, gt.repo_url, gt.description,
                       gt.stars, gt.forks, gt.open_issues, gt.last_commit_date,
                       gt.last_release_date, gt.last_release_tag, gt.health_score,
                       gt.is_archived, gt.language, gt.license, gt.topics,
                       gt.paper_count, gt.citing_paper_count, gt.total_citations_of_papers,
                       gt.tool_type, pgt.relationship
                FROM paper_github_tools pgt
                JOIN github_tools gt ON gt.id = pgt.github_tool_id
            """).fetchall()

            for tr in rows:
                pid = tr["paper_id"]
                if pid not in github_tools_map:
                    github_tools_map[pid] = []
                github_tools_map[pid].append({
                    "full_name": tr["full_name"],
                    "url": tr["repo_url"],
                    "description": tr["description"],
                    "stars": tr["stars"],
                    "forks": tr["forks"],
                    "open_issues": tr["open_issues"],
                    "last_commit_date": tr["last_commit_date"],
                    "last_release": tr["last_release_tag"],
                    "health_score": tr["health_score"],
                    "is_archived": bool(tr["is_archived"]),
                    "language": tr["language"],
                    "license": tr["license"],
                    "topics": self.safe_json_parse(tr["topics"]),
                    "paper_count": tr["paper_count"],
                    "citing_paper_count": tr["citing_paper_count"],
                    "relationship": tr["relationship"],
                })

            summary_rows = conn.execute("""
                SELECT full_name, repo_url, description, stars, forks, open_issues,
                       health_score, paper_count, citing_paper_count, is_archived,
                       language, license, last_commit_date, last_release_tag,
                       tool_type, topics
                FROM github_tools
                WHERE paper_count >= 1
                ORDER BY paper_count DESC, stars DESC
                LIMIT 200
            """).fetchall()

            for sr in summary_rows:
                github_tools_summary.append({
                    "full_name": sr["full_name"],
                    "url": sr["repo_url"],
                    "description": sr["description"],
                    "stars": sr["stars"],
                    "forks": sr["forks"],
                    "open_issues": sr["open_issues"] or 0,
                    "health_score": sr["health_score"],
                    "paper_count": sr["paper_count"],
                    "citing_paper_count": sr["citing_paper_count"],
                    "is_archived": bool(sr["is_archived"]),
                    "language": sr["language"],
                    "license": sr["license"],
                    "last_commit_date": sr["last_commit_date"],
                    "last_release": sr["last_release_tag"],
                    "tool_type": sr["tool_type"],
                    "topics": self.safe_json_parse(sr["topics"]),
                    "relationship": "uses",
                })

            logger.info(
                "Loaded GitHub tools for %d papers, %d unique tools",
                len(github_tools_map), len(github_tools_summary),
            )
        except Exception as exc:
            logger.warning("GitHub tools loading failed: %s", exc)

        return github_tools_map, github_tools_summary

    # ------------------------------------------------------------------
    # Stats & file writing
    # ------------------------------------------------------------------

    @staticmethod
    def _save_chunk(papers: List[Dict], filename: str):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(papers, f, indent=2, ensure_ascii=False, default=str)

    @staticmethod
    def _init_stats() -> Dict:
        return {
            "with_citations": 0, "with_full_text": 0, "with_methods": 0,
            "with_figures": 0, "with_protocols": 0, "with_github": 0,
            "with_repositories": 0, "with_rrids": 0, "with_rors": 0,
            "with_techniques": 0, "with_software": 0,
            "with_fluorophores": 0, "with_organisms": 0,
            "with_antibody_sources": 0, "with_sample_prep": 0,
            "with_cell_lines": 0, "with_staining": 0,
            "with_affiliations": 0, "with_institutions": 0,
            "with_reagent_suppliers": 0, "with_general_software": 0,
            "with_objectives": 0, "with_lasers": 0,
            "with_detectors": 0, "with_filters": 0,
            "total_citations": 0, "total_figures": 0,
            "total_protocols": 0, "total_repositories": 0,
            "total_fluorophores": 0, "total_cell_lines": 0,
            "total_rors": 0, "total_rrids": 0,
            "total_affiliations": 0, "total_institutions": 0,
            "from_methods": 0, "from_title_abstract": 0,
        }

    @staticmethod
    def _update_stats(stats: Dict, paper: Dict, row_dict: Dict):
        cc = paper.get("citation_count", 0) or 0
        if cc > 0:
            stats["with_citations"] += 1
            stats["total_citations"] += cc
        if row_dict.get("has_full_text"):
            stats["with_full_text"] += 1
        if paper.get("has_methods"):
            stats["with_methods"] += 1
        if paper.get("has_figures"):
            stats["with_figures"] += 1
            stats["total_figures"] += len(paper.get("figures", []))
        if paper.get("has_protocols"):
            stats["with_protocols"] += 1
            stats["total_protocols"] += len(paper.get("protocols", []))
        if paper.get("has_github"):
            stats["with_github"] += 1
        if paper.get("repositories"):
            stats["with_repositories"] += 1
            stats["total_repositories"] += len(paper["repositories"])
        if paper.get("rrids"):
            stats["with_rrids"] += 1
            stats["total_rrids"] += len(paper["rrids"])
        if paper.get("rors"):
            stats["with_rors"] += 1
            stats["total_rors"] += len(paper["rors"])
        if paper.get("microscopy_techniques"):
            stats["with_techniques"] += 1
        if paper.get("image_analysis_software") or paper.get("image_acquisition_software"):
            stats["with_software"] += 1
        if paper.get("fluorophores"):
            stats["with_fluorophores"] += 1
            stats["total_fluorophores"] += len(paper["fluorophores"])
        if paper.get("organisms"):
            stats["with_organisms"] += 1
        if paper.get("antibody_sources"):
            stats["with_antibody_sources"] += 1
        if paper.get("sample_preparation"):
            stats["with_sample_prep"] += 1
        if paper.get("cell_lines"):
            stats["with_cell_lines"] += 1
            stats["total_cell_lines"] += len(paper["cell_lines"])
        if paper.get("staining_methods"):
            stats["with_staining"] += 1
        if paper.get("affiliations"):
            stats["with_affiliations"] += 1
            stats["total_affiliations"] += len(paper["affiliations"])
        if paper.get("institutions"):
            stats["with_institutions"] += 1
            stats["total_institutions"] += len(paper["institutions"])
        if paper.get("reagent_suppliers"):
            stats["with_reagent_suppliers"] += 1
        if paper.get("general_software"):
            stats["with_general_software"] += 1
        if paper.get("objectives"):
            stats["with_objectives"] += 1
        if paper.get("lasers"):
            stats["with_lasers"] += 1
        if paper.get("detectors"):
            stats["with_detectors"] += 1
        if paper.get("filters"):
            stats["with_filters"] += 1
        ts = paper.get("tag_source", "")
        if ts == "methods":
            stats["from_methods"] += 1
        elif ts == "title_abstract":
            stats["from_title_abstract"] += 1

    @staticmethod
    def _print_stats(stats: Dict, total: int, files: List[str]):
        total_size = sum(
            os.path.getsize(f) for f in files if os.path.exists(f)
        ) / 1024 / 1024
        logger.info("")
        logger.info("=" * 60)
        logger.info("EXPORT COMPLETE - ALL DATA PRESERVED")
        logger.info("=" * 60)
        logger.info("Total papers exported: %d", total)
        logger.info("Number of files: %d", len(files))
        logger.info("Total size: %.1f MB", total_size)
        logger.info("")
        logger.info("CONTENT STATISTICS:")
        logger.info("  With citations:    %d (%d total)", stats["with_citations"], stats["total_citations"])
        logger.info("  With full text:    %d", stats["with_full_text"])
        logger.info("  With methods:      %d", stats["with_methods"])
        logger.info("  With figures:      %d (%d total)", stats["with_figures"], stats["total_figures"])
        logger.info("  With protocols:    %d (%d total)", stats["with_protocols"], stats["total_protocols"])
        logger.info("  With GitHub:       %d", stats["with_github"])
        logger.info("  With repositories: %d (%d total)", stats["with_repositories"], stats["total_repositories"])
        logger.info("  With RRIDs:        %d (%d total)", stats["with_rrids"], stats["total_rrids"])
        logger.info("  With RORs:         %d (%d total)", stats["with_rors"], stats["total_rors"])
        logger.info("")
        logger.info("AFFILIATIONS & INSTITUTIONS:")
        logger.info("  With affiliations: %d (%d total)", stats["with_affiliations"], stats["total_affiliations"])
        logger.info("  With institutions: %d (%d total)", stats["with_institutions"], stats["total_institutions"])
        logger.info("")
        logger.info("TAG STATISTICS:")
        logger.info("  With techniques:     %d", stats["with_techniques"])
        logger.info("  With software:       %d", stats["with_software"])
        logger.info("  With fluorophores:   %d (%d total)", stats["with_fluorophores"], stats["total_fluorophores"])
        logger.info("  With organisms:      %d", stats["with_organisms"])
        logger.info("  With antibody src:   %d", stats["with_antibody_sources"])
        logger.info("  With sample prep:    %d", stats["with_sample_prep"])
        logger.info("  With cell lines:     %d (%d total)", stats["with_cell_lines"], stats["total_cell_lines"])
        logger.info("  With staining:       %d", stats["with_staining"])
        logger.info("  With objectives:     %d", stats.get("with_objectives", 0))
        logger.info("  With lasers:         %d", stats.get("with_lasers", 0))
        logger.info("  With detectors:      %d", stats.get("with_detectors", 0))
        logger.info("  With filters:        %d", stats.get("with_filters", 0))
        logger.info("")
        logger.info("TAG EXTRACTION SOURCE:")
        logger.info("  From methods (high confidence):  %d", stats["from_methods"])
        logger.info("  From title+abstract (reviews):   %d", stats["from_title_abstract"])
        logger.info("")
        logger.info("Created files:")
        for fn in files:
            if os.path.exists(fn):
                sz = os.path.getsize(fn) / 1024 / 1024
                logger.info("  %s (%.1f MB)", fn, sz)
