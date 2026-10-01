"""Consistency tests between define_tools() JSON Schemas and Pydantic input models.

The hand-written inputSchema in define_tools() and the Pydantic models in
schemas.py must agree: same fields, same required set, same basic types.
"""

from typing import Any, get_args, get_origin

import pytest
from pydantic import BaseModel

from elsevier_mcp.handlers import define_tools
from elsevier_mcp.schemas import (
    AnalyzeResearchTrendsInput,
    FindAuthorCandidatesInput,
    GetAuthorInfoInput,
    GetInstitutionPapersInput,
    GetJournalMetricsInput,
    GetPaperAbstractInput,
    SearchAuthorPapersInput,
    SearchOpenAccessPapersInput,
    SearchPapersInput,
)

SCHEMA_TYPES = {"string": str, "integer": int, "number": float, "array": list, "boolean": bool}

MODEL_BY_TOOL = {
    "search_papers": SearchPapersInput,
    "get_paper_abstract": GetPaperAbstractInput,
    "get_author_info": GetAuthorInfoInput,
    "analyze_research_trends": AnalyzeResearchTrendsInput,
    "get_institution_papers": GetInstitutionPapersInput,
    "search_open_access_papers": SearchOpenAccessPapersInput,
    "get_journal_metrics": GetJournalMetricsInput,
    "search_author_papers": SearchAuthorPapersInput,
    "find_author_candidates": FindAuthorCandidatesInput,
}


def _required_fields(model: type[BaseModel]) -> list[str]:
    """Field names without defaults (i.e. required by the Pydantic model)."""
    return [name for name, field in model.model_fields.items() if field.is_required()]


def _annotation_includes(annotation: object, base: type) -> bool:
    """Whether an annotation is the base type, a generic of it (list[int]), or an Optional."""
    if annotation is base:
        return True
    if get_origin(annotation) is base:
        return True
    return base in get_args(annotation)


@pytest.mark.parametrize("tool_name", sorted(MODEL_BY_TOOL))
def test_schema_matches_pydantic_model(tool_name: str) -> None:
    """inputSchema properties/required match the Pydantic model fields."""
    tool_def = define_tools()[tool_name]
    schema: dict[str, Any] = tool_def["inputSchema"]
    model = MODEL_BY_TOOL[tool_name]

    assert set(schema["properties"]) == set(model.model_fields.keys()), (
        f"{tool_name}: inputSchema properties {sorted(schema['properties'])} != "
        f"model fields {sorted(model.model_fields)}"
    )
    assert schema.get("required", []) == _required_fields(model), (
        f"{tool_name}: inputSchema required {schema.get('required', [])} != "
        f"model required {_required_fields(model)}"
    )
    assert schema["type"] == "object"

    for field_name, prop in schema["properties"].items():
        expected_type = SCHEMA_TYPES.get(prop.get("type"))
        if expected_type is None:
            continue
        annotation = model.model_fields[field_name].annotation
        assert annotation is not None
        assert _annotation_includes(annotation, expected_type), (
            f"{tool_name}.{field_name}: schema type {prop['type']} not compatible with annotation {annotation}"
        )


def test_schema_bounds_match_model_constraints() -> None:
    """Documented min/max bounds in schemas match the Pydantic Field constraints."""

    def bounds(model: type[BaseModel], field: str) -> tuple[object, object]:
        ge = next(m.ge for m in model.model_fields[field].metadata if hasattr(m, "ge"))
        le = next(m.le for m in model.model_fields[field].metadata if hasattr(m, "le"))
        return ge, le

    tools = define_tools()
    search = tools["search_papers"]["inputSchema"]["properties"]["count"]
    assert search["minimum"] == 1 and search["maximum"] == 25
    assert bounds(SearchPapersInput, "count") == (1, 25)

    oa = tools["search_open_access_papers"]["inputSchema"]["properties"]["count"]
    assert oa["minimum"] == 1 and oa["maximum"] == 20
    assert bounds(SearchOpenAccessPapersInput, "count") == (1, 20)
