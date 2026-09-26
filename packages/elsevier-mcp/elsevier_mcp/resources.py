"""MCP resource and resource template definitions and content providers."""

from datetime import datetime
from typing import Any
from urllib.parse import unquote

from elsevier_mcp.handlers import ToolHandlers


def define_resources() -> list[dict[str, Any]]:
    """Define static resources exposed by the MCP server.

    Returns:
        List of resource descriptors compliant with MCP protocol.
    """
    return [
        {
            "uri": "elsevier://docs/scopus-search-syntax",
            "name": "Scopus Search API Query Syntax Reference",
            "description": (
                "Official Scopus search query syntax, boolean operators, "
                "field codes, and proximity operators reference guide."
            ),
            "mimeType": "text/markdown",
        }
    ]


def define_resource_templates() -> list[dict[str, Any]]:
    """Define dynamic URI templates for MCP resources.

    Returns:
        List of resource template descriptors compliant with MCP protocol.
    """
    return [
        {
            "uriTemplate": "elsevier://paper/{eid}",
            "name": "Scopus Paper Abstract & Metadata",
            "description": (
                "Dynamic resource retrieving paper abstract, authors, "
                "journal metadata, DOI, and citations by Scopus EID."
            ),
            "mimeType": "text/markdown",
        },
        {
            "uriTemplate": "elsevier://trends/{field}",
            "name": "Research Field Publication Trends",
            "description": (
                "Dynamic resource providing multi-year publication volume "
                "and growth statistics for a research field."
            ),
            "mimeType": "text/markdown",
        },
        {
            "uriTemplate": "elsevier://journal/{query}",
            "name": "Scopus Journal Metrics & Impact Report",
            "description": (
                "Dynamic resource providing CiteScore, SJR, SNIP, "
                "and Quartiles (Q1-Q4) for a journal title or ISSN."
            ),
            "mimeType": "text/markdown",
        },
    ]


async def read_resource(uri: str, handlers: ToolHandlers) -> dict[str, Any]:
    """Read and render MCP resource content for a given URI.

    Args:
        uri: The resource URI to fetch.
        handlers: ToolHandlers instance to execute underlying data queries.

    Returns:
        Dictionary containing contents list compliant with MCP protocol.

    Raises:
        ValueError: If URI is unknown or unsupported.
    """
    if uri == "elsevier://docs/scopus-search-syntax":
        content = (
            "# Scopus Search API Query Syntax Guide\n\n"
            "## 1. Field Codes\n"
            "- `TITLE-ABS-KEY(query)`: Search in Title, Abstract, and Keywords (default for general search).\n"
            "- `TITLE(query)`: Search in Article Title only.\n"
            "- `ABS(query)`: Search in Abstract text only.\n"
            "- `KEY(query)`: Search in Author Keywords and Index Terms.\n"
            "- `AUTH(author_name)` / `AUTHOR-NAME(author_name)`: Search by author name.\n"
            "- `AFFIL(\"Institution Name\")`: Search by institutional affiliation (*Always quote multi-word names*).\n"
            "- `AFFILCITY(\"City\")`: Search by affiliation city.\n"
            "- `AFFILCOUNTRY(\"Country\")`: Search by affiliation country.\n"
            "- `DOI(10.xxxx/yyyy)`: Search by Digital Object Identifier.\n"
            "- `SRCTITLE(\"Journal Name\")`: Search by Source/Publication name.\n"
            "- `PUBYEAR = YYYY`: Filter by specific publication year (e.g., `PUBYEAR = 2024`).\n"
            "- `OPENACCESS(1)`: Filter for Open Access publications.\n\n"
            "## 2. Boolean & Proximity Operators\n"
            "- `AND`, `OR`, `AND NOT` (must be uppercase).\n"
            "- `W/n`: Words within `n` words of each other in any order (e.g., `neural W/3 network`).\n"
            "- `PRE/n`: First word precedes second word within `n` words.\n\n"
            "## 3. Best Practices\n"
            "- Wrap multi-word terms in double quotes (e.g., `TITLE-ABS-KEY(\"deep learning\")`).\n"
            "- Combine field codes: `TITLE-ABS-KEY(\"generative AI\") AND AFFIL(\"Stanford\") AND PUBYEAR = 2024`.\n"
        )
        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "text/markdown",
                    "text": content,
                }
            ]
        }

    if uri.startswith("elsevier://paper/"):
        eid = unquote(uri[len("elsevier://paper/"):])
        res = await handlers.get_paper_abstract({"eid": eid})
        if res.get("success") and "paper" in res:
            p = res["paper"]
            authors_val = p.get("authors")
            if isinstance(authors_val, dict):
                authors_list = authors_val.get("author", [])
                if isinstance(authors_list, list):
                    names = [
                        a.get("ce:indexed-name", a.get("ce:surname", "Unknown"))
                        for a in authors_list
                        if isinstance(a, dict)
                    ]
                    authors_str = ", ".join(names)
                else:
                    authors_str = str(authors_val)
            else:
                authors_str = str(authors_val)

            text = (
                f"# {p.get('title', 'No Title')}\n\n"
                f"- **Authors**: {authors_str}\n"
                f"- **Journal**: {p.get('journal', 'Unknown')}\n"
                f"- **Publication Date**: {p.get('year', 'Unknown')}\n"
                f"- **DOI**: {p.get('doi') or 'N/A'}\n"
                f"- **EID**: {p.get('eid') or eid}\n"
                f"- **Citations**: {p.get('citations', '0')}\n\n"
                f"## Abstract\n\n"
                f"{p.get('abstract', 'No abstract available.')}\n"
            )
            return {
                "contents": [
                    {"uri": uri, "mimeType": "text/markdown", "text": text}
                ]
            }
        error_msg = res.get("error", "Unknown error retrieving abstract")
        text = f"# Error\n\nFailed to fetch paper `{eid}`: {error_msg}"
        return {
            "contents": [
                {"uri": uri, "mimeType": "text/markdown", "text": text}
            ]
        }

    if uri.startswith("elsevier://trends/"):
        field = unquote(uri[len("elsevier://trends/"):])
        cur_year = datetime.now().year
        res = await handlers.analyze_research_trends({
            "field": field,
            "years": [cur_year - 2, cur_year - 1, cur_year],
        })
        if res.get("success"):
            yearly = res.get("yearly_papers", {})
            growth = res.get("growth_rates", {})
            total = res.get("total_papers", 0)

            rows = "\n".join([f"| {year} | {count:,} |" for year, count in yearly.items()])
            growth_rows = "\n".join([f"| {period} | {rate}% |" for period, rate in growth.items()])

            text = (
                f"# Research Trend Report: {field.title()}\n\n"
                f"**Total Indexed Papers (Analyzed Window)**: {total:,}\n\n"
                f"## Annual Publication Volume\n\n"
                f"| Year | Publications |\n"
                f"| :--- | :--- |\n"
                f"{rows}\n\n"
                f"## Growth Rates\n\n"
                f"| Period | Growth (%) |\n"
                f"| :--- | :--- |\n"
                f"{growth_rows}\n"
            )
            return {
                "contents": [
                    {"uri": uri, "mimeType": "text/markdown", "text": text}
                ]
            }
        error_msg = res.get("error", "Unknown error analyzing trends")
        text = f"# Error\n\nFailed to analyze trends for `{field}`: {error_msg}"
        return {
            "contents": [
                {"uri": uri, "mimeType": "text/markdown", "text": text}
            ]
        }

    if uri.startswith("elsevier://journal/"):
        query = unquote(uri[len("elsevier://journal/"):].strip())
        if any(c.isdigit() for c in query) and ("-" in query or len(query) == 8):
            res = await handlers.get_journal_metrics({"issn": query})
        else:
            res = await handlers.get_journal_metrics({"title": query})

        if res.get("success") and "journal" in res:
            j = res["journal"]
            cs = j.get("citescore", {})
            sjr = j.get("sjr", {})
            snip = j.get("snip", {})
            oa_badge = "✅ Open Access" if j.get("open_access") else "🔒 Subscription / Hybrid"

            rank_rows = "\n".join([
                f"| {r.get('subject_code')} | Rank {r.get('rank')} | {r.get('percentile')}% | **{r.get('quartile')}** |"
                for r in j.get("subject_rankings", [])
            ]) or "| N/A | N/A | N/A | N/A |"

            text = (
                f"# {j.get('title', 'Journal Metrics')}\n\n"
                f"- **Publisher**: {j.get('publisher', 'Unknown')}\n"
                f"- **ISSN**: {j.get('issn') or 'N/A'} | **E-ISSN**: {j.get('eissn') or 'N/A'}\n"
                f"- **Best Quartile**: **{j.get('best_quartile') or 'N/A'}**\n"
                f"- **Access Type**: {oa_badge}\n\n"
                f"## 📊 Citation & Impact Metrics\n\n"
                f"| Metric | Value | Year |\n"
                f"| :--- | :--- | :--- |\n"
                f"| **CiteScore (Current)** | {cs.get('current') or 'N/A'} | {cs.get('year') or 'N/A'} |\n"
                f"| **CiteScore (Tracker)** | {cs.get('tracker') or 'N/A'} | {cs.get('tracker_year') or 'N/A'} |\n"
                f"| **SCImago Journal Rank (SJR)** | {sjr.get('value') or 'N/A'} | {sjr.get('year') or 'N/A'} |\n"
                f"| **Source Normalized Impact (SNIP)** | {snip.get('value') or 'N/A'} "
                f"| {snip.get('year') or 'N/A'} |\n\n"
                f"## 🏆 Subject Category Rankings & Quartiles\n\n"
                f"| Subject Code | Rank | Percentile | Quartile |\n"
                f"| :--- | :--- | :--- | :--- |\n"
                f"{rank_rows}\n"
            )
            return {
                "contents": [
                    {"uri": uri, "mimeType": "text/markdown", "text": text}
                ]
            }
        error_msg = res.get("error", "Journal not found")
        text = f"# Error\n\nFailed to fetch journal metrics for `{query}`: {error_msg}"
        return {
            "contents": [
                {"uri": uri, "mimeType": "text/markdown", "text": text}
            ]
        }

    raise ValueError(f"Resource not found: {uri}")
