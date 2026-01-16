"""
Wayback Machine URL discovery tool wrapper.
Uses waybackurls to find historical URLs for a domain.
"""

from ..base import Tool
from typing import List, Dict, Any

class WaybackTool(Tool):
    """Wrapper for waybackurls tool."""
    
    def __init__(self):
        super().__init__(
            name="waybackurls",
            command="waybackurls",
            install_url="go install github.com/tomnomnom/waybackurls@latest"
        )
    
    def run(self, target: str, args: List[str]) -> Dict[str, Any]:
        """Run waybackurls and parse output."""
        # Default args for waybackurls
        default_args = []
        full_args = (args or []) + default_args
        
        result = super().run(target, full_args)
        
        if result["success"]:
            result["urls"] = self.parse_output(result["stdout"])
            result["url_count"] = len(result["urls"])
        
        return result
    
    def parse_output(self, stdout: str) -> List[str]:
        """Extract URLs from waybackurls output."""
        urls = []
        for line in stdout.strip().split("\n"):
            line = line.strip()
            if line and "://" in line:
                urls.append(line)
        return urls