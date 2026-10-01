"""Configuration and credential management."""
import json
import os
from pathlib import Path

from pydantic_settings import BaseSettings

CONFIG_DIR = Path.home() / '.elsevier-mcp'
CONFIG_FILE = CONFIG_DIR / 'config.json'

class Settings(BaseSettings):
    """Application settings."""
    cors_origins: list[str] = ["*"]

def load_config_into_env():
    """Load API key and insttoken from config file into environment variables."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                config_data = json.load(f)

            if 'ELSEVIER_API_KEY' not in os.environ and 'api_key' in config_data:
                os.environ['ELSEVIER_API_KEY'] = config_data['api_key']

            if 'ELSEVIER_INSTTOKEN' not in os.environ and 'insttoken' in config_data:
                os.environ['ELSEVIER_INSTTOKEN'] = config_data['insttoken']
        except Exception as e:
            print(f"Error loading config file: {e}")

settings = Settings()
