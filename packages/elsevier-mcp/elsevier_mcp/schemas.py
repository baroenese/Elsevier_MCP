"""Pydantic input and output validation models for Elsevier MCP server tools."""

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def _current_year() -> int:
    """Return the current calendar year."""
    return datetime.now().year


def _default_trend_years() -> list[int]:
    """Return the last three calendar years for trend analysis."""
    cur = _current_year()
    return [cur - 2, cur - 1, cur]


def strip_non_empty(value: str, field_name: str) -> str:
    """Strip surrounding whitespace from a string field and reject empty results.

    Shared validator body for all single-value string fields.

    Args:
        value: Raw field value.
        field_name: Field name used in the error message.

    Returns:
        Stripped value.

    Raises:
        ValueError: If the stripped value is empty.
    """
    s = value.strip()
    if not s:
        raise ValueError(f"{field_name} must not be empty")
    return s


class SearchPapersInput(BaseModel):
    """Input parameters for search_papers tool."""

    model_config = ConfigDict(extra="ignore")

    query: str = Field(..., min_length=1, description="Search keyword or Scopus advanced query")
    count: int = Field(default=10, ge=1, le=25, description="Number of results to retrieve (1-25)")
    year: str | None = Field(default=None, description="Publication year in YYYY format")

    @field_validator("year")
    @classmethod
    def validate_year(cls, v: str | None) -> str | None:
        """Validate that publication year is in YYYY format."""
        if v is not None and v.strip():
            v_str = v.strip()
            if not re.match(r"^\d{4}$", v_str):
                raise ValueError("Year must be a 4-digit year (YYYY)")
            return v_str
        return None


class GetPaperAbstractInput(BaseModel):
    """Input parameters for get_paper_abstract tool."""

    model_config = ConfigDict(extra="ignore")

    eid: str | None = Field(default=None, description="Scopus Electronic Identifier (EID)")
    doi: str | None = Field(default=None, description="Digital Object Identifier (DOI)")

    @model_validator(mode="after")
    def validate_eid_or_doi(self) -> "GetPaperAbstractInput":
        """Ensure either eid or doi is specified."""
        eid_val = (self.eid or "").strip()
        doi_val = (self.doi or "").strip()
        if not eid_val and not doi_val:
            raise ValueError("Either 'eid' or 'doi' must be provided")
        self.eid = eid_val or None
        self.doi = doi_val or None
        return self


class GetAuthorInfoInput(BaseModel):
    """Input parameters for get_author_info tool."""

    model_config = ConfigDict(extra="ignore")

    author_id: str = Field(..., min_length=1, description="Scopus Author ID")

    @field_validator("author_id")
    @classmethod
    def strip_id(cls, v: str) -> str:
        """Strip surrounding whitespace from author_id."""
        return strip_non_empty(v, "author_id")


class AnalyzeResearchTrendsInput(BaseModel):
    """Input parameters for analyze_research_trends tool."""

    model_config = ConfigDict(extra="ignore")

    field: str = Field(..., min_length=1, description="Research field keyword")
    years: list[int] = Field(
        default_factory=_default_trend_years,
        description="List of target publication years to analyze"
    )

    @field_validator("field")
    @classmethod
    def strip_field(cls, v: str) -> str:
        """Strip surrounding whitespace from field."""
        return strip_non_empty(v, "field")

    @field_validator("years")
    @classmethod
    def validate_years_list(cls, v: list[int]) -> list[int]:
        """Ensure years list is non-empty and contains valid years."""
        if not v:
            return _default_trend_years()
        for y in v:
            if y < 1900 or y > 2100:
                raise ValueError(f"Year {y} is outside the acceptable range (1900-2100)")
        return sorted(set(v))


class GetInstitutionPapersInput(BaseModel):
    """Input parameters for get_institution_papers tool."""

    model_config = ConfigDict(extra="ignore")

    institution: str = Field(..., min_length=1, description="Institution name")
    year: int = Field(default_factory=_current_year, description="Target publication year")

    @field_validator("institution")
    @classmethod
    def strip_institution(cls, v: str) -> str:
        """Strip surrounding whitespace from institution name."""
        return strip_non_empty(v, "institution")

    @field_validator("year")
    @classmethod
    def validate_year_val(cls, v: int) -> int:
        """Validate year range."""
        if v < 1900 or v > 2100:
            raise ValueError(f"Year {v} is outside the acceptable range (1900-2100)")
        return v


class SearchOpenAccessPapersInput(BaseModel):
    """Input parameters for search_open_access_papers tool."""

    model_config = ConfigDict(extra="ignore")

    field: str = Field(..., min_length=1, description="Research field keyword")
    count: int = Field(default=10, ge=1, le=20, description="Number of results to retrieve (1-20)")
    year: int | None = Field(default=None, description="Publication year (defaults to current year)")

    @field_validator("field")
    @classmethod
    def strip_field(cls, v: str) -> str:
        """Strip surrounding whitespace from field."""
        return strip_non_empty(v, "field")


class GetJournalMetricsInput(BaseModel):
    """Input parameters for get_journal_metrics tool."""

    model_config = ConfigDict(extra="ignore")

    title: str | None = Field(default=None, description="Journal title")
    issn: str | None = Field(default=None, description="Journal ISSN or E-ISSN")

    @model_validator(mode="after")
    def validate_title_or_issn(self) -> "GetJournalMetricsInput":
        """Ensure either title or issn is specified."""
        t = (self.title or "").strip()
        i = (self.issn or "").strip()
        if not t and not i:
            raise ValueError("Either 'title' or 'issn' must be provided")
        self.title = t or None
        self.issn = i or None
        return self
