"""Tests for stdio loop, error handling, and CLI entry point in elsevier_mcp.server."""

import asyncio
import io
import json
import logging
import sys
from typing import Any

import pytest

import elsevier_mcp.server as server_module
from elsevier_mcp.server import VERSION, ElsevierMCPServer, configure_logging, handle_request, main, run_stdio


class FakeStdin:
    """Stand-in for sys.stdin that replays prepared lines then hits EOF."""

    def __init__(self, lines: list[str]) -> None:
        self._reader = io.StringIO("".join(line + "\n" for line in lines))

    def readline(self) -> str:
        return self._reader.readline()


@pytest.mark.asyncio
async def test_run_stdio_parses_and_responds(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture, server: ElsevierMCPServer
) -> None:
    """run_stdio answers valid requests, skips blanks, and exits on EOF."""
    requests = [
        "",  # blank line is ignored
        "{not valid json",  # parse error -> -32700
        json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}),
        "",  # EOF afterwards
    ]
    monkeypatch.setattr(sys, "stdin", FakeStdin(requests))
    monkeypatch.setattr(server_module, "ElsevierMCPServer", lambda: server)

    await asyncio.wait_for(run_stdio(), timeout=5.0)

    out = capsys.readouterr().out.strip().splitlines()
    assert len(out) == 2
    parse_error = json.loads(out[0])
    assert parse_error["error"]["code"] == -32700
    assert "Parse error" in parse_error["error"]["message"]
    init_response = json.loads(out[1])
    assert init_response["id"] == 1
    assert init_response["result"]["protocolVersion"] == "2024-11-05"


@pytest.mark.asyncio
async def test_run_stdio_internal_error_returns_minus_32603(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture, server: ElsevierMCPServer
) -> None:
    """An exception inside handle_request yields a -32603 error response, not a crash."""

    async def boom(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("kaboom")

    monkeypatch.setattr(sys, "stdin", FakeStdin([json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})]))
    monkeypatch.setattr(server_module, "ElsevierMCPServer", lambda: server)
    monkeypatch.setattr(server_module, "handle_request", boom)

    await asyncio.wait_for(run_stdio(), timeout=5.0)

    resp = json.loads(capsys.readouterr().out.strip())
    assert resp["error"]["code"] == -32603
    assert "kaboom" in resp["error"]["message"]


@pytest.mark.asyncio
async def test_tools_call_handler_exception_maps_to_32603(server: ElsevierMCPServer) -> None:
    """tools/call converts an unexpected handler exception into a -32603 JSON-RPC error."""

    async def explode(arguments: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError("handler exploded")

    server.search_papers = explode  # type: ignore[method-assign]
    resp = await handle_request(
        server,
        {"jsonrpc": "2.0", "id": 9, "method": "tools/call", "params": {"name": "search_papers", "arguments": {}}},
    )
    assert resp is not None
    assert resp["error"]["code"] == -32603
    assert "handler exploded" in resp["error"]["message"]


def test_main_version_flag(capsys: pytest.CaptureFixture) -> None:
    """--version prints the version and exits 0."""
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(sys, "argv", ["elsevier-mcp-server", "--version"])
        assert main() == 0
    assert capsys.readouterr().out.strip() == VERSION


def test_main_help_flag(capsys: pytest.CaptureFixture) -> None:
    """--help prints usage and exits 0."""
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(sys, "argv", ["elsevier-mcp-server", "--help"])
        assert main() == 0
    assert "Usage" in capsys.readouterr().out


def test_main_warns_without_api_key(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """Missing ELSEVIER_API_KEY prints a stderr warning but still starts."""

    async def fake_run_stdio() -> None:
        return None

    monkeypatch.setattr(sys, "argv", ["elsevier-mcp-server"])
    monkeypatch.delenv("ELSEVIER_API_KEY", raising=False)
    monkeypatch.setattr(server_module, "run_stdio", fake_run_stdio)
    assert main() == 0
    assert "ELSEVIER_API_KEY" in capsys.readouterr().err


def test_configure_logging_respects_env_level(monkeypatch: pytest.MonkeyPatch) -> None:
    """ELSEVIER_LOG_LEVEL selects the root logging level."""
    monkeypatch.setenv("ELSEVIER_LOG_LEVEL", "DEBUG")
    configure_logging()
    assert logging.getLogger().level == logging.DEBUG
    monkeypatch.setenv("ELSEVIER_LOG_LEVEL", "WARNING")
    configure_logging()
    assert logging.getLogger().level == logging.WARNING
