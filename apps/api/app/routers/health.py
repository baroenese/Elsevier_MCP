"""Health and configuration management routes."""

import json
import os
from typing import Any

from elsevier_mcp.handlers import define_tools
from fastapi import APIRouter
from pydantic import BaseModel

from app.config import CONFIG_DIR, CONFIG_FILE

router = APIRouter(tags=["health"])


class ConfigBody(BaseModel):
    """Configuration body."""

    api_key: str | None = None
    insttoken: str | None = None


def _config_has(key: str) -> bool:
    """Check if a key exists in the persistent config file."""
    if not CONFIG_FILE.exists():
        return False
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        return bool(data.get(key))
    except (OSError, json.JSONDecodeError):
        return False


def _save_config(api_key: str | None, insttoken: str | None) -> None:
    """Persist credentials with 0600 permissions."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data: dict[str, str] = {}
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}

    if api_key is not None:
        if api_key:
            data["api_key"] = api_key
        else:
            data.pop("api_key", None)

    if insttoken is not None:
        if insttoken:
            data["insttoken"] = insttoken
        else:
            data.pop("insttoken", None)

    CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    CONFIG_FILE.chmod(0o600)


@router.get("/health")
async def get_health() -> dict[str, Any]:
    """Health check endpoint exposing active credential sources."""
    has_env_key = bool(os.environ.get("ELSEVIER_API_KEY"))
    has_cfg_key = _config_has("api_key")
    return {
        "success": True,
        "version": "2.0.0",
        "api_key_set": has_env_key or has_cfg_key,
        "api_key_source": (
            "environment"
            if has_env_key
            else "config_file"
            if has_cfg_key
            else "not_set"
        ),
        "insttoken_set": bool(
            os.environ.get("ELSEVIER_INSTTOKEN") or _config_has("insttoken")
        ),
        "config_file": str(CONFIG_FILE),
    }


@router.get("/tools")
async def get_tools() -> dict[str, Any]:
    """Get registered MCP tools with names and descriptions."""
    tool_defs = define_tools()
    return {
        "success": True,
        "tools": [
            {
                "name": t["name"],
                "description": t["description"],
                "inputSchema": t["inputSchema"],
            }
            for t in tool_defs.values()
        ],
    }


@router.post("/config")
async def post_config(body: ConfigBody) -> dict[str, Any]:
    """Save API configuration credentials."""
    try:
        _save_config(body.api_key, body.insttoken)
    except OSError as exc:
        return {"success": False, "error": f"Could not write config: {exc}"}

    if body.api_key:
        os.environ["ELSEVIER_API_KEY"] = body.api_key
    elif body.api_key == "":
        os.environ.pop("ELSEVIER_API_KEY", None)

    if body.insttoken:
        os.environ["ELSEVIER_INSTTOKEN"] = body.insttoken
    elif body.insttoken == "":
        os.environ.pop("ELSEVIER_INSTTOKEN", None)

    return await get_health()
