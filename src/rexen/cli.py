#!/usr/bin/env python3
"""
Main CLI entry point for ReXeN (ReconSentry).
Provides command-line interface for all recon operations.
Commands: discover, analyze, report, validate, etc.
"""

import click
import json
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
@click.option("--output", "-o", default=None, help="Output file")
@click.option("--simple", is_flag=True, help="Quick discovery only")
def discover(domain, output, simple):
    """
    Discover URLs and endpoints for a domain.
    Uses waybackurls and other discovery tools.
    """
    if not output:
        output = config.RESULTS_DIR / f"{domain}.json"
    
    console.print(f"[bold green]🚀 Starting discovery for {domain}[/bold green]")
    console.print(f"[dim]Results will be saved to: {output}[/dim]")
    
    # Initialize tools
    tools = [WaybackTool()]
    
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
        results = orchestrator.run_all(tools, domain)
        
        progress.update(task, completed=100)
    
    # Process results
    all_urls = []
    for tool_name, result in results.items():
        if result.get("success"):
            urls = result.get("urls", [])
            console.print(f"[green]✓ {tool_name}: Found {len(urls)} URLs[/green]")
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
@click.option("--ai", is_flag=True, help="Use AI analysis")
def analyze(domain, ai):
    """Analyze discovery results."""
    results_file = config.RESULTS_DIR / f"{domain}.json"
    
    if not results_file.exists():
        console.print(f"[red]No results found for {domain}[/red]")
        console.print(f"Run: rexen discover {domain}")
        return
    
    console.print(f"[bold blue]🔍 Analyzing {domain}[/bold blue]")
    
    with open(results_file) as f:
        data = json.load(f)
    
    console.print(f"Found {data['total_urls']} URLs")
    
    # Simple analysis
    from urllib.parse import urlparse
    endpoints = {}
    
    for url in data["urls"][:100]:  # Analyze first 100
        parsed = urlparse(url)
        path = parsed.path
        
        # Categorize by common patterns
        if "api" in path or "api" in parsed.netloc:
            category = "api"
        elif "admin" in path or "admin" in parsed.netloc:
            category = "admin"
        elif "login" in path or "auth" in path:
            category = "auth"
        elif "upload" in path or "file" in path:
            category = "upload"
        else:
            category = "other"
        
        endpoints.setdefault(category, []).append(url)
    
    # Display summary
    table = Table(title="Analysis Summary")
    table.add_column("Category", style="cyan")
    table.add_column("Count", style="green")
    table.add_column("Example", style="yellow")
    
    for category, urls in sorted(endpoints.items()):
        example = urls[0] if urls else "None"
        table.add_row(category, str(len(urls)), example[:50] + "..." if len(example) > 50 else example)
    
    console.print(table)
    
    if ai:
        console.print("[yellow]🤖 AI analysis coming soon...[/yellow]")

if __name__ == "__main__":
    import time
    cli()