#!/usr/bin/env python3
"""
Elsevier MCP Complete Server
Cursorで使用するすべてのMCPツール機能を実装
"""

import asyncio
import json
import sys
import requests
import os

BASE_URL = "https://api.elsevier.com"
VERSION = "1.1.0"


def get_headers() -> dict:
    """Return Elsevier API request headers or raise a clear configuration error."""
    api_key = os.getenv("ELSEVIER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ELSEVIER_API_KEY environment variable is not set. "
            "Set it before calling Elsevier tools."
        )
    return {"X-ELS-APIKey": api_key, "Accept": "application/json"}

class ElsevierMCPServer:
    def __init__(self):
        self.tools = self._define_tools()
        self.prompts = self._define_prompts()
        self.resources = self._define_resources()
        self.resource_templates = self._define_resource_templates()

    def _define_tools(self):
        """全ツール定義（MCPプロトコル準拠）"""
        return {
            "search_papers": {
                "name": "search_papers",
                "description": "Scopus論文データベースから論文を検索します。キーワード、著者名、年度等で検索可能。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "検索キーワード（例: 'machine learning', '著者名', '分野名'）"
                        },
                        "count": {
                            "type": "integer",
                            "description": "取得件数（最大25）",
                            "minimum": 1,
                            "maximum": 25
                        },
                        "year": {
                            "type": "string",
                            "description": "発行年（YYYY形式）"
                        }
                    },
                    "required": ["query"]
                }
            },
            "get_paper_abstract": {
                "name": "get_paper_abstract",
                "description": "論文のEIDまたはDOIから詳細な抄録とメタデータを取得します。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "eid": {
                            "type": "string",
                            "description": "論文のElsevier ID（EID）"
                        },
                        "doi": {
                            "type": "string",
                            "description": "論文のDigital Object Identifier（DOI）"
                        }
                    }
                }
            },
            "get_author_info": {
                "name": "get_author_info",
                "description": "著者IDから研究者の詳細プロファイルを取得します。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "author_id": {
                            "type": "string",
                            "description": "Scopus著者ID"
                        }
                    },
                    "required": ["author_id"]
                }
            },
            "analyze_research_trends": {
                "name": "analyze_research_trends",
                "description": "指定された研究分野の年別論文数推移を分析します。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "field": {
                            "type": "string",
                            "description": "研究分野キーワード（例: 'artificial intelligence', 'quantum computing'）"
                        },
                        "years": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "分析対象年のリスト（例: [2022, 2023, 2024]）"
                        }
                    },
                    "required": ["field"]
                }
            },
            "get_institution_papers": {
                "name": "get_institution_papers",
                "description": "指定された機関の論文統計と最新論文リストを取得します。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "institution": {
                            "type": "string",
                            "description": "機関名（例: 'MIT', 'Stanford University'）"
                        },
                        "year": {
                            "type": "integer",
                            "description": "対象年"
                        }
                    },
                    "required": ["institution"]
                }
            },
            "search_open_access_papers": {
                "name": "search_open_access_papers",
                "description": "指定された分野のオープンアクセス論文を検索します。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "field": {
                            "type": "string",
                            "description": "研究分野（例: 'machine learning', 'climate change'）"
                        },
                        "count": {
                            "type": "integer",
                            "description": "取得件数",
                            "minimum": 1,
                            "maximum": 20
                        }
                    },
                    "required": ["field"]
                }
            }
        }

    async def search_papers(self, arguments: dict) -> dict:
        """論文検索"""
        query = arguments.get("query", "")
        count = arguments.get("count", 10)
        year = arguments.get("year", "")

        # クエリ構築: 既にフィールドコードが指定されている場合はそのまま使用、それ以外は TITLE-ABS-KEY でラップ
        field_codes = (
            "TITLE-ABS-KEY(", "AUTH(", "AUTHOR-NAME(", "AFFIL(", "AFFILORG(",
            "TITLE(", "ABS(", "KEY(", "DOI(", "SRCTITLE(", "ALL("
        )
        if any(code in query.upper() for code in field_codes):
            search_query = query
        else:
            search_query = f"TITLE-ABS-KEY({query})"

        if year and "PUBYEAR" not in search_query.upper():
            search_query += f" AND PUBYEAR = {year}"

        url = f"{BASE_URL}/content/search/scopus"
        params = {
            "query": search_query,
            "count": min(count, 25),
            "sort": "citedby-count"
        }

        try:
            response = requests.get(url, headers=get_headers(), params=params, timeout=15)
            if response.ok:
                data = response.json()
                entries = data.get('search-results', {}).get('entry', [])
                total = data.get('search-results', {}).get('opensearch:totalResults', 0)

                results = []
                for entry in entries:
                    paper = {
                        "title": entry.get('dc:title', 'No title'),
                        "authors": entry.get('dc:creator', 'Unknown'),
                        "journal": entry.get('prism:publicationName', 'Unknown'),
                        "year": entry.get('prism:coverDate', ''),
                        "citations": int(entry.get('citedby-count', 0)),
                        "doi": entry.get('prism:doi', ''),
                        "eid": entry.get('eid', '')
                    }
                    results.append(paper)

                return {
                    "success": True,
                    "total_results": int(total),
                    "papers": results,
                    "query": query
                }
            else:
                return {"success": False, "error": f"API Error: {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_paper_abstract(self, arguments: dict) -> dict:
        """論文抄録取得"""
        eid = arguments.get("eid", "")
        doi = arguments.get("doi", "")

        if not eid and not doi:
            return {"success": False, "error": "EIDまたはDOIが必要です"}

        # EID優先
        if eid:
            url = f"{BASE_URL}/content/abstract/eid/{eid}"
        else:
            url = f"{BASE_URL}/content/abstract/doi/{doi}"

        try:
            response = requests.get(url, headers=get_headers(), timeout=10)
            if response.ok:
                data = response.json()
                abstract_response = data.get('abstracts-retrieval-response', {})
                coredata = abstract_response.get('coredata', {})

                result = {
                    "title": coredata.get('dc:title', 'No title'),
                    "abstract": coredata.get('dc:description', 'No abstract'),
                    "authors": coredata.get('dc:creator', 'Unknown'),
                    "journal": coredata.get('prism:publicationName', 'Unknown'),
                    "year": coredata.get('prism:coverDate', ''),
                    "doi": coredata.get('prism:doi', ''),
                    "eid": coredata.get('eid', ''),
                    "citations": coredata.get('citedby-count', '0')
                }

                return {"success": True, "paper": result}
            else:
                return {"success": False, "error": f"API Error: {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_author_info(self, arguments: dict) -> dict:
        """著者情報取得"""
        author_id = arguments.get("author_id", "")

        if not author_id:
            return {"success": False, "error": "author_idが必要です"}

        url = f"{BASE_URL}/analytics/scival/author/{author_id}"

        try:
            response = requests.get(url, headers=get_headers(), timeout=10)
            if response.ok:
                data = response.json()
                author_data = data.get('author', {})

                result = {
                    "author_id": author_id,
                    "name": author_data.get('name', 'Unknown'),
                    "current_institution": author_data.get('currentInstitutionName', 'Unknown'),
                    "scopus_url": author_data.get('link', {}).get('@href', '')
                }

                return {"success": True, "author": result}
            else:
                return {"success": False, "error": f"API Error: {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def analyze_research_trends(self, arguments: dict) -> dict:
        """研究分野トレンド分析"""
        field = arguments.get("field", "")
        years = arguments.get("years", [2022, 2023, 2024])

        if not field:
            return {"success": False, "error": "research fieldが必要です"}

        url = f"{BASE_URL}/content/search/scopus"
        yearly_data = {}

        try:
            for year in years:
                params = {
                    "query": f"TITLE-ABS-KEY({field}) AND PUBYEAR = {year}",
                    "count": 1
                }

                response = requests.get(url, headers=get_headers(), params=params, timeout=10)
                if response.ok:
                    data = response.json()
                    total = int(data.get('search-results', {}).get('opensearch:totalResults', 0))
                    yearly_data[year] = total

            # 成長率計算
            growth_rates = {}
            years_sorted = sorted(yearly_data.keys())
            for i in range(1, len(years_sorted)):
                prev_year = years_sorted[i-1]
                curr_year = years_sorted[i]
                if yearly_data[prev_year] > 0:
                    growth_rate = ((yearly_data[curr_year] - yearly_data[prev_year]) / yearly_data[prev_year]) * 100
                    growth_rates[f"{prev_year}-{curr_year}"] = round(growth_rate, 2)

            return {
                "success": True,
                "field": field,
                "yearly_papers": yearly_data,
                "growth_rates": growth_rates,
                "total_papers": sum(yearly_data.values())
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_institution_papers(self, arguments: dict) -> dict:
        """機関論文統計"""
        institution = arguments.get("institution", "")
        year = arguments.get("year", 2024)

        if not institution:
            return {"success": False, "error": "institution nameが必要です"}

        url = f"{BASE_URL}/content/search/scopus"
        params = {
            "query": f'AFFIL("{institution}") AND PUBYEAR = {year}',
            "count": 5,
            "sort": "citedby-count"
        }

        try:
            response = requests.get(url, headers=get_headers(), params=params, timeout=15)
            if response.ok:
                data = response.json()
                entries = data.get('search-results', {}).get('entry', [])
                total = int(data.get('search-results', {}).get('opensearch:totalResults', 0))

                top_papers = []
                for entry in entries:
                    paper = {
                        "title": entry.get('dc:title', 'No title'),
                        "authors": entry.get('dc:creator', 'Unknown'),
                        "journal": entry.get('prism:publicationName', 'Unknown'),
                        "citations": int(entry.get('citedby-count', 0)),
                        "doi": entry.get('prism:doi', '')
                    }
                    top_papers.append(paper)

                return {
                    "success": True,
                    "institution": institution,
                    "year": year,
                    "total_papers": total,
                    "top_papers": top_papers
                }
            else:
                return {"success": False, "error": f"API Error: {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def search_open_access_papers(self, arguments: dict) -> dict:
        """オープンアクセス論文検索"""
        field = arguments.get("field", "")
        count = arguments.get("count", 10)

        if not field:
            return {"success": False, "error": "research fieldが必要です"}

        url = f"{BASE_URL}/content/search/scopus"
        params = {
            "query": f"TITLE-ABS-KEY({field}) AND OPENACCESS(1) AND PUBYEAR = 2024",
            "count": min(count, 20),
            "sort": "citedby-count"
        }

        try:
            response = requests.get(url, headers=get_headers(), params=params, timeout=15)
            if response.ok:
                data = response.json()
                entries = data.get('search-results', {}).get('entry', [])
                total = int(data.get('search-results', {}).get('opensearch:totalResults', 0))

                papers = []
                for entry in entries:
                    paper = {
                        "title": entry.get('dc:title', 'No title'),
                        "authors": entry.get('dc:creator', 'Unknown'),
                        "journal": entry.get('prism:publicationName', 'Unknown'),
                        "citations": int(entry.get('citedby-count', 0)),
                        "doi": entry.get('prism:doi', ''),
                        "open_access": True
                    }
                    papers.append(paper)

                return {
                    "success": True,
                    "field": field,
                    "total_open_access": total,
                    "papers": papers
                }
            else:
                return {"success": False, "error": f"API Error: {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _define_prompts(self) -> dict:
        """Prompt definitions compliant with MCP specification."""
        return {
            "systematic_literature_review": {
                "name": "systematic_literature_review",
                "description": "Formulate a systematic literature review and comparative analysis on a research topic using Scopus search.",
                "arguments": [
                    {
                        "name": "topic",
                        "description": "The central research topic or technology to review (e.g., 'Transformer architectures in Computer Vision')",
                        "required": True
                    },
                    {
                        "name": "year_range",
                        "description": "Publication year range (e.g., '2021-2025')",
                        "required": False
                    },
                    {
                        "name": "focus",
                        "description": "Specific focus: 'methodology', 'benchmarks', 'application', or 'gap_analysis'",
                        "required": False
                    }
                ]
            },
            "paper_deep_dive": {
                "name": "paper_deep_dive",
                "description": "Conduct a comprehensive critical appraisal of a specific paper (methodology, findings, limitations, citations).",
                "arguments": [
                    {
                        "name": "paper_title_or_eid",
                        "description": "Title, DOI, or Scopus EID of the paper",
                        "required": True
                    },
                    {
                        "name": "analysis_depth",
                        "description": "Depth of analysis: 'concise_summary', 'critical_appraisal', or 'methodology_breakdown'",
                        "required": False
                    }
                ]
            },
            "research_trend_analysis": {
                "name": "research_trend_analysis",
                "description": "Analyze research momentum, publication trajectory, and breakthrough developments in a scientific domain.",
                "arguments": [
                    {
                        "name": "field",
                        "description": "The research field or domain keyword (e.g., 'Quantum Computing', 'Federated Learning')",
                        "required": True
                    },
                    {
                        "name": "timeframe",
                        "description": "Timeframe for trend evaluation (e.g., '2020-2025')",
                        "required": False
                    }
                ]
            }
        }

    async def get_prompt(self, name: str, arguments: dict) -> dict:
        """Construct prompt messages for an MCP prompt request."""
        if name == "systematic_literature_review":
            topic = arguments.get("topic", "the specified research topic")
            year_range = arguments.get("year_range", "recent years")
            focus = arguments.get("focus", "general methodology and open gaps")

            prompt_text = (
                f"You are an expert academic researcher conducting a systematic literature review on: \"{topic}\".\n\n"
                f"Scope & Constraints:\n"
                f"- Timeframe: {year_range}\n"
                f"- Primary Focus: {focus}\n\n"
                f"Step-by-Step Instructions:\n"
                f"1. Use `search_papers` with queries targeting \"{topic}\" to identify landmark and high-impact papers.\n"
                f"2. Use `get_paper_abstract` on the top retrieved papers to inspect their core methodologies, datasets, and claims.\n"
                f"3. Synthesize the findings into a rigorous academic report structured as follows:\n"
                f"   - **Executive Summary & Problem Statement**\n"
                f"   - **Taxonomy of Approaches**: Group papers into distinct conceptual paradigms.\n"
                f"   - **Methodological Comparison Table**: Columns for Paper (Author, Year), Key Technique, Dataset/Benchmark, Strengths, Limitations.\n"
                f"   - **Critical Research Gaps & Open Challenges**: Identify what current literature fails to address.\n"
                f"   - **Promising Future Directions**\n"
                f"4. Cite all referenced works using LaTeX citation markers (e.g., \\cite{{AuthorYear}} or direct DOI/EID links)."
            )
            return {
                "description": f"Systematic Literature Review on {topic}",
                "messages": [
                    {
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": prompt_text
                        }
                    }
                ]
            }

        elif name == "paper_deep_dive":
            target = arguments.get("paper_title_or_eid", "the target paper")
            depth = arguments.get("analysis_depth", "critical_appraisal")

            prompt_text = (
                f"You are an academic reviewer conducting a deep-dive analysis on: \"{target}\".\n\n"
                f"Analysis Depth: {depth}\n\n"
                f"Instructions:\n"
                f"1. Fetch the paper metadata and abstract using `get_paper_abstract` (or search for it with `search_papers` if only the title is provided).\n"
                f"2. Provide a structured critical review with the following sections:\n"
                f"   - **Bibliographic Metadata**: Title, Authors, Journal/Venue, Year, DOI, Citation Count.\n"
                f"   - **Core Research Question & Hypotheses**\n"
                f"   - **Methodology Breakdown**: Mathematical formulation, experimental setup, or algorithmic architecture.\n"
                f"   - **Key Findings & Evidence**: What was empirically proven vs. claimed.\n"
                f"   - **Threats to Validity & Limitations**: Unaddressed edge cases, dataset biases, or theoretical bounds.\n"
                f"   - **Impact & Context**: How this work relates to subsequent research."
            )
            return {
                "description": f"Deep Dive Analysis for {target}",
                "messages": [
                    {
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": prompt_text
                        }
                    }
                ]
            }

        elif name == "research_trend_analysis":
            field = arguments.get("field", "the specified domain")
            timeframe = arguments.get("timeframe", "2020-2025")

            prompt_text = (
                f"You are a scientometrics expert evaluating research trends in: \"{field}\" over {timeframe}.\n\n"
                f"Instructions:\n"
                f"1. Use `analyze_research_trends` and `search_papers` across target years to assess publication velocity.\n"
                f"2. Identify the leading institutions publishing in this field using `get_institution_papers`.\n"
                f"3. Produce a structured trend report covering:\n"
                f"   - **Growth Trajectory**: Annual publication volume and compound annual growth rate (CAGR).\n"
                f"   - **Top Contributing Hubs & Institutions**\n"
                f"   - **Emerging Sub-disciplines vs. Saturated Topics**\n"
                f"   - **Strategic Outlook & 3-Year Projection**"
            )
            return {
                "description": f"Research Trend Analysis for {field}",
                "messages": [
                    {
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": prompt_text
                        }
                    }
                ]
            }

        else:
            raise ValueError(f"Prompt not found: {name}")

    def _define_resources(self) -> list:
        """Define static resources exposed by the MCP server."""
        return [
            {
                "uri": "elsevier://docs/scopus-search-syntax",
                "name": "Scopus Search API Query Syntax Reference",
                "description": "Official Scopus search query syntax, boolean operators, field codes, and proximity operators reference guide.",
                "mimeType": "text/markdown"
            }
        ]

    def _define_resource_templates(self) -> list:
        """Define dynamic URI templates for MCP resources."""
        return [
            {
                "uriTemplate": "elsevier://paper/{eid}",
                "name": "Scopus Paper Abstract & Metadata",
                "description": "Dynamic resource retrieving paper abstract, authors, journal metadata, DOI, and citations by Scopus EID.",
                "mimeType": "text/markdown"
            },
            {
                "uriTemplate": "elsevier://trends/{field}",
                "name": "Research Field Publication Trends",
                "description": "Dynamic resource providing multi-year publication volume and growth statistics for a research field.",
                "mimeType": "text/markdown"
            }
        ]

    async def read_resource(self, uri: str) -> dict:
        """Read and render MCP resource content for a given URI."""
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
                        "text": content
                    }
                ]
            }

        elif uri.startswith("elsevier://paper/"):
            eid = uri[len("elsevier://paper/"):]
            res = await self.get_paper_abstract({"eid": eid})
            if res.get("success") and "paper" in res:
                p = res["paper"]
                authors_str = p.get("authors")
                if isinstance(authors_str, dict):
                    authors_list = authors_str.get("author", [])
                    if isinstance(authors_list, list):
                        names = [a.get("ce:indexed-name", a.get("ce:surname", "Unknown")) for a in authors_list if isinstance(a, dict)]
                        authors_str = ", ".join(names)
                    else:
                        authors_str = str(authors_str)

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
            else:
                error_msg = res.get("error", "Unknown error retrieving abstract")
                return {
                    "contents": [
                        {"uri": uri, "mimeType": "text/markdown", "text": f"# Error\n\nFailed to fetch paper `{eid}`: {error_msg}"}
                    ]
                }

        elif uri.startswith("elsevier://trends/"):
            field = uri[len("elsevier://trends/"):]
            res = await self.analyze_research_trends({"field": field, "years": [2022, 2023, 2024]})
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
            else:
                error_msg = res.get("error", "Unknown error analyzing trends")
                return {
                    "contents": [
                        {"uri": uri, "mimeType": "text/markdown", "text": f"# Error\n\nFailed to analyze trends for `{field}`: {error_msg}"}
                    ]
                }

        else:
            raise ValueError(f"Resource not found: {uri}")

async def handle_request(server, request):
    """MCPリクエスト処理"""
    method = request.get("method")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {
                        "subscribe": False,
                        "listChanged": False
                    },
                    "prompts": {
                        "listChanged": False
                    }
                },
                "serverInfo": {
                    "name": "elsevier-mcp-complete-server",
                    "version": VERSION
                }
            }
        }

    elif method == "prompts/list":
        prompts_list = list(server.prompts.values())
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {"prompts": prompts_list}
        }

    elif method == "prompts/get":
        prompt_name = request.get("params", {}).get("name")
        arguments = request.get("params", {}).get("arguments", {})
        if prompt_name in server.prompts:
            result = await server.get_prompt(prompt_name, arguments)
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": result
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {"code": -32602, "message": f"Prompt not found: {prompt_name}"}
            }

    elif method == "resources/list":
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {"resources": server.resources}
        }

    elif method == "resources/templates/list":
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {"resourceTemplates": server.resource_templates}
        }

    elif method == "resources/read":
        uri = request.get("params", {}).get("uri")
        try:
            result = await server.read_resource(uri)
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": result
            }
        except ValueError as e:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {"code": -32602, "message": str(e)}
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {"code": -32603, "message": f"Failed to read resource: {str(e)}"}
            }

    elif method == "tools/list":
        tools_list = []
        for tool_name, tool_def in server.tools.items():
            tools_list.append({
                "name": tool_def["name"],
                "description": tool_def["description"],
                "inputSchema": tool_def["inputSchema"]
            })

        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {"tools": tools_list}
        }

    elif method == "tools/call":
        tool_name = request.get("params", {}).get("name")
        arguments = request.get("params", {}).get("arguments", {})

        if tool_name in server.tools:
            # ツール実行
            handler = getattr(server, tool_name)
            result = await handler(arguments)

            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "content": [{
                        "type": "text",
                        "text": json.dumps(result, ensure_ascii=False, indent=2)
                    }]
                }
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {"code": -32601, "message": f"Tool not found: {tool_name}"}
            }

    else:
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {"code": -32601, "message": f"Method not found: {method}"}
        }

async def run_stdio():
    """メイン処理"""
    server = ElsevierMCPServer()
    print("Elsevier MCP Complete Server started", file=sys.stderr)

    # stdio での通信処理
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            request = json.loads(line.strip())
            response = await handle_request(server, request)

            print(json.dumps(response), flush=True)

        except EOFError:
            break
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": request.get("id") if 'request' in locals() else None,
                "error": {"code": -32603, "message": str(e)}
            }
            print(json.dumps(error_response), flush=True)

def main() -> int:
    """Console entry point for the stdio MCP server."""
    if "--version" in sys.argv:
        print(VERSION)
        return 0

    if "--help" in sys.argv or "-h" in sys.argv:
        print("Usage: elsevier-mcp-server [--version]")
        print("Runs the Elsevier MCP server over stdio.")
        return 0

    if not os.getenv("ELSEVIER_API_KEY"):
        print(
            "Warning: ELSEVIER_API_KEY is not set; tools will return configuration errors until it is set.",
            file=sys.stderr,
        )

    asyncio.run(run_stdio())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
