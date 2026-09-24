"""Tool handlers and Elsevier API integration logic."""

from datetime import datetime
import logging
from typing import Any

from pydantic import ValidationError

from elsevier_mcp.client import ElsevierAPIClient
from elsevier_mcp.schemas import (
    AnalyzeResearchTrendsInput,
    GetAuthorInfoInput,
    GetInstitutionPapersInput,
    GetJournalMetricsInput,
    GetPaperAbstractInput,
    SearchOpenAccessPapersInput,
    SearchPapersInput,
)

logger = logging.getLogger("elsevier_mcp.handlers")

FIELD_CODES = (
    "TITLE-ABS-KEY(",
    "AUTH(",
    "AUTHOR-NAME(",
    "AFFIL(",
    "AFFILORG(",
    "TITLE(",
    "ABS(",
    "KEY(",
    "DOI(",
    "SRCTITLE(",
    "ALL(",
)


def build_scopus_query(
    query: str,
    year: str | int | None = None,
    open_access: bool = False,
    institution: str | None = None,
) -> str:
    """Construct a formatted Scopus search query string.

    Args:
        query: Base query or field-coded expression.
        year: Optional publication year to restrict results.
        open_access: Whether to restrict results to open access.
        institution: Optional institution affiliation name.

    Returns:
        Formatted Scopus query string.
    """
    parts = []

    if institution:
        parts.append(f'AFFIL("{institution}")')

    if query:
        if any(code in query.upper() for code in FIELD_CODES):
            parts.append(query)
        else:
            parts.append(f"TITLE-ABS-KEY({query})")

    if open_access:
        parts.append("OPENACCESS(1)")

    if year:
        year_str = str(year)
        combined_so_far = " ".join(parts).upper()
        if "PUBYEAR" not in combined_so_far:
            parts.append(f"PUBYEAR = {year_str}")

    return " AND ".join(parts)


def parse_paper_entry(entry: dict[str, Any], open_access: bool = False) -> dict[str, Any]:
    """Extract standard paper metadata from a Scopus search result entry.

    Args:
        entry: Scopus search entry dictionary.
        open_access: Whether this entry is known to be open access.

    Returns:
        Normalized paper dictionary.
    """
    raw_citations = entry.get("citedby-count", 0)
    try:
        citations = int(raw_citations)
    except (ValueError, TypeError):
        citations = 0

    paper: dict[str, Any] = {
        "title": entry.get("dc:title", "No title"),
        "authors": entry.get("dc:creator", "Unknown"),
        "journal": entry.get("prism:publicationName", "Unknown"),
        "year": entry.get("prism:coverDate", ""),
        "citations": citations,
        "doi": entry.get("prism:doi", ""),
        "eid": entry.get("eid", ""),
    }
    if open_access:
        paper["open_access"] = True
    return paper


def define_tools() -> dict[str, dict[str, Any]]:
    """Define available MCP tools and their input schemas compliant with MCP specification.

    Returns:
        Dictionary of tool definitions keyed by tool name.
    """
    return {
        "search_papers": {
            "name": "search_papers",
            "description": "Scopus論文データベースから論文を検索します。キーワード、著者名、年度等で検索可能。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "検索キーワード（例: 'machine learning', '著者名', '分野名'）",
                    },
                    "count": {
                        "type": "integer",
                        "description": "取得件数（最大25）",
                        "minimum": 1,
                        "maximum": 25,
                    },
                    "year": {
                        "type": "string",
                        "description": "発行年（YYYY形式）",
                    },
                },
                "required": ["query"],
            },
        },
        "get_paper_abstract": {
            "name": "get_paper_abstract",
            "description": "論文のEIDまたはDOIから詳細な抄録とメタデータを取得します。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "eid": {
                        "type": "string",
                        "description": "論文のElsevier ID（EID）",
                    },
                    "doi": {
                        "type": "string",
                        "description": "論文のDigital Object Identifier（DOI）",
                    },
                },
            },
        },
        "get_author_info": {
            "name": "get_author_info",
            "description": "著者IDから研究者の詳細プロファイルを取得します。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "author_id": {
                        "type": "string",
                        "description": "Scopus著者ID",
                    },
                },
                "required": ["author_id"],
            },
        },
        "analyze_research_trends": {
            "name": "analyze_research_trends",
            "description": "指定された研究分野の年別論文数推移を分析します。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "field": {
                        "type": "string",
                        "description": "研究分野キーワード（例: 'artificial intelligence', 'quantum computing'）",
                    },
                    "years": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "分析対象年のリスト（例: [2022, 2023, 2024]）",
                    },
                },
                "required": ["field"],
            },
        },
        "get_institution_papers": {
            "name": "get_institution_papers",
            "description": "指定された機関の論文統計と最新論文リストを取得します。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "institution": {
                        "type": "string",
                        "description": "機関名（例: 'MIT', 'Stanford University'）",
                    },
                    "year": {
                        "type": "integer",
                        "description": "対象年",
                    },
                },
                "required": ["institution"],
            },
        },
        "search_open_access_papers": {
            "name": "search_open_access_papers",
            "description": "指定された分野のオープンアクセス論文を検索します。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "field": {
                        "type": "string",
                        "description": "研究分野（例: 'machine learning', 'climate change'）",
                    },
                    "count": {
                        "type": "integer",
                        "description": "取得件数",
                        "minimum": 1,
                        "maximum": 20,
                    },
                    "year": {
                        "type": "integer",
                        "description": "発行年（デフォルトは現在の年）",
                    },
                },
                "required": ["field"],
            },
        },
        "get_journal_metrics": {
            "name": "get_journal_metrics",
            "description": (
                "Scopus収録ジャーナルの評価指標（CiteScore、SJR、SNIP、Q1-Q4クォータイル、"
                "オープンアクセス区分）を取得します。雑誌名またはISSNで検索可能。"
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "学術誌・ジャーナル名（例: 'Nature', 'Machine Learning', 'IEEE Access'）",
                    },
                    "issn": {
                        "type": "string",
                        "description": "ジャーナルのISSNまたはE-ISSN（例: '0885-6125', '0028-0836'）",
                    },
                },
            },
        },
    }


class ToolHandlers:
    """Executes Elsevier MCP tool requests using an async API client."""

    def __init__(self, client: ElsevierAPIClient | None = None) -> None:
        """Initialize handlers with an API client.

        Args:
            client: ElsevierAPIClient instance. If None, a default instance is created.
        """
        self.client = client or ElsevierAPIClient()

    async def search_papers(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """論文検索 (Search Scopus papers by query, count, and year).

        Args:
            arguments: Tool arguments containing query, optional count and year.

        Returns:
            Dict containing success status, paper items, and total count.
        """
        try:
            params_input = SearchPapersInput(**arguments)
        except ValidationError as exc:
            return {"success": False, "error": f"Validation error: {exc}"}

        search_query = build_scopus_query(params_input.query, year=params_input.year)
        params = {
            "query": search_query,
            "count": min(params_input.count, 25),
            "sort": "citedby-count",
        }

        try:
            response = await self.client.get("/content/search/scopus", params=params)
            if response.is_success:
                data = response.json()
                entries = data.get("search-results", {}).get("entry", [])
                raw_total = data.get("search-results", {}).get("opensearch:totalResults", 0)
                try:
                    total = int(raw_total)
                except (ValueError, TypeError):
                    total = 0

                results = [parse_paper_entry(entry) for entry in entries]
                return {
                    "success": True,
                    "total_results": total,
                    "papers": results,
                    "query": params_input.query,
                }
            return {"success": False, "error": f"API Error: {response.status_code}"}
        except Exception as exc:
            logger.exception("search_papers failed")
            return {"success": False, "error": str(exc)}

    async def get_paper_abstract(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """論文抄録取得 (Retrieve paper abstract by EID or DOI).

        Args:
            arguments: Tool arguments containing eid and/or doi.

        Returns:
            Dict containing success status and paper abstract metadata.
        """
        try:
            params_input = GetPaperAbstractInput(**arguments)
        except ValidationError as exc:
            return {"success": False, "error": f"Validation error: {exc}"}

        if params_input.eid:
            path = f"/content/abstract/eid/{params_input.eid}"
        else:
            path = f"/content/abstract/doi/{params_input.doi}"

        try:
            response = await self.client.get(path)
            if response.is_success:
                data = response.json()
                abstract_response = data.get("abstracts-retrieval-response", {})
                coredata = abstract_response.get("coredata", {})

                result = {
                    "title": coredata.get("dc:title", "No title"),
                    "abstract": coredata.get("dc:description", "No abstract"),
                    "authors": coredata.get("dc:creator", "Unknown"),
                    "journal": coredata.get("prism:publicationName", "Unknown"),
                    "year": coredata.get("prism:coverDate", ""),
                    "doi": coredata.get("prism:doi", ""),
                    "eid": coredata.get("eid", ""),
                    "citations": str(coredata.get("citedby-count", "0")),
                }
                return {"success": True, "paper": result}
            return {"success": False, "error": f"API Error: {response.status_code}"}
        except Exception as exc:
            logger.exception("get_paper_abstract failed")
            return {"success": False, "error": str(exc)}

    async def get_author_info(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """著者情報取得 (Retrieve researcher profile by Scopus author ID).

        Args:
            arguments: Tool arguments containing author_id.

        Returns:
            Dict containing success status and author profile.
        """
        try:
            params_input = GetAuthorInfoInput(**arguments)
        except ValidationError as exc:
            return {"success": False, "error": f"Validation error: {exc}"}

        path = f"/analytics/scival/author/{params_input.author_id}"

        try:
            response = await self.client.get(path)
            if response.is_success:
                data = response.json()
                author_data = data.get("author", {})

                result = {
                    "author_id": params_input.author_id,
                    "name": author_data.get("name", "Unknown"),
                    "current_institution": author_data.get("currentInstitutionName", "Unknown"),
                    "scopus_url": author_data.get("link", {}).get("@href", ""),
                }
                return {"success": True, "author": result}
            return {"success": False, "error": f"API Error: {response.status_code}"}
        except Exception as exc:
            logger.exception("get_author_info failed")
            return {"success": False, "error": str(exc)}

    async def analyze_research_trends(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """研究分野トレンド分析 (Analyze multi-year research trend and growth rates).

        Args:
            arguments: Tool arguments containing field and years list.

        Returns:
            Dict containing success status, yearly publication counts, and growth rates.
        """
        try:
            params_input = AnalyzeResearchTrendsInput(**arguments)
        except ValidationError as exc:
            return {"success": False, "error": f"Validation error: {exc}"}

        yearly_data: dict[int, int] = {}

        try:
            for year in params_input.years:
                query = f"TITLE-ABS-KEY({params_input.field}) AND PUBYEAR = {year}"
                params = {"query": query, "count": 1}
                response = await self.client.get("/content/search/scopus", params=params)
                if response.is_success:
                    data = response.json()
                    raw_total = data.get("search-results", {}).get("opensearch:totalResults", 0)
                    try:
                        total = int(raw_total)
                    except (ValueError, TypeError):
                        total = 0
                    yearly_data[year] = total
                else:
                    return {"success": False, "error": f"API Error {response.status_code} for year {year}"}

            growth_rates: dict[str, float] = {}
            years_sorted = sorted(yearly_data.keys())
            for i in range(1, len(years_sorted)):
                prev_year = years_sorted[i - 1]
                curr_year = years_sorted[i]
                if yearly_data[prev_year] > 0:
                    growth_rate = ((yearly_data[curr_year] - yearly_data[prev_year]) / yearly_data[prev_year]) * 100
                    growth_rates[f"{prev_year}-{curr_year}"] = round(growth_rate, 2)

            return {
                "success": True,
                "field": params_input.field,
                "yearly_papers": yearly_data,
                "growth_rates": growth_rates,
                "total_papers": sum(yearly_data.values()),
            }
        except Exception as exc:
            logger.exception("analyze_research_trends failed")
            return {"success": False, "error": str(exc)}

    async def get_institution_papers(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """機関論文統計 (Retrieve publication statistics for an academic institution).

        Args:
            arguments: Tool arguments containing institution name and year.

        Returns:
            Dict containing success status, total publication count, and top cited papers.
        """
        try:
            params_input = GetInstitutionPapersInput(**arguments)
        except ValidationError as exc:
            return {"success": False, "error": f"Validation error: {exc}"}

        query = f'AFFIL("{params_input.institution}") AND PUBYEAR = {params_input.year}'
        params = {
            "query": query,
            "count": 5,
            "sort": "citedby-count",
        }

        try:
            response = await self.client.get("/content/search/scopus", params=params)
            if response.is_success:
                data = response.json()
                entries = data.get("search-results", {}).get("entry", [])
                raw_total = data.get("search-results", {}).get("opensearch:totalResults", 0)
                try:
                    total = int(raw_total)
                except (ValueError, TypeError):
                    total = 0

                top_papers = []
                for entry in entries:
                    raw_cites = entry.get("citedby-count", 0)
                    try:
                        cites = int(raw_cites)
                    except (ValueError, TypeError):
                        cites = 0
                    top_papers.append({
                        "title": entry.get("dc:title", "No title"),
                        "authors": entry.get("dc:creator", "Unknown"),
                        "journal": entry.get("prism:publicationName", "Unknown"),
                        "citations": cites,
                        "doi": entry.get("prism:doi", ""),
                    })

                return {
                    "success": True,
                    "institution": params_input.institution,
                    "year": params_input.year,
                    "total_papers": total,
                    "top_papers": top_papers,
                }
            return {"success": False, "error": f"API Error: {response.status_code}"}
        except Exception as exc:
            logger.exception("get_institution_papers failed")
            return {"success": False, "error": str(exc)}

    async def search_open_access_papers(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """オープンアクセス論文検索 (Search open access papers in a given field).

        Args:
            arguments: Tool arguments containing field and count.

        Returns:
            Dict containing success status, open access papers list, and total count.
        """
        try:
            params_input = SearchOpenAccessPapersInput(**arguments)
        except ValidationError as exc:
            return {"success": False, "error": f"Validation error: {exc}"}

        target_year = params_input.year if params_input.year is not None else datetime.now().year
        query = f"TITLE-ABS-KEY({params_input.field}) AND OPENACCESS(1) AND PUBYEAR = {target_year}"
        params = {
            "query": query,
            "count": min(params_input.count, 20),
            "sort": "citedby-count",
        }

        try:
            response = await self.client.get("/content/search/scopus", params=params)
            if response.is_success:
                data = response.json()
                entries = data.get("search-results", {}).get("entry", [])
                raw_total = data.get("search-results", {}).get("opensearch:totalResults", 0)
                try:
                    total = int(raw_total)
                except (ValueError, TypeError):
                    total = 0

                papers = [parse_paper_entry(entry, open_access=True) for entry in entries]
                return {
                    "success": True,
                    "field": params_input.field,
                    "total_open_access": total,
                    "papers": papers,
                }
            return {"success": False, "error": f"API Error: {response.status_code}"}
        except Exception as exc:
            logger.exception("search_open_access_papers failed")
            return {"success": False, "error": str(exc)}

    async def get_journal_metrics(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """学術雑誌・ジャーナル評価指標取得 (Retrieve CiteScore, SJR, SNIP, and Quartiles).

        Args:
            arguments: Tool arguments containing journal title or ISSN.

        Returns:
            Dict containing success status and journal metrics.
        """
        try:
            params_input = GetJournalMetricsInput(**arguments)
        except ValidationError as exc:
            return {"success": False, "error": f"Validation error: {exc}"}

        params: dict[str, Any] = {"view": "CITESCORE", "count": 1}
        if params_input.issn:
            params["issn"] = params_input.issn
        elif params_input.title:
            params["title"] = params_input.title

        try:
            response = await self.client.get("/content/serial/title", params=params)
            if response.is_success:
                data = response.json()
                entries = data.get("serial-metadata-response", {}).get("entry", [])
                if not entries:
                    ident = f"title='{params_input.title}'" if params_input.title else f"issn='{params_input.issn}'"
                    return {"success": False, "error": f"Journal not found for query ({ident})"}

                entry = entries[0]
                citescore_info = entry.get("citeScoreYearInfoList", {}) or {}
                citescore_current = citescore_info.get("citeScoreCurrentMetric")
                citescore_current_year = citescore_info.get("citeScoreCurrentMetricYear")
                citescore_tracker = citescore_info.get("citeScoreTracker")
                citescore_tracker_year = citescore_info.get("citeScoreTrackerYear")

                sjr_list = entry.get("SJRList", {}).get("SJR", []) if isinstance(entry.get("SJRList"), dict) else []
                sjr_val = sjr_list[0].get("$") if sjr_list and isinstance(sjr_list, list) and isinstance(sjr_list[0], dict) else None
                sjr_year = sjr_list[0].get("@year") if sjr_list and isinstance(sjr_list, list) and isinstance(sjr_list[0], dict) else None

                snip_list = entry.get("SNIPList", {}).get("SNIP", []) if isinstance(entry.get("SNIPList"), dict) else []
                snip_val = snip_list[0].get("$") if snip_list and isinstance(snip_list, list) and isinstance(snip_list[0], dict) else None
                snip_year = snip_list[0].get("@year") if snip_list and isinstance(snip_list, list) and isinstance(snip_list[0], dict) else None

                subject_rankings: list[dict[str, Any]] = []
                best_quartile: str | None = None

                year_info_list = citescore_info.get("citeScoreYearInfo", [])
                if isinstance(year_info_list, list) and year_info_list:
                    latest_year_data = next((y for y in year_info_list if y.get("@status") == "Complete"), year_info_list[0])
                    info_list = latest_year_data.get("citeScoreInformationList", [])
                    if isinstance(info_list, list) and info_list:
                        score_info = info_list[0].get("citeScoreInfo", [])
                        if isinstance(score_info, list) and score_info:
                            ranks = score_info[0].get("citeScoreSubjectRank", [])
                            if isinstance(ranks, list):
                                for r in ranks:
                                    if isinstance(r, dict):
                                        perc_str = r.get("percentile", "0")
                                        try:
                                            perc = float(perc_str)
                                        except (ValueError, TypeError):
                                            perc = 0.0

                                        if perc >= 75:
                                            q = "Q1"
                                        elif perc >= 50:
                                            q = "Q2"
                                        elif perc >= 25:
                                            q = "Q3"
                                        else:
                                            q = "Q4"

                                        if best_quartile is None or q < best_quartile:
                                            best_quartile = q

                                        rank_val = r.get("rank")
                                        parsed_rank = int(rank_val) if str(rank_val).isdigit() else rank_val
                                        subject_rankings.append({
                                            "subject_code": r.get("subjectCode"),
                                            "rank": parsed_rank,
                                            "percentile": perc,
                                            "quartile": q,
                                        })

                result = {
                    "title": entry.get("dc:title", "Unknown Title"),
                    "publisher": entry.get("dc:publisher", "Unknown Publisher"),
                    "issn": entry.get("prism:issn", ""),
                    "eissn": entry.get("prism:eIssn", ""),
                    "aggregation_type": entry.get("prism:aggregationType", "Journal"),
                    "open_access": entry.get("openaccess") == "1",
                    "citescore": {
                        "current": float(citescore_current) if citescore_current is not None else None,
                        "year": citescore_current_year,
                        "tracker": float(citescore_tracker) if citescore_tracker is not None else None,
                        "tracker_year": citescore_tracker_year,
                    },
                    "sjr": {
                        "value": float(sjr_val) if sjr_val is not None else None,
                        "year": sjr_year,
                    },
                    "snip": {
                        "value": float(snip_val) if snip_val is not None else None,
                        "year": snip_year,
                    },
                    "best_quartile": best_quartile,
                    "subject_rankings": subject_rankings,
                }
                return {"success": True, "journal": result}
            return {"success": False, "error": f"API Error {response.status_code}: {response.text[:200]}"}
        except Exception as exc:
            logger.exception("get_journal_metrics failed")
            return {"success": False, "error": str(exc)}
