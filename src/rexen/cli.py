#!/usr/bin/env python3
"""
Main CLI entry point for ReXeN (ReconSentry).
Provides command-line interface for all recon operations.
Commands: discover, analyze, report, validate, etc.
"""

import os
import click
import json
import time
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TaskProgressColumn
from urllib.parse import urlparse

# Import our modules
from rexen.core.orchestrator import Orchestrator
from rexen.tools.discovery.subfinder import SubfinderTool
from rexen.tools.crawlers.gospider import GospiderTool
from rexen.tools.crawlers.katana import KatanaTool
from rexen.tools.discovery.httpx import HttpxTool
from rexen.config import config
from rexen.core.pipeline import run_pipeline

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

    if not output:
        # Strip scheme (http:// or https://) and trailing slashes for filename
        parsed = urlparse(domain)
        if parsed.netloc:
            safe_domain = parsed.netloc
        else:
            # If no scheme, domain is just the input
            safe_domain = domain.split('/')[0]
        output = config.RESULTS_DIR / f"discover_{safe_domain}.json"
    
    console.print(f"[bold green]Starting discovery for {domain}[/bold green]")
    console.print(f"[dim]Results will be saved to: {output}[/dim]")
    
    user_input = "Discover URLs and endpoints for this domain."
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Running adaptive recon pipeline...", total=None)
        output_obj = run_pipeline(user_input=user_input, target=domain)
        progress.update(task, completed=100)

    results = output_obj.get("results", {})
    report_path = output_obj.get("report_path")
    console.print(f"[green]✓ Adaptive pipeline completed. Report generated at: {report_path}[/green]")
    # Optionally, print summary of results
    for tool, result in results.items():
        console.print(f"[bold]{tool}[/bold]: {result}")
    # Save pipeline results to output file
    output_data = {
        "domain": domain,
        "results": results,
        "report_path": str(report_path),
        "timestamp": time.time()
    }
    with open(output, "w") as f:
        json.dump(output_data, f, indent=2)
    console.print(f"[green] Main report saved to {report_path}[/green]")
    console.print(f"[yellow]For detailed tool outputs, check the JSON file at {output}[/yellow]")


@cli.command()
@click.argument("domain")
@click.option("--output", "-o", help="Output file")
def crawl(domain, output):
    """
    Crawl a domain using gospider and katana to discover URLs.
    Results are saved as crawl_domain.json.
    """
    if not output:
        parsed = urlparse(domain)
        if parsed.netloc:
            safe_domain = parsed.netloc
        else:
            safe_domain = domain.split('/')[0]
        output = config.RESULTS_DIR / f"crawl_{safe_domain}.json"

    console.print(f"[bold green]Starting crawl for {domain}[/bold green]")
    console.print(f"[dim]Results will be saved to: {output}[/dim]")
    tools = [GospiderTool(), KatanaTool()]

    for tool in tools:
        if not tool.is_installed:
            console.print(f"[red]⚠️ {tool.name} not installed[/red]")
            console.print(f"Install with: {tool.install_url}")
            return

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Crawling URLs...", total=None)
        orchestrator = Orchestrator()
        results = orchestrator.run_all(tools, domain, args=[])
        progress.update(task, completed=100)

    all_urls = []
    tool_url_map = {}
    for tool_name, result in results.items():
        if result.get("success"):
            urls = result.get("urls", [])
            tool_url_map[tool_name] = urls
            console.print(f"[green]✓ {tool_name}: Found {len(urls)} URLs[/green]")
            for url in urls[:3]:
                console.print(f"    [dim]{url}[/dim]")
            all_urls.extend(urls)
        else:
            console.print(f"[red]✗ {tool_name}: Failed - {result.get('error', 'Unknown error')}[/red]")

    unique_urls = list(set(all_urls))
    console.print(f"[bold]Total unique URLs found: {len(unique_urls)}[/bold]")

    output_data = {
        "domain": domain,
        "total_urls": len(unique_urls),
        "urls": unique_urls,
        "tools_used": list(results.keys()),
        "timestamp": time.time()
    }

    with open(output, "w") as f:
        json.dump(output_data, f, indent=2)

    console.print(f"[green] Results saved to {output}[/green]")

    if unique_urls:
        console.print("\n[bold]Sample URLs:[/bold]")
        for url in unique_urls[:5]:
            console.print(f"  • {url}")
        if len(unique_urls) > 5:
            console.print(f"  • ... and {len(unique_urls) - 5} more")
            

@cli.command()
@click.argument("input", nargs=1)
@click.option("--limit", help="Max URLs to probe (e.g. --limit 1000 scans first 1000 URLs)")
def analyze(input, limit):
    """
    Probe URLs with httpx to find live sites.
    INPUT can be:
      - a single URL (http/https)
      - a path to a JSON file with a 'urls' array
      - a path to a text file with one URL per line
    """

    def is_valid_url(url):
        try:
            parsed = urlparse(url)
            return parsed.scheme in ("http", "https") and parsed.netloc and not any(c in url for c in [' ', '\'', '"', '<', '>', '{', '}', '|', '`'])
        except Exception:
            return False

    urls = []
    # If input looks like a URL, validate and use it directly
    if input.startswith("http://") or input.startswith("https://"):
        if not is_valid_url(input):
            console.print(f"[red]Input '{input}' is not a valid URL.[/red]")
    elif os.path.isfile(input):
        # Try to load as JSON first
        try:
            with open(input, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and "urls" in data:
                urls = [u for u in data["urls"] if is_valid_url(u)]
        except Exception:
            # Not JSON, try as plain text
            with open(input, "r", encoding="utf-8") as f:
                urls = [line.strip() for line in f if is_valid_url(line.strip())]
    else:
        console.print(f"[red]Input '{input}' is not a valid URL or file.[/red]")
        return

    if limit:
        try:
            limit = int(limit)
        except Exception:
            console.print(f"[red]Invalid limit value: {limit}. Using all URLs.[/red]")
            limit = None
    if limit:
        urls = urls[:limit]
    if not urls:
        console.print(f"[red]No valid URLs to probe.[/red]")
        return
    console.print(f"[bold blue]Probing {len(urls)} URLs for liveness with httpx...[/bold blue]")
    if urls:
        console.print("[yellow]First 10 URLs sent to httpx:[/yellow]")
        for u in urls[:10]:
            console.print(f"  [dim]{u}[/dim]")

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("Running httpx...", total=None)
        httpx_tool = HttpxTool()
        result = httpx_tool.run(urls, args=["-rl", "4"])
        progress.update(task, completed=100)
    if not result["success"]:
        console.print(f"[red]httpx failed: {result.get('error', 'Unknown error')}[/red]")
        return
    results = result["results"]
    console.print(f"[yellow]Parsed results sample (first 5):[/yellow] {results[:5]}")
    import re
    live = []
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task(f"Filtering live URLs...", total=len(results))
        for r in results:
            status = r.get("status")
            if status:
                match = re.search(r"(\d{3})", status)
                if match:
                    code = int(match.group(1))
                    if 200 <= code < 400:
                        live.append(r)
            progress.advance(task)
    table = Table(title="Live URLs (Status 2xx/3xx)")
    table.add_column("URL", style="cyan")
    table.add_column("Status", style="green")
    for r in live:
        table.add_row(r["url"], r["status"] or "?")
    console.print(table)
    console.print(f"[bold]Total live URLs: {len(live)}[/bold]")

if __name__ == "__main__":
    cli()