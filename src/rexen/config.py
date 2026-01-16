"""
Configuration management for ReXeN.
Loads settings from environment variables and config files.
Provides default values for all settings.
"""

import os
from pathlib import Path
from typing import Dict, Any

class Config:
    """Central configuration class."""
    
    def __init__(self):
        # Base paths
        self.BASE_DIR = Path(__file__).parent.parent
        self.DATA_DIR = self.BASE_DIR / "data"
        self.REPORTS_DIR = self.DATA_DIR / "reports"
        self.RESULTS_DIR = self.DATA_DIR / "results"
        
        # Create directories
        self.DATA_DIR.mkdir(exist_ok=True)
        self.REPORTS_DIR.mkdir(exist_ok=True)
        self.RESULTS_DIR.mkdir(exist_ok=True)
        
        # Database
        self.DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/rexen.db")
        
        # AI
        self.OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
        
        # Rate limiting
        self.RATE_LIMIT_RPS = int(os.getenv("RATE_LIMIT_RPS", "2"))  # Requests per second
        self.MAX_PARALLEL_TOOLS = int(os.getenv("MAX_PARALLEL_TOOLS", "3"))
        
        # Tools
        self.TOOLS_DIR = self.BASE_DIR / "tools"
        self.TOOLS_DIR.mkdir(exist_ok=True)
        
        # Safety
        self.SAFE_MODE = os.getenv("SAFE_MODE", "true").lower() == "true"
        self.MAX_URLS_PER_DOMAIN = int(os.getenv("MAX_URLS_PER_DOMAIN", "10000"))

# Global config instance
config = Config()