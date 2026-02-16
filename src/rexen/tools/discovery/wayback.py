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
            command="docker",
            install_url="docker build -f docker/Dockerfile.waybackurls -t waybackurls-image ."
        )
        self.image = "waybackurls-image"
    
    def run(self, target: str, args: List[str]) -> Dict[str, Any]:
        """Run waybackurls in a Docker container and parse output."""
        import subprocess
        # Compose the docker run command
        docker_cmd = [
            "docker", "run", "--rm",
            self.image,
            "waybackurls"
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
        """Extract URLs from waybackurls output."""
        urls = []
        for line in stdout.strip().split("\n"):
            line = line.strip()
            if line and "://" in line:
                urls.append(line)
        return urls