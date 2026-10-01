"""Tests for Pydantic input models in elsevier_mcp.schemas."""

from datetime import datetime

import pytest
from pydantic import ValidationError

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


def test_search_papers_input_valid() -> None:
    """Verify SearchPapersInput with valid inputs."""
    data = SearchPapersInput(query="deep learning", count=15, year="2024")
    assert data.query == "deep learning"
    assert data.count == 15
    assert data.year == "2024"


def test_search_papers_input_invalid_year() -> None:
    """Verify SearchPapersInput rejects non-4-digit years."""
    with pytest.raises(ValidationError, match="4-digit year"):
        SearchPapersInput(query="AI", year="24")


def test_search_papers_input_count_bounds() -> None:
    """Verify SearchPapersInput enforces count bounds [1, 25]."""
    with pytest.raises(ValidationError):
        SearchPapersInput(query="AI", count=0)

    with pytest.raises(ValidationError):
        SearchPapersInput(query="AI", count=30)


def test_search_papers_input_pagination() -> None:
    """Verify SearchPapersInput pagination defaults, bounds, and sort keys."""
    data = SearchPapersInput(query="AI")
    assert data.start == 0
    assert data.sort is None

    data = SearchPapersInput(query="AI", start=25, sort="-coverdate")
    assert data.start == 25
    assert data.sort == "-coverdate"

    with pytest.raises(ValidationError):
        SearchPapersInput(query="AI", start=-1)

    with pytest.raises(ValidationError):
        SearchPapersInput(query="AI", start=6000)

    with pytest.raises(ValidationError, match="sort must be one of"):
        SearchPapersInput(query="AI", sort="bogus")


def test_search_author_papers_input() -> None:
    """Verify SearchAuthorPapersInput requires an author and validates options."""
    with pytest.raises(ValidationError, match="Either 'author_id' or 'author_name'"):
        SearchAuthorPapersInput()

    data = SearchAuthorPapersInput(author_id=" 55239922200 ")
    assert data.author_id == "55239922200"
    assert data.author_name is None

    data = SearchAuthorPapersInput(
        author_name=" Wahono, Romi S. ",
        affiliation=" Binus ",
        year="2024",
        sort="coverdate",
        start=25,
        count=25,
    )
    assert data.author_name == "Wahono, Romi S."
    assert data.affiliation == "Binus"
    assert data.year == "2024"
    assert data.sort == "coverdate"

    with pytest.raises(ValidationError, match="4-digit year"):
        SearchAuthorPapersInput(author_id="55239922200", year="20x4")

    with pytest.raises(ValidationError, match="sort must be one of"):
        SearchAuthorPapersInput(author_id="55239922200", sort="nope")

    with pytest.raises(ValidationError):
        SearchAuthorPapersInput(author_id="55239922200", count=26)

    with pytest.raises(ValidationError):
        SearchAuthorPapersInput(author_id="55239922200", start=6000)


def test_find_author_candidates_input() -> None:
    """Verify FindAuthorCandidatesInput strips and bounds inputs."""
    data = FindAuthorCandidatesInput(author_name="  Wahono, R S  ")
    assert data.author_name == "Wahono, R S"
    assert data.affiliation is None
    assert data.count == 25

    data = FindAuthorCandidatesInput(author_name="Wahono, R S", affiliation=" Binus ", count=1)
    assert data.affiliation == "Binus"
    assert data.count == 1

    with pytest.raises(ValidationError):
        FindAuthorCandidatesInput(author_name="   ")

    with pytest.raises(ValidationError):
        FindAuthorCandidatesInput(author_name="Wahono, R S", count=26)


def test_get_paper_abstract_input() -> None:
    """Verify GetPaperAbstractInput requires at least one of eid or doi."""
    with pytest.raises(ValidationError, match="Either 'eid' or 'doi'"):
        GetPaperAbstractInput()

    data_eid = GetPaperAbstractInput(eid="2-s2.0-85041938382")
    assert data_eid.eid == "2-s2.0-85041938382"
    assert data_eid.doi is None

    data_doi = GetPaperAbstractInput(doi="10.1000/182")
    assert data_doi.doi == "10.1000/182"


def test_get_author_info_input() -> None:
    """Verify GetAuthorInfoInput validation."""
    with pytest.raises(ValidationError):
        GetAuthorInfoInput(author_id="   ")

    data = GetAuthorInfoInput(author_id="  55239922200  ")
    assert data.author_id == "55239922200"


def test_analyze_research_trends_input() -> None:
    """Verify AnalyzeResearchTrendsInput defaults and validations."""
    data = AnalyzeResearchTrendsInput(field="quantum computing")
    assert data.field == "quantum computing"
    assert len(data.years) == 3

    custom = AnalyzeResearchTrendsInput(field="NLP", years=[2021, 2022, 2023])
    assert custom.years == [2021, 2022, 2023]

    with pytest.raises(ValidationError, match="acceptable range"):
        AnalyzeResearchTrendsInput(field="NLP", years=[1800])


def test_get_institution_papers_input() -> None:
    """Verify GetInstitutionPapersInput defaults and validation."""
    data = GetInstitutionPapersInput(institution="Stanford University")
    assert data.institution == "Stanford University"
    assert data.year == datetime.now().year

    with pytest.raises(ValidationError):
        GetInstitutionPapersInput(institution="")


def test_search_open_access_papers_input() -> None:
    """Verify SearchOpenAccessPapersInput count boundaries."""
    data = SearchOpenAccessPapersInput(field="climate change", count=20)
    assert data.count == 20

    with pytest.raises(ValidationError):
        SearchOpenAccessPapersInput(field="climate", count=25)


def test_get_journal_metrics_input() -> None:
    """Verify GetJournalMetricsInput requires title or issn."""
    with pytest.raises(ValidationError, match="Either 'title' or 'issn'"):
        GetJournalMetricsInput()

    data_title = GetJournalMetricsInput(title="Nature")
    assert data_title.title == "Nature"

    data_issn = GetJournalMetricsInput(issn="0028-0836")
    assert data_issn.issn == "0028-0836"
