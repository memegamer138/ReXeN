"""
Katana tool wrapper.
Uses katana to crawl a domain and discover URLs.
"""

from ..base import Tool
from typing import List, Dict, Any, Optional
import subprocess

class KatanaTool(Tool):
    """Wrapper for katana tool (dockerized)."""
    def __init__(self):
        super().__init__(
            name="katana",
            command="docker",
            install_url="docker build -f docker/Dockerfile.katana -t katana-image ."
        )
        self.image = "katana-image"

    def run(self, target: str, args: List[str]) -> Dict[str, Any]:
        """Run katana in a Docker container and parse output."""
        docker_cmd = [
            "docker", "run", "--rm",
            self.image,
            "katana", "-u", target, "-d", "2", "-jc", "-silent"
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
            # Pass the target domain to parse_output
            from urllib.parse import urlparse
            parsed = urlparse(target)
            target_domain = parsed.netloc or parsed.path.split('/')[0]
            urls = self.parse_output(output, target_domain) if success else []
            return {
                "success": success,
                "stdout": output,
                "stderr": result.stderr,
                "urls": urls,
                "url_count": len(urls),
                "command": " ".join(docker_cmd),
                "returncode": result.returncode
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": " ".join(docker_cmd)
            }

    def parse_output(self, stdout: str, target_domain: Optional[str] = None) -> List[str]:
        """Extract URLs from katana output, filtering static assets and out-of-scope domains."""
        from urllib.parse import urlparse
        static_exts = (
            ".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff", ".woff2", ".ttf", ".eot", ".otf", ".mp4", ".webm", ".pdf", ".zip", ".tar", ".gz", ".rar", ".7z", ".mp3", ".wav", ".avi", ".mov", ".mkv"
        )
        def is_valid(url):
            try:
                parsed = urlparse(url)
                if not parsed.netloc:
                    return False
                if any(parsed.path.lower().endswith(ext) for ext in static_exts):
                    return False
                if target_domain and parsed.netloc != target_domain:
                    return False
                return True
            except Exception:
                return False
        urls = []
        for line in stdout.strip().split("\n"):
            line = line.strip()
            if line and (line.startswith("http://") or line.startswith("https://")):
                if is_valid(line):
                    urls.append(line)
        return urls
