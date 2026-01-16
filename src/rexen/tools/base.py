"""
Base class for all tool wrappers.
Provides common functionality: execution, error handling, output parsing.
Each tool inherits from this class.
"""

import subprocess
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from ..config import config

class Tool:
    """Base class for security tool wrappers."""
    
    def __init__(self, name: str, command: str, install_url: str = ""):
        self.name = name
        self.command = command
        self.install_url = install_url
        self.is_installed = self._check_installation()
    
    def _check_installation(self) -> bool:
        """Check if tool is installed."""
        try:
            subprocess.run([self.command, "--version"], 
                          capture_output=True, check=False)
            return True
        except (FileNotFoundError, PermissionError):
            return False
    
    def run(self, target: str, args: List[str]) -> Dict[str, Any]:
        """
        Run the tool against a target.
        Returns dict with stdout, stderr, and success status.
        """
        if not self.is_installed:
            return {
                "success": False,
                "error": f"Tool {self.name} not installed",
                "install_url": self.install_url
            }
        
        cmd = [self.command] + (args or []) + [target]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes max
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(cmd),
                "returncode": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command timed out after 5 minutes"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def parse_output(self, stdout: str) -> List[Any]:
        """Parse tool-specific output. Override in subclasses."""
        return stdout.strip().split("\n")