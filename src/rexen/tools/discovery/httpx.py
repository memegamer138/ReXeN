"""
Httpx tool wrapper.
Uses httpx to probe URLs and check which are live.

For running through docker, use: 

docker run --rm httpx-image httpx -u https://httpbin.org/ -json
"""

from ..base import Tool
from typing import List, Dict, Any
import subprocess
import json
import re

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
                "httpx", "-l", "/input.txt", "-status-code"
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
            line = re.sub(r"\x1b\[[0-9;]*m", "", line).strip()
            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                record = None

            if isinstance(record, dict) and record.get("url"):
                status = record.get("status") or record.get("status_code")
                results.append({
                    "url": record["url"],
                    "status": str(status) if status is not None else None,
                })
                continue

            # httpx text output: URL [status] [title] [technology]
            match = re.match(r"^(\S+)(?:\s+\[(\d{3})\])?", line)
            if match:
                results.append({
                    "url": match.group(1),
                    "status": match.group(2),
                })
        return results