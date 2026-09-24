"""Pytest fixtures and sample data for the elsevier_mcp test suite."""

import os
from typing import Any, AsyncGenerator

import pytest
import respx

from elsevier_mcp.client import ElsevierAPIClient
from elsevier_mcp.rate_limiter import TokenBucketRateLimiter
from elsevier_mcp.server import ElsevierMCPServer


@pytest.fixture(autouse=True)
def set_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set required Elsevier API environment variables for tests."""
    monkeypatch.setenv("ELSEVIER_API_KEY", "mock-test-key-12345")
    monkeypatch.setenv("ELSEVIER_RATE_LIMIT", "100.0")  # Fast for tests
    monkeypatch.setenv("ELSEVIER_TIMEOUT", "5.0")


@pytest.fixture
def sample_scopus_search_response() -> dict[str, Any]:
    """Provide realistic sample JSON response from Scopus Search API."""
    return {
        "search-results": {
            "opensearch:totalResults": "42",
            "entry": [
                {
                    "dc:title": "Attention Is All You Need",
                    "dc:creator": "Vaswani A.",
                    "prism:publicationName": "Advances in Neural Information Processing Systems",
                    "prism:coverDate": "2017-12-01",
                    "citedby-count": "105432",
                    "prism:doi": "10.5555/3295222.3295349",
                    "eid": "2-s2.0-85041938382",
                },
                {
                    "dc:title": "BERT: Pre-training of Deep Bidirectional Transformers",
                    "dc:creator": "Devlin J.",
                    "prism:publicationName": "NAACL HLT 2019",
                    "prism:coverDate": "2019-06-01",
                    "citedby-count": "65000",
                    "prism:doi": "10.18653/v1/N19-1423",
                    "eid": "2-s2.0-85072049281",
                },
            ],
        }
    }


@pytest.fixture
def sample_abstract_response() -> dict[str, Any]:
    """Provide realistic sample JSON response from Scopus Abstract Retrieval API."""
    return {
        "abstracts-retrieval-response": {
            "coredata": {
                "dc:title": "Deep Residual Learning for Image Recognition",
                "dc:description": "Deeper neural networks are more difficult to train...",
                "dc:creator": "He K.",
                "prism:publicationName": "Proceedings of the IEEE CVPR",
                "prism:coverDate": "2016-06-27",
                "prism:doi": "10.1109/CVPR.2016.90",
                "eid": "2-s2.0-84984577884",
                "citedby-count": "180000",
            }
        }
    }


@pytest.fixture
def sample_author_response() -> dict[str, Any]:
    """Provide realistic sample JSON response from SciVal Author API."""
    return {
        "author": {
            "name": "Yoshua Bengio",
            "currentInstitutionName": "Université de Montréal",
            "link": {
                "@href": "https://www.scopus.com/authid/detail.uri?authorId=55239922200"
            },
        }
    }


@pytest.fixture
def sample_serial_response() -> dict[str, Any]:
    """Provide realistic sample JSON response from Serial Title (CiteScore) API."""
    return {
        "serial-metadata-response": {
            "entry": [
                {
                    "dc:title": "Nature Machine Intelligence",
                    "dc:publisher": "Nature Publishing Group",
                    "prism:issn": "2522-5839",
                    "prism:eIssn": "2522-5839",
                    "prism:aggregationType": "Journal",
                    "openaccess": "0",
                    "citeScoreYearInfoList": {
                        "citeScoreCurrentMetric": "28.5",
                        "citeScoreCurrentMetricYear": "2023",
                        "citeScoreTracker": "29.1",
                        "citeScoreTrackerYear": "2024",
                        "citeScoreYearInfo": [
                            {
                                "@status": "Complete",
                                "citeScoreInformationList": [
                                    {
                                        "citeScoreInfo": [
                                            {
                                                "citeScoreSubjectRank": [
                                                    {
                                                        "subjectCode": "1702",
                                                        "rank": "1",
                                                        "percentile": "99.0",
                                                    },
                                                    {
                                                        "subjectCode": "1707",
                                                        "rank": "3",
                                                        "percentile": "97.5",
                                                    },
                                                ]
                                            }
                                        ]
                                    }
                                ],
                            }
                        ],
                    },
                    "SJRList": {
                        "SJR": [{"$": "5.42", "@year": "2023"}]
                    },
                    "SNIPList": {
                        "SNIP": [{"$": "6.85", "@year": "2023"}]
                    },
                }
            ]
        }
    }


@pytest.fixture
async def api_client() -> AsyncGenerator[ElsevierAPIClient, None]:
    """Provide an isolated ElsevierAPIClient for testing."""
    limiter = TokenBucketRateLimiter(rate=500.0, burst=500.0)
    client = ElsevierAPIClient(rate_limiter=limiter, timeout=5.0, max_retries=2)
    yield client
    await client.aclose()


@pytest.fixture
def server(api_client: ElsevierAPIClient) -> ElsevierMCPServer:
    """Provide an ElsevierMCPServer configured with the test api_client."""
    return ElsevierMCPServer(client=api_client)
