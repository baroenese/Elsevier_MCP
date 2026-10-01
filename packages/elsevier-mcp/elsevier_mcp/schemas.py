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


SORT_KEYS = ("citedby-count", "-citedby-count", "coverdate", "-coverdate", "relevancy")


def _validate_year_string(v: str | None) -> str | None:
    """Validate an optional YYYY publication-year string (shared validator body)."""
    if v is not None and v.strip():
        v_str = v.strip()
        if not re.match(r"^\d{4}$", v_str):
            raise ValueError("Year must be a 4-digit year (YYYY)")
        return v_str
    return None


def _validate_sort_string(v: str | None) -> str | None:
    """Validate an optional Scopus sort key (shared validator body)."""
    if v is None or not v.strip():
        return None
    v = v.strip()
    if v not in SORT_KEYS:
        raise ValueError(f"sort must be one of: {', '.join(SORT_KEYS)}")
    return v


class SearchPapersInput(BaseModel):
    """Input parameters for search_papers tool."""

    model_config = ConfigDict(extra="ignore")

    query: str = Field(..., min_length=1, description="Search keyword or Scopus advanced query")
    count: int = Field(default=10, ge=1, le=25, description="Number of results to retrieve (1-25)")
    year: str | None = Field(default=None, description="Publication year in YYYY format")
    start: int = Field(
        default=0,
        ge=0,
        le=5999,
        description="Result offset for pagination (0-based; Scopus caps retrieval at the first 6000 results)",
    )
    sort: str | None = Field(default=None, description=f"Sort order, one of: {', '.join(SORT_KEYS)}")

    @field_validator("year")
    @classmethod
    def validate_year(cls, v: str | None) -> str | None:
        """Validate that publication year is in YYYY format."""
        return _validate_year_string(v)

    @field_validator("sort")
    @classmethod
    def validate_sort(cls, v: str | None) -> str | None:
        """Restrict sort to the Scopus-supported sort keys."""
        return _validate_sort_string(v)


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


class SearchAuthorPapersInput(BaseModel):
    """Input parameters for search_author_papers tool."""

    model_config = ConfigDict(extra="ignore")

    author_id: str | None = Field(default=None, description="Scopus Author ID (exact match, preferred)")
    author_name: str | None = Field(
        default=None, description='Author name in "Surname, Initials" format (prone to homonym collisions)'
    )
    affiliation: str | None = Field(default=None, description="Institution name to narrow the author down")
    count: int = Field(default=10, ge=1, le=25, description="Number of results to retrieve (1-25)")
    year: str | None = Field(default=None, description="Publication year in YYYY format")
    start: int = Field(default=0, ge=0, le=5999, description="Result offset for pagination (0-based)")
    sort: str | None = Field(default=None, description=f"Sort order, one of: {', '.join(SORT_KEYS)}")

    @field_validator("author_id")
    @classmethod
    def strip_author_id(cls, v: str | None) -> str | None:
        """Strip surrounding whitespace from author_id."""
        return strip_non_empty(v, "author_id") if v and v.strip() else None

    @field_validator("author_name")
    @classmethod
    def strip_author_name(cls, v: str | None) -> str | None:
        """Strip surrounding whitespace from author_name."""
        return strip_non_empty(v, "author_name") if v and v.strip() else None

    @field_validator("affiliation")
    @classmethod
    def strip_affiliation(cls, v: str | None) -> str | None:
        """Strip surrounding whitespace from affiliation."""
        return strip_non_empty(v, "affiliation") if v and v.strip() else None

    @field_validator("year")
    @classmethod
    def validate_year(cls, v: str | None) -> str | None:
        """Validate that publication year is in YYYY format."""
        return _validate_year_string(v)

    @field_validator("sort")
    @classmethod
    def validate_sort(cls, v: str | None) -> str | None:
        """Restrict sort to the Scopus-supported sort keys."""
        return _validate_sort_string(v)

    @model_validator(mode="after")
    def validate_author_specified(self) -> "SearchAuthorPapersInput":
        """Ensure either author_id or author_name is specified."""
        if not self.author_id and not self.author_name:
            raise ValueError("Either 'author_id' or 'author_name' must be provided")
        return self


class FindAuthorCandidatesInput(BaseModel):
    """Input parameters for find_author_candidates tool."""

    model_config = ConfigDict(extra="ignore")

    author_name: str = Field(
        ...,
        min_length=1,
        description='Author name to disambiguate, in "Surname, Initials" format',
    )
    affiliation: str | None = Field(default=None, description="Institution name to narrow candidates down")
    count: int = Field(default=25, ge=1, le=25, description="Number of papers to sample for grouping (1-25)")

    @field_validator("author_name")
    @classmethod
    def strip_author_name(cls, v: str) -> str:
        """Strip surrounding whitespace from author_name."""
        return strip_non_empty(v, "author_name")

    @field_validator("affiliation")
    @classmethod
    def strip_affiliation(cls, v: str | None) -> str | None:
        """Strip surrounding whitespace from affiliation."""
        return strip_non_empty(v, "affiliation") if v and v.strip() else None


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
