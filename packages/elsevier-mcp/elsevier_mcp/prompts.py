"""MCP prompt definitions and generator handlers."""

from typing import Any


def define_prompts() -> dict[str, dict[str, Any]]:
    """Define prompt specifications compliant with MCP protocol.

    Returns:
        Dictionary of prompt configurations keyed by prompt name.
    """
    return {
        "systematic_literature_review": {
            "name": "systematic_literature_review",
            "description": (
                "Formulate a systematic literature review and comparative analysis on a research topic "
                "using Scopus search."
            ),
            "arguments": [
                {
                    "name": "topic",
                    "description": (
                        "The central research topic or technology to review "
                        "(e.g., 'Transformer architectures in Computer Vision')"
                    ),
                    "required": True,
                },
                {
                    "name": "year_range",
                    "description": "Publication year range (e.g., '2021-2025')",
                    "required": False,
                },
                {
                    "name": "focus",
                    "description": "Specific focus: 'methodology', 'benchmarks', 'application', or 'gap_analysis'",
                    "required": False,
                },
            ],
        },
        "paper_deep_dive": {
            "name": "paper_deep_dive",
            "description": (
                "Conduct a comprehensive critical appraisal of a specific paper "
                "(methodology, findings, limitations, citations)."
            ),
            "arguments": [
                {
                    "name": "paper_title_or_eid",
                    "description": "Title, DOI, or Scopus EID of the paper",
                    "required": True,
                },
                {
                    "name": "analysis_depth",
                    "description": (
                        "Depth of analysis: 'concise_summary', 'critical_appraisal', or 'methodology_breakdown'"
                    ),
                    "required": False,
                },
            ],
        },
        "research_trend_analysis": {
            "name": "research_trend_analysis",
            "description": (
                "Analyze research momentum, publication trajectory, and breakthrough developments "
                "in a scientific domain."
            ),
            "arguments": [
                {
                    "name": "field",
                    "description": (
                        "The research field or domain keyword (e.g., 'Quantum Computing', 'Federated Learning')"
                    ),
                    "required": True,
                },
                {
                    "name": "timeframe",
                    "description": "Timeframe for trend evaluation (e.g., '2020-2025')",
                    "required": False,
                },
            ],
        },
    }


def get_prompt(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Construct prompt messages for an MCP prompt request.

    Args:
        name: Name of the prompt template.
        arguments: Arguments passed to the prompt template.

    Returns:
        MCP prompt result with description and message content.

    Raises:
        ValueError: If the prompt name is not recognized.
    """
    if name == "systematic_literature_review":
        topic = arguments.get("topic", "the specified research topic")
        year_range = arguments.get("year_range", "recent years")
        focus = arguments.get("focus", "general methodology and open gaps")

        prompt_text = (
            f'You are an expert academic researcher conducting a systematic literature review on: "{topic}".\n\n'
            f"Scope & Constraints:\n"
            f"- Timeframe: {year_range}\n"
            f"- Primary Focus: {focus}\n\n"
            f"Step-by-Step Instructions:\n"
            f'1. Use `search_papers` with queries targeting "{topic}" to identify landmark and high-impact papers.\n'
            f"2. Use `get_paper_abstract` on the top retrieved papers to inspect their core methodologies, "
            f"datasets, and claims.\n"
            f"3. Synthesize the findings into a rigorous academic report structured as follows:\n"
            f"   - **Executive Summary & Problem Statement**\n"
            f"   - **Taxonomy of Approaches**: Group papers into distinct conceptual paradigms.\n"
            f"   - **Methodological Comparison Table**: Columns for Paper (Author, Year), Key Technique, "
            f"Dataset/Benchmark, Strengths, Limitations.\n"
            f"   - **Critical Research Gaps & Open Challenges**: Identify what current literature fails to address.\n"
            f"   - **Promising Future Directions**\n"
            f"4. Cite all referenced works using LaTeX citation markers "
            f"(e.g., \\cite{{AuthorYear}} or direct DOI/EID links)."
        )
        return {
            "description": f"Systematic Literature Review on {topic}",
            "messages": [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": prompt_text,
                    },
                }
            ],
        }

    if name == "paper_deep_dive":
        target = arguments.get("paper_title_or_eid", "the target paper")
        depth = arguments.get("analysis_depth", "critical_appraisal")

        prompt_text = (
            f'You are an academic reviewer conducting a deep-dive analysis on: "{target}".\n\n'
            f"Analysis Depth: {depth}\n\n"
            f"Instructions:\n"
            f"1. Fetch the paper metadata and abstract using `get_paper_abstract` "
            f"(or search for it with `search_papers` if only the title is provided).\n"
            f"2. Provide a structured critical review with the following sections:\n"
            f"   - **Bibliographic Metadata**: Title, Authors, Journal/Venue, Year, DOI, Citation Count.\n"
            f"   - **Core Research Question & Hypotheses**\n"
            f"   - **Methodology Breakdown**: Mathematical formulation, experimental setup, "
            f"or algorithmic architecture.\n"
            f"   - **Key Findings & Evidence**: What was empirically proven vs. claimed.\n"
            f"   - **Threats to Validity & Limitations**: Unaddressed edge cases, dataset biases, "
            f"or theoretical bounds.\n"
            f"   - **Impact & Context**: How this work relates to subsequent research."
        )
        return {
            "description": f"Deep Dive Analysis for {target}",
            "messages": [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": prompt_text,
                    },
                }
            ],
        }

    if name == "research_trend_analysis":
        field = arguments.get("field", "the specified domain")
        timeframe = arguments.get("timeframe", "2020-2025")

        prompt_text = (
            f'You are a scientometrics expert evaluating research trends in: "{field}" over {timeframe}.\n\n'
            f"Instructions:\n"
            f"1. Use `analyze_research_trends` and `search_papers` across target years to assess publication "
            f"velocity.\n"
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
                        "text": prompt_text,
                    },
                }
            ],
        }

    raise ValueError(f"Prompt not found: {name}")
