"""Health and config routes."""
import json
import os
from fastapi import APIRouter
from pydantic import BaseModel
from elsevier_mcp.handlers import define_tools
from app.config import CONFIG_FILE, CONFIG_DIR

router = APIRouter(tags=["health"])

class ConfigBody(BaseModel):
    """Configuration body."""
    api_key: str | None = None
    insttoken: str | None = None

def _config_has(key: str) -> bool:
    if not CONFIG_FILE.exists():
        return False
    try:
        with open(CONFIG_FILE, 'r') as f:
            data = json.load(f)
            return bool(data.get(key))
    except Exception:
        return False

def _save_config(api_key: str | None, insttoken: str | None) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data = {}
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
        except Exception:
            pass
            
    if api_key:
        data['api_key'] = api_key
    if insttoken:
        data['insttoken'] = insttoken
        
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f)
    CONFIG_FILE.chmod(0o600)

@router.get("/health")
async def get_health():
    """Health check endpoint."""
    return {
        "version": "2.0.0",
        "api_key_set": "ELSEVIER_API_KEY" in os.environ or _config_has("api_key"),
        "api_key_source": "env" if "ELSEVIER_API_KEY" in os.environ else "config" if _config_has("api_key") else None,
        "insttoken_set": "ELSEVIER_INSTTOKEN" in os.environ or _config_has("insttoken"),
        "config_file": str(CONFIG_FILE)
    }

@router.get("/tools")
async def get_tools():
    """Get available tools."""
    return define_tools()

@router.post("/config")
async def post_config(body: ConfigBody):
    """Save API configuration."""
    _save_config(body.api_key, body.insttoken)
    if body.api_key:
        os.environ['ELSEVIER_API_KEY'] = body.api_key
    if body.insttoken:
        os.environ['ELSEVIER_INSTTOKEN'] = body.insttoken
    return {"status": "success"}
