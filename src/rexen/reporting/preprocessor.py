"""
Preprocessor for recon tool outputs.
Extracts, deduplicates, and organizes data for LLM reporting.
"""

def preprocess_results(results):
    """
    Preprocess and structure tool outputs for LLM reporting.
    Extracts, deduplicates, and organizes subdomains, URLs, live URLs, errors, and tool metadata.
    """
    subdomains = set()
    urls = set()
    live_urls = set()
    errors = []
    tool_info = []

    for tool, output in results.items():
        # Subdomains
        if output.get("subdomains"):
            subdomains.update(output["subdomains"])
        # URLs
        if output.get("urls"):
            urls.update(output["urls"])
        # Live URLs (from httpx or similar)
        if output.get("results"):
            for r in output["results"]:
                status = str(r.get("status", ""))
                if status.startswith("2") or status.startswith("3"):
                    live_urls.add(r.get("url"))
        # Errors
        if output.get("stderr") and output["stderr"].strip():
            errors.append({"tool": tool, "error": output["stderr"]})
        # Tool metadata
        tool_info.append({
            "tool": tool,
            "command": output.get("command"),
            "success": output.get("success"),
            "returncode": output.get("returncode"),
        })

    return {
        "subdomains": sorted(subdomains),
        "urls": sorted(urls),
        "live_urls": sorted(live_urls),
        "errors": errors,
        "tool_info": tool_info,
    }
