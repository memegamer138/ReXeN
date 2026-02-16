#!/usr/bin/env python3
"""
Main CLI entry point for ReXeN (ReconSentry).
Provides command-line interface for all recon operations.
Commands: discover, analyze, report, validate, etc.
"""

import click
import json
import time
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# Import our modules
from rexen.core.orchestrator import Orchestrator
from rexen.tools.discovery.wayback import WaybackTool
from rexen.config import config

console = Console()

@click.group()
@click.version_option(version="0.1.0")
def cli():
    """ReXeN - AI-Powered Bug Bounty Recon Assistant"""
    pass

@cli.command()
@click.argument("domain")
@click.option("--output", "-o", help="Output file")
@click.option("--simple", is_flag=True, help="Quick discovery only")
def discover(domain, output, simple):
    """
    Discover URLs and endpoints for a domain.
    Uses waybackurls and other discovery tools.
    """
    from urllib.parse import urlparse
    if not output:
        # Strip scheme (http:// or https://) and trailing slashes for filename
        parsed = urlparse(domain)
        if parsed.netloc:
            safe_domain = parsed.netloc
        else:
            # If no scheme, domain is just the input
            safe_domain = domain.split('/')[0]
        output = config.RESULTS_DIR / f"{safe_domain}.json"
    
    console.print(f"[bold green]🚀 Starting discovery for {domain}[/bold green]")
    console.print(f"[dim]Results will be saved to: {output}[/dim]")
    
    from rexen.tools.discovery.gau import GauTool
    # Initialize tools
    tools = [WaybackTool(), GauTool()]
    
    # Check installation
    for tool in tools:
        if not tool.is_installed:
            console.print(f"[red]⚠️ {tool.name} not installed[/red]")
            console.print(f"Install with: {tool.install_url}")
            return
    
    # Run discovery
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Discovering URLs...", total=None)
        
        orchestrator = Orchestrator()
        # Pass empty args list to each tool
        results = orchestrator.run_all(tools, domain, args=[])
        
        progress.update(task, completed=100)
    

    # Process results and print per-tool stats
    all_urls = []
    tool_url_map = {}
    for tool_name, result in results.items():
        if result.get("success"):
            urls = result.get("urls", [])
            tool_url_map[tool_name] = urls
            console.print(f"[green]✓ {tool_name}: Found {len(urls)} URLs[/green]")
            # Show up to 3 sample URLs per tool
            for url in urls[:3]:
                console.print(f"    [dim]{url}[/dim]")
            all_urls.extend(urls)
        else:
            console.print(f"[red]✗ {tool_name}: Failed - {result.get('error', 'Unknown error')}[/red]")

    # Deduplicate and save
    unique_urls = list(set(all_urls))
    console.print(f"[bold]📊 Total unique URLs found: {len(unique_urls)}[/bold]")
    
    # Save results
    output_data = {
        "domain": domain,
        "total_urls": len(unique_urls),
        "urls": unique_urls,
        "tools_used": list(results.keys()),
        "timestamp": time.time()
    }
    
    with open(output, "w") as f:
        json.dump(output_data, f, indent=2)
    
    console.print(f"[green]✅ Results saved to {output}[/green]")
    
    # Show sample URLs
    if unique_urls:
        console.print("\n[bold]Sample URLs:[/bold]")
        for url in unique_urls[:5]:  # Show first 5
            console.print(f"  • {url}")
        if len(unique_urls) > 5:
            console.print(f"  • ... and {len(unique_urls) - 5} more")

@cli.command()
@click.argument("domain")
@click.option("--limit", help="Max URLs to probe")
def analyze(domain, limit):
    """Probe discovered URLs with httpx to find live sites."""
    from rexen.tools.discovery.httpx import HttpxTool
    from urllib.parse import urlparse
    # Normalize domain to match discover's output filename logic
    parsed = urlparse(domain)
    if parsed.netloc:
        safe_domain = parsed.netloc
    else:
        safe_domain = domain.split('/')[0]
    results_file = config.RESULTS_DIR / f"{safe_domain}.json"
    if not results_file.exists():
        console.print(f"[red]No results found for {domain}[/red]")
        console.print(f"Run: rexen discover {domain}")
        return
    with open(results_file) as f:
        data = json.load(f)
    # Pass all URLs from the JSON's urls array directly to httpx
    from urllib.parse import urlparse
    def is_valid_url(url):
        try:
            parsed = urlparse(url)
            return parsed.scheme in ("http", "https") and parsed.netloc and not any(c in url for c in [' ', '\'', '"', '<', '>', '{', '}', '|', '`'])
        except Exception:
            return False

    # Clean and filter URLs before probing
    urls = [u for u in data["urls"] if is_valid_url(u)][:limit]
    console.print(f"[bold blue]Probing {len(urls)} URLs for liveness with httpx...[/bold blue]")
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TaskProgressColumn
    # Show spinner while httpx runs
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("Running httpx...", total=None)
        httpx_tool = HttpxTool()
        # Add rate limit to httpx (4 req/sec = 240/min)
        result = httpx_tool.run(urls, args=["-rl", "4"])
        progress.update(task, completed=100)
    if not result["success"]:
        console.print(f"[red]httpx failed: {result.get('error', 'Unknown error')}[/red]")
        return

    # Debug: print a sample of the raw httpx output
    console.print("[yellow]--- httpx raw stdout (first 10 lines) ---[/yellow]")
    for line in result.get("stdout", "").splitlines()[:10]:
        console.print(line)
    console.print("[yellow]--- end httpx raw stdout ---[/yellow]")

    # Debug: print a sample of the parsed results
    results = result["results"]
    console.print(f"[yellow]Parsed results sample (first 5):[/yellow] {results[:5]}")

    live = []
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task(f"Filtering live URLs...", total=len(results))
        for r in results:
            if r.get("status") and (r["status"].startswith("[2") or r["status"].startswith("[3")):
                live.append(r)
            progress.advance(task)
    table = Table(title="Live URLs (Status 2xx)")
    table.add_column("URL", style="cyan")
    table.add_column("Status", style="green")
    for r in live:
        table.add_row(r["url"], r["status"] or "?")
    console.print(table)
    console.print(f"[bold]Total live URLs: {len(live)}[/bold]")

if __name__ == "__main__":
    import time
    cli()