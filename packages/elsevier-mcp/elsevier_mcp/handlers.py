"""Tool handlers and Elsevier API integration logic."""

import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

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


def _to_int(raw: Any, default: int = 0) -> int:
    """Coerce an Elsevier string/numeric field to int, falling back on garbage.

    Args:
        raw: Raw field value (Elsevier often sends numbers as strings).
        default: Value returned when coercion fails.

    Returns:
        Integer value, or ``default``.
    """
    try:
        return int(raw)
    except (ValueError, TypeError):
        return default


def _parse_total_results(data: dict[str, Any]) -> int:
    """Extract ``opensearch:totalResults`` from a Scopus search response as int.

    Args:
        data: Parsed Scopus search response body.

    Returns:
        Total result count, or 0 when absent/unparseable.
    """
    raw_total = data.get("search-results", {}).get("opensearch:totalResults", 0)
    return _to_int(raw_total)


def _validated(
    model_cls: type[BaseModel], arguments: dict[str, Any]
) -> tuple[BaseModel | None, dict[str, Any] | None]:
    """Validate tool arguments against a Pydantic input model.

    Args:
        model_cls: Pydantic input model class.
        arguments: Raw tool arguments.

    Returns:
        ``(model, None)`` when valid, else ``(None, error-dict)``.
    """
    try:
        return model_cls(**arguments), None
    except ValidationError as exc:
        return None, {"success": False, "error": f"Validation error: {exc}"}


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


def _parse_author_names(creator_data: Any) -> str:
    """Normalize author creator field from Scopus entry or abstract into readable string.

    Args:
        creator_data: String, dict, or list representation of author(s).

    Returns:
        Comma-separated string of author names.
    """
    if not creator_data:
        return "Unknown"
    if isinstance(creator_data, str):
        return creator_data
    if isinstance(creator_data, dict):
        authors = creator_data.get("author", [])
        if isinstance(authors, list):
            names: list[str] = []
            for a in authors:
                if isinstance(a, dict):
                    name = (
                        a.get("preferred-name", {}).get("ce:indexed-name")
                        or a.get("ce:indexed-name")
                    )
                    if not name:
                        surname = a.get("ce:surname", "")
                        given = a.get("ce:given-name", "")
                        name = f"{surname} {given}".strip()
                    if name:
                        names.append(name)
                elif isinstance(a, str):
                    names.append(a)
            return ", ".join(names) if names else "Unknown"
        if isinstance(authors, dict):
            return _parse_author_names(authors)
    if isinstance(creator_data, list):
        return ", ".join(str(x) for x in creator_data if x)
    return str(creator_data)


def parse_paper_entry(entry: dict[str, Any], open_access: bool = False) -> dict[str, Any]:
    """Extract standard paper metadata from a Scopus search result entry.

    Args:
        entry: Scopus search entry dictionary.
        open_access: Whether this entry is known to be open access.

    Returns:
        Normalized paper dictionary.
    """
    raw_citations = entry.get("citedby-count", 0)
    citations = _to_int(raw_citations)

    paper: dict[str, Any] = {
        "title": entry.get("dc:title", "No title"),
        "authors": _parse_author_names(entry.get("dc:creator")),
        "journal": entry.get("prism:publicationName", "Unknown"),
        "year": entry.get("prism:coverDate", ""),
        "citations": citations,
        "doi": entry.get("prism:doi", ""),
        "eid": entry.get("eid", ""),
    }
    if open_access:
        paper["open_access"] = True
    return paper


def _parse_metric_list(entry: dict[str, Any], list_key: str, item_key: str) -> tuple[Any, Any]:
    """Extract a single metric value/year pair from an SJRList/SNIPList structure.

    Args:
        entry: Serial metadata entry.
        list_key: Either ``"SJRList"`` or ``"SNIPList"``.
        item_key: Either ``"SJR"`` or ``"SNIP"``.

    Returns:
        ``(value, year)`` tuple; either element may be None when absent.
    """
    container = entry.get(list_key)
    metric_list = container.get(item_key, []) if isinstance(container, dict) else []
    if metric_list and isinstance(metric_list, list) and isinstance(metric_list[0], dict):
        return metric_list[0].get("$"), metric_list[0].get("@year")
    return None, None


def _quartile_from_percentile(percentile: float) -> str:
    """Map a percentile score (0-100) to its quartile label (Q1-Q4)."""
    if percentile >= 75:
        return "Q1"
    if percentile >= 50:
        return "Q2"
    if percentile >= 25:
        return "Q3"
    return "Q4"


def _parse_subject_rankings(citescore_info: dict[str, Any]) -> tuple[list[dict[str, Any]], str | None]:
    """Parse subject rankings and best quartile from CiteScore year info.

    Args:
        citescore_info: ``citeScoreYearInfoList`` value from the serial entry.

    Returns:
        ``(subject_rankings, best_quartile)``; best_quartile is None when no
        complete ranking data is present.
    """
    subject_rankings: list[dict[str, Any]] = []
    best_quartile: str | None = None

    year_info_list = citescore_info.get("citeScoreYearInfo", [])
    if not (isinstance(year_info_list, list) and year_info_list):
        return subject_rankings, best_quartile

    latest_year_data = next((y for y in year_info_list if y.get("@status") == "Complete"), year_info_list[0])
    info_list = latest_year_data.get("citeScoreInformationList", [])
    if not (isinstance(info_list, list) and info_list):
        return subject_rankings, best_quartile

    score_info = info_list[0].get("citeScoreInfo", [])
    if not (isinstance(score_info, list) and score_info):
        return subject_rankings, best_quartile

    ranks = score_info[0].get("citeScoreSubjectRank", [])
    if not isinstance(ranks, list):
        return subject_rankings, best_quartile

    for r in ranks:
        if not isinstance(r, dict):
            continue
        try:
            perc = float(r.get("percentile", "0"))
        except (ValueError, TypeError):
            perc = 0.0

        q = _quartile_from_percentile(perc)
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

    return subject_rankings, best_quartile


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

    async def _fetch_json(
        self,
        tool_name: str,
        path: str,
        params: dict[str, Any] | None = None,
        error_message: Callable[[httpx.Response], str] | None = None,
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """GET a JSON payload from the Elsevier API with unified error handling.

        Args:
            tool_name: Tool name used in exception logging.
            path: API path to request.
            params: Optional query parameters.
            error_message: Optional formatter for non-success responses;
                defaults to ``API Error: {status_code}``.

        Returns:
            ``(data, None)`` on success, else ``(None, error-dict)``. Errors are
            always returned as dicts, never raised to the caller.
        """
        try:
            response = await self.client.get(path, params=params)
            if response.is_success:
                return response.json(), None
            message = error_message(response) if error_message else f"API Error: {response.status_code}"
            return None, {"success": False, "error": message}
        except Exception as exc:
            logger.exception("%s failed", tool_name)
            return None, {"success": False, "error": str(exc)}

    async def search_papers(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """論文検索 (Search Scopus papers by query, count, and year).

        Args:
            arguments: Tool arguments containing query, optional count and year.

        Returns:
            Dict containing success status, paper items, and total count.
        """
        params_input, error = _validated(SearchPapersInput, arguments)
        if error:
            return error

        assert params_input is not None
        search_query = build_scopus_query(params_input.query, year=params_input.year)
        params = {
            "query": search_query,
            "count": min(params_input.count, 25),
            "sort": "citedby-count",
        }

        data, error = await self._fetch_json("search_papers", "/content/search/scopus", params=params)
        if error:
            return error

        assert data is not None
        entries = data.get("search-results", {}).get("entry", [])
        total = _parse_total_results(data)
        results = [parse_paper_entry(entry) for entry in entries]
        return {
            "success": True,
            "total_results": total,
            "papers": results,
            "query": params_input.query,
        }

    async def get_paper_abstract(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """論文抄録取得 (Retrieve paper abstract by EID or DOI).

        Args:
            arguments: Tool arguments containing eid and/or doi.

        Returns:
            Dict containing success status and paper abstract metadata.
        """
        params_input, error = _validated(GetPaperAbstractInput, arguments)
        if error:
            return error

        assert params_input is not None
        if params_input.eid:
            path = f"/content/abstract/eid/{params_input.eid}"
        else:
            path = f"/content/abstract/doi/{params_input.doi}"

        data, error = await self._fetch_json("get_paper_abstract", path)
        if error:
            return error

        assert data is not None
        abstract_response = data.get("abstracts-retrieval-response", {})
        coredata = abstract_response.get("coredata", {})

        raw_abstract = coredata.get("dc:description")
        abstract_text = (
            raw_abstract
            if raw_abstract and str(raw_abstract).strip() != "No abstract"
            else (
                "Full narrative abstract is not available in basic view. Access typically requires an institutional "
                "subscription (ELSEVIER_INSTTOKEN). You can view full article details and open access full-text via "
                "the DOI link."
            )
        )

        result = {
            "title": coredata.get("dc:title", "No title"),
            "abstract": abstract_text,
            "authors": _parse_author_names(coredata.get("dc:creator")),
            "journal": coredata.get("prism:publicationName", "Unknown"),
            "year": coredata.get("prism:coverDate", ""),
            "doi": coredata.get("prism:doi", ""),
            "eid": coredata.get("eid", ""),
            "citations": str(coredata.get("citedby-count", "0")),
        }
        return {"success": True, "paper": result}

    async def get_author_info(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """著者情報取得 (Retrieve researcher profile by Scopus author ID).

        Args:
            arguments: Tool arguments containing author_id.

        Returns:
            Dict containing success status and author profile.
        """
        params_input, error = _validated(GetAuthorInfoInput, arguments)
        if error:
            return error

        assert params_input is not None
        path = f"/analytics/scival/author/{params_input.author_id}"

        data, error = await self._fetch_json("get_author_info", path)
        if error:
            return error

        assert data is not None
        author_data = data.get("author", {})

        result = {
            "author_id": params_input.author_id,
            "name": author_data.get("name", "Unknown"),
            "current_institution": author_data.get("currentInstitutionName", "Unknown"),
            "scopus_url": author_data.get("link", {}).get("@href", ""),
        }
        return {"success": True, "author": result}

    async def analyze_research_trends(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """研究分野トレンド分析 (Analyze multi-year research trend and growth rates).

        Args:
            arguments: Tool arguments containing field and years list.

        Returns:
            Dict containing success status, yearly publication counts, and growth rates.
        """
        params_input, error = _validated(AnalyzeResearchTrendsInput, arguments)
        if error:
            return error

        assert params_input is not None
        yearly_data: dict[int, int] = {}

        for year in params_input.years:
            query = f"TITLE-ABS-KEY({params_input.field}) AND PUBYEAR = {year}"
            params = {"query": query, "count": 1}
            data, error = await self._fetch_json(
                "analyze_research_trends",
                "/content/search/scopus",
                params=params,
                error_message=lambda resp, y=year: f"API Error {resp.status_code} for year {y}",
            )
            if error:
                return error

            assert data is not None
            yearly_data[year] = _parse_total_results(data)

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

    async def get_institution_papers(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """機関論文統計 (Retrieve publication statistics for an academic institution).

        Args:
            arguments: Tool arguments containing institution name and year.

        Returns:
            Dict containing success status, total publication count, and top cited papers.
        """
        params_input, error = _validated(GetInstitutionPapersInput, arguments)
        if error:
            return error

        assert params_input is not None
        query = f'AFFIL("{params_input.institution}") AND PUBYEAR = {params_input.year}'
        params = {
            "query": query,
            "count": 5,
            "sort": "citedby-count",
        }

        data, error = await self._fetch_json("get_institution_papers", "/content/search/scopus", params=params)
        if error:
            return error

        assert data is not None
        entries = data.get("search-results", {}).get("entry", [])
        total = _parse_total_results(data)

        top_papers = []
        for entry in entries:
            top_papers.append({
                "title": entry.get("dc:title", "No title"),
                "authors": entry.get("dc:creator", "Unknown"),
                "journal": entry.get("prism:publicationName", "Unknown"),
                "citations": _to_int(entry.get("citedby-count", 0)),
                "doi": entry.get("prism:doi", ""),
            })

        return {
            "success": True,
            "institution": params_input.institution,
            "year": params_input.year,
            "total_papers": total,
            "top_papers": top_papers,
        }

    async def search_open_access_papers(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """オープンアクセス論文検索 (Search open access papers in a given field).

        Args:
            arguments: Tool arguments containing field and count.

        Returns:
            Dict containing success status, open access papers list, and total count.
        """
        params_input, error = _validated(SearchOpenAccessPapersInput, arguments)
        if error:
            return error

        assert params_input is not None
        target_year = params_input.year if params_input.year is not None else datetime.now().year
        query = f"TITLE-ABS-KEY({params_input.field}) AND OPENACCESS(1) AND PUBYEAR = {target_year}"
        params = {
            "query": query,
            "count": min(params_input.count, 20),
            "sort": "citedby-count",
        }

        data, error = await self._fetch_json("search_open_access_papers", "/content/search/scopus", params=params)
        if error:
            return error

        assert data is not None
        entries = data.get("search-results", {}).get("entry", [])
        total = _parse_total_results(data)

        papers = [parse_paper_entry(entry, open_access=True) for entry in entries]
        return {
            "success": True,
            "field": params_input.field,
            "total_open_access": total,
            "papers": papers,
        }

    async def get_journal_metrics(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """学術雑誌・ジャーナル評価指標取得 (Retrieve CiteScore, SJR, SNIP, and Quartiles).

        Args:
            arguments: Tool arguments containing journal title or ISSN.

        Returns:
            Dict containing success status and journal metrics.
        """
        params_input, error = _validated(GetJournalMetricsInput, arguments)
        if error:
            return error

        assert params_input is not None
        params: dict[str, Any] = {"view": "CITESCORE", "count": 1}
        if params_input.issn:
            params["issn"] = params_input.issn
        elif params_input.title:
            params["title"] = params_input.title

        data, error = await self._fetch_json(
            "get_journal_metrics",
            "/content/serial/title",
            params=params,
            error_message=lambda resp: f"API Error {resp.status_code}: {resp.text[:200]}",
        )
        if error:
            return error

        assert data is not None
        entries = data.get("serial-metadata-response", {}).get("entry", [])
        if not entries:
            ident = f"title='{params_input.title}'" if params_input.title else f"issn='{params_input.issn}'"
            return {"success": False, "error": f"Journal not found for query ({ident})"}

        entry = entries[0]
        citescore_info = entry.get("citeScoreYearInfoList", {}) or {}

        sjr_val, sjr_year = _parse_metric_list(entry, "SJRList", "SJR")
        snip_val, snip_year = _parse_metric_list(entry, "SNIPList", "SNIP")
        subject_rankings, best_quartile = _parse_subject_rankings(citescore_info)

        citescore_current = citescore_info.get("citeScoreCurrentMetric")
        citescore_tracker = citescore_info.get("citeScoreTracker")

        result = {
            "title": entry.get("dc:title", "Unknown Title"),
            "publisher": entry.get("dc:publisher", "Unknown Publisher"),
            "issn": entry.get("prism:issn", ""),
            "eissn": entry.get("prism:eIssn", ""),
            "aggregation_type": entry.get("prism:aggregationType", "Journal"),
            "open_access": entry.get("openaccess") == "1",
            "citescore": {
                "current": float(citescore_current) if citescore_current is not None else None,
                "year": citescore_info.get("citeScoreCurrentMetricYear"),
                "tracker": float(citescore_tracker) if citescore_tracker is not None else None,
                "tracker_year": citescore_info.get("citeScoreTrackerYear"),
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
