"""Basic API startup and route registration tests."""


def test_app_imports():
    """Verify the FastAPI app can be imported without errors."""
    from app.main import app

    assert app.title == "Elsevier Academic API"


def test_routes_registered():
    """Verify all expected routes are registered and present in OpenAPI schema."""
    from app.main import app

    paths = list(app.openapi()["paths"].keys())
    expected = [
        "/api/health",
        "/api/search",
        "/api/abstract",
        "/api/trends",
        "/api/journal-metrics",
    ]
    for path in expected:
        assert path in paths, f"Route {path} not found in {paths}"
