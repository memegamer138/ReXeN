"""
Simple tool orchestration.
Manages execution of multiple tools with rate limiting.
Coordinates discovery workflows.
"""

import time
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..config import config
from rich.console import Console

console = Console()

class Orchestrator:
    """Manages tool execution."""
    
    def __init__(self, max_workers: Optional[int] = None):
        # Provide default if None
        if max_workers is None:
            max_workers = config.MAX_PARALLEL_TOOLS
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.last_request_time = 0
        
    def rate_limit(self):
        """Simple rate limiting."""
        elapsed = time.time() - self.last_request_time
        if elapsed < 1.0 / config.RATE_LIMIT_RPS:
            time.sleep(1.0 / config.RATE_LIMIT_RPS - elapsed)
        self.last_request_time = time.time()
    
    def run_tool(self, tool, target: str, args=None, **kwargs) -> Dict[str, Any]:
        """Run a single tool with rate limiting."""
        self.rate_limit()
        console.print(f"[dim]Running {tool.name}...[/dim]")
        if args is None:
            args = []
        return tool.run(target, args, **kwargs)
    
    def run_all(self, tools: List, target: str, args=None) -> Dict[str, Any]:
        """Run multiple tools in parallel."""
        results = {}
        futures = {}
        if args is None:
            args = []
        # Submit all tools for execution
        for tool in tools:
            future = self.executor.submit(self.run_tool, tool, target, args)
            futures[future] = tool.name
        # Collect results as they complete
        for future in as_completed(futures):
            tool_name = futures[future]
            try:
                results[tool_name] = future.result()
            except Exception as e:
                results[tool_name] = {
                    "success": False,
                    "error": str(e)
                }
        return results
    
    def shutdown(self):
        """Clean shutdown of executor."""
        self.executor.shutdown(wait=True)