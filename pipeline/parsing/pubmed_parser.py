"""
PubMed / PMC article parser.

Extracts structured sections, metadata, and author affiliations from
PubMed XML (efetch) and PMC NXML full-text articles.  Also handles
the PubMed E-utilities search workflow used by the original scraper.
"""

import re
import logging
import time
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional
from urllib.parse import quote

logger = logging.getLogger(__name__)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# PubMed E-utilities base
_EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
_PMC_OA = "https://www.ncbi.nlm.nih.gov/pmc/oai/oai.cgi"

# Rate-limit: NCBI asks for <=3 requests/sec without an API key
_REQUEST_DELAY = 0.35


def _retry_get(url: str, params: Dict = None, retries: int = 3,
               timeout: int = 30) -> Optional[requests.Response]:
    """GET with exponential backoff."""
    if not HAS_REQUESTS:
        return None
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, timeout=timeout)
            if resp.status_code == 200:
                return resp
            if resp.status_code == 429:
                time.sleep(2 ** (attempt + 2))
                continue
            logger.debug("HTTP %d from %s", resp.status_code, url)
        except requests.RequestException as exc:
            logger.debug("Request error: %s", exc)
            time.sleep(2 ** attempt)
    return None


# ======================================================================
# PubMed search + metadata
# ======================================================================

def search_pubmed(query: str, retmax: int = 100) -> List[str]:
    """Return a list of PMIDs matching *query*."""
    resp = _retry_get(
        f"{_EUTILS}/esearch.fcgi",
        params={"db": "pubmed", "term": query, "retmax": retmax, "retmode": "json"},
    )
    if resp is None:
        return []
    try:
        data = resp.json()
        return data.get("esearchresult", {}).get("idlist", [])
    except Exception:
        return []


def fetch_pubmed_metadata(pmids: List[str]) -> List[Dict[str, Any]]:
    """Fetch metadata for a batch of PMIDs (max ~200 per call)."""
    if not pmids:
        return []

    resp = _retry_get(
        f"{_EUTILS}/efetch.fcgi",
        params={
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
        },
        timeout=60,
    )
    if resp is None:
        return []

    papers: List[Dict[str, Any]] = []
    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError:
        logger.warning("Failed to parse PubMed XML")
        return []

    for article in root.findall(".//PubmedArticle"):
        papers.append(_parse_pubmed_article(article))
        time.sleep(_REQUEST_DELAY)

    return papers


def _parse_pubmed_article(article: ET.Element) -> Dict[str, Any]:
    """Parse a single <PubmedArticle> element."""
    medline = article.find("MedlineCitation")
    if medline is None:
        return {}

    art = medline.find("Article")
    if art is None:
        return {}

    result: Dict[str, Any] = {}

    # PMID
    pmid_el = medline.find("PMID")
    result["pmid"] = pmid_el.text.strip() if pmid_el is not None else None

    # Title
    title_el = art.find("ArticleTitle")
    result["title"] = _element_text(title_el)

    # Abstract
    abstract_parts = []
    abstract_el = art.find("Abstract")
    if abstract_el is not None:
        for abst in abstract_el.findall("AbstractText"):
            label = abst.get("Label", "")
            text = _element_text(abst)
            if label:
                abstract_parts.append(f"{label}: {text}")
            else:
                abstract_parts.append(text)
    result["abstract"] = " ".join(abstract_parts)

    # Journal
    journal_el = art.find("Journal/Title")
    result["journal"] = _element_text(journal_el)

    # Year
    pub_date = art.find("Journal/JournalIssue/PubDate")
    if pub_date is not None:
        year_el = pub_date.find("Year")
        if year_el is not None and year_el.text:
            try:
                result["year"] = int(year_el.text)
            except ValueError:
                pass

    # Authors
    author_list = art.find("AuthorList")
    authors, affiliations = _parse_authors(author_list)
    result["authors"] = ", ".join(authors)
    result["affiliations"] = affiliations

    # DOI and PMC ID
    article_ids = article.find("PubmedData/ArticleIdList")
    if article_ids is not None:
        for aid in article_ids.findall("ArticleId"):
            id_type = aid.get("IdType", "")
            if id_type == "doi" and aid.text:
                result["doi"] = aid.text.strip()
            elif id_type == "pmc" and aid.text:
                result["pmc_id"] = aid.text.strip()

    return result


def _parse_authors(author_list: Optional[ET.Element]):
    """Return (author_names, affiliations) from <AuthorList>."""
    names: List[str] = []
    affs: List[str] = []
    if author_list is None:
        return names, affs

    for author in author_list.findall("Author"):
        last = author.find("LastName")
        fore = author.find("ForeName")
        parts = []
        if last is not None and last.text:
            parts.append(last.text.strip())
        if fore is not None and fore.text:
            parts.append(fore.text.strip())
        if parts:
            names.append(" ".join(parts))

        for aff_el in author.findall("AffiliationInfo/Affiliation"):
            text = _element_text(aff_el)
            if text and text not in affs:
                affs.append(text)

    return names, affs


# ======================================================================
# PMC full-text
# ======================================================================

def fetch_pmc_fulltext(pmc_id: str) -> Optional[str]:
    """Fetch full-text XML from PMC for a given PMC ID (e.g. 'PMC1234567')."""
    pmc_id = pmc_id.replace("PMC", "").strip()
    resp = _retry_get(
        f"{_EUTILS}/efetch.fcgi",
        params={"db": "pmc", "id": pmc_id, "retmode": "xml"},
        timeout=60,
    )
    if resp and resp.status_code == 200:
        return resp.text
    return None


def extract_pmc_sections(xml_text: str) -> List[Dict[str, str]]:
    """Parse PMC NXML into section dicts with heading, text, and type."""
    sections: List[Dict[str, str]] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return sections

    # Abstract
    for abstract in root.findall(".//abstract"):
        text = _recursive_text(abstract)
        if text.strip():
            sections.append(
                {"heading": "Abstract", "text": text.strip(), "type": "abstract"}
            )

    # Body sections
    for sec in root.findall(".//body//sec"):
        title_el = sec.find("title")
        heading = _element_text(title_el) if title_el is not None else ""
        paragraphs = []
        for p in sec.findall("p"):
            t = _recursive_text(p)
            if t.strip():
                paragraphs.append(t.strip())
        if not paragraphs:
            continue

        section_type = _classify_pmc_heading(heading)
        sections.append(
            {"heading": heading, "text": " ".join(paragraphs), "type": section_type}
        )

    return sections


_SECTION_MAP = {
    "methods": re.compile(
        r"method|material|experimental|procedure|microscopy|imaging", re.I
    ),
    "results": re.compile(r"result|finding", re.I),
    "introduction": re.compile(r"introduction|background", re.I),
    "discussion": re.compile(r"discussion|conclusion|summary", re.I),
}


def _classify_pmc_heading(heading: str) -> str:
    for stype, pat in _SECTION_MAP.items():
        if pat.search(heading):
            return stype
    return "other"


# ======================================================================
# Citation APIs
# ======================================================================

def fetch_semantic_scholar(doi: str = None, pmid: str = None,
                           api_key: str = "") -> Dict[str, Any]:
    """Query Semantic Scholar for citation data and paper ID."""
    headers = {}
    if api_key:
        headers["x-api-key"] = api_key

    identifier = None
    if doi:
        identifier = f"DOI:{doi}"
    elif pmid:
        identifier = f"PMID:{pmid}"
    else:
        return {}

    url = (
        f"https://api.semanticscholar.org/graph/v1/paper/{identifier}"
        f"?fields=citationCount,influentialCitationCount,externalIds,fieldsOfStudy"
    )
    resp = _retry_get(url)
    if resp is None:
        return {}
    try:
        data = resp.json()
        return {
            "semantic_scholar_id": data.get("paperId"),
            "citation_count": data.get("citationCount", 0),
            "influential_citation_count": data.get("influentialCitationCount", 0),
            "fields_of_study": [
                f.get("category", "") for f in (data.get("fieldsOfStudy") or [])
            ],
        }
    except Exception:
        return {}


def fetch_crossref(doi: str) -> Dict[str, Any]:
    """Query CrossRef for DOI metadata."""
    if not doi:
        return {}
    url = f"https://api.crossref.org/works/{quote(doi, safe='')}"
    resp = _retry_get(url)
    if resp is None:
        return {}
    try:
        msg = resp.json().get("message", {})
        return {
            "doi_url": f"https://doi.org/{doi}",
            "journal": " ".join(msg.get("container-title", [])),
            "type": msg.get("type"),
        }
    except Exception:
        return {}


# ======================================================================
# Helpers
# ======================================================================

def _element_text(el: Optional[ET.Element]) -> str:
    if el is None:
        return ""
    return "".join(el.itertext()).strip()


def _recursive_text(el: ET.Element) -> str:
    return "".join(el.itertext())
