"""
Subfinder tool wrapper.
Uses subfinder to find live subdomains for a domain.
"""

from ..base import Tool
from typing import List, Dict, Any
import subprocess

class SubfinderTool(Tool):
    """Wrapper for subfinder tool (dockerized)."""
    def __init__(self):
        super().__init__(
            name="subfinder",
            command="docker",
            install_url="docker build -f docker/Dockerfile.subfinder -t subfinder-image ."
        )
        self.image = "subfinder-image"

    def run(self, target: str, args: List[str]) -> Dict[str, Any]:
        """Run subfinder in a Docker container and parse output."""
        docker_cmd = [
            "docker", "run", "--rm",
            self.image,
            "subfinder", "-silent", "-d", target
        ] + (args or [])
        try:
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            success = result.returncode == 0
            output = result.stdout
            parsed_subdomains = self.parse_output(output) if success else []
            return {
                "success": success,
                "stdout": output,
                "stderr": result.stderr,
                "subdomains": parsed_subdomains,
                "subdomain_count": len(parsed_subdomains),
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
        """Extract subdomains from subfinder output."""
        return [line.strip() for line in stdout.strip().split("\n") if line.strip()]
