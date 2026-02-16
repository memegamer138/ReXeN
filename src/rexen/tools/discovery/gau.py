"""
GAU (GetAllUrls) tool wrapper.
Uses gau to find historical and indexed URLs for a domain.
"""

from ..base import Tool
from typing import List, Dict, Any
import subprocess

class GauTool(Tool):
    """Wrapper for gau tool (dockerized)."""
    def __init__(self):
        super().__init__(
            name="gau",
            command="docker",
            install_url="docker build -f docker/Dockerfile.gau -t gau-image ."
        )
        self.image = "gau-image"

    def run(self, target: str, args: List[str]) -> Dict[str, Any]:
        """Run gau in a Docker container and parse output."""
        docker_cmd = [
            "docker", "run", "--rm",
            self.image,
            "gau"
        ] + (args or []) + [target]
        try:
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            success = result.returncode == 0
            output = result.stdout
            parsed_urls = self.parse_output(output) if success else []
            return {
                "success": success,
                "stdout": output,
                "stderr": result.stderr,
                "urls": parsed_urls,
                "url_count": len(parsed_urls),
                "command": " ".join(docker_cmd),
                "returncode": result.returncode
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": " ".join(docker_cmd)
            }

    def parse_output(self, stdout: str) -> List[str]:
        """Extract URLs from gau output."""
        urls = []
        for line in stdout.strip().split("\n"):
            line = line.strip()
            if line and "//" in line:
                urls.append(line)
        return urls
