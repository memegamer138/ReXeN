"""
Httpx tool wrapper.
Uses httpx to probe URLs and check which are live.

For running through docker, use: 

docker run --rm httpx-image httpx -u https://httpbin.org/ -json
"""

from ..base import Tool
from typing import List, Dict, Any
import subprocess

class HttpxTool(Tool):
    """Wrapper for httpx tool (dockerized)."""
    def __init__(self):
        super().__init__(
            name="httpx",
            command="docker",
            install_url="docker build -f docker/Dockerfile.httpx -t httpx-image ."
        )
        self.image = "httpx-image"

    def run(self, target: List[str], args: List[str]) -> Dict[str, Any]:
        """Run httpx in a Docker container and parse output."""
        import tempfile
        import os
        input_file = None
        docker_cmd = []
        try:
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
                for url in target:
                    f.write(url + "\n")
                input_file = f.name

            docker_cmd = [
                "docker", "run", "--rm",
                "-v", f"{input_file}:/input.txt",
                self.image,
                "httpx", "-l", "/input.txt"
            ] + (args or [])
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            success = result.returncode == 0
            output = result.stdout
            parsed_results = self.parse_output(output) if success and output else []
            return {
                "success": success,
                "stdout": output,
                "stderr": result.stderr,
                "results": parsed_results,
                "result_count": len(parsed_results),
                "command": " ".join(docker_cmd),
                "returncode": result.returncode
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": " ".join(docker_cmd) if docker_cmd else ""
            }
        finally:
            if input_file and os.path.exists(input_file):
                try:
                    os.unlink(input_file)
                except Exception:
                    pass

    def parse_output(self, stdout: str) -> List[Dict[str, Any]]:
        """Parse httpx output into structured results."""
        results = []
        for line in stdout.strip().split("\n"):
            if line:
                # httpx default output: URL [status] [title] [tech]
                parts = line.split()
                url = parts[0]
                status = parts[1] if len(parts) > 1 else None
                results.append({"url": url, "status": status})
        return results