"""
Preprocessor for recon tool outputs.
Extracts, deduplicates, and organizes data for LLM reporting.
"""
from urllib.parse import urlparse

def preprocess_results(results, target=None):
    """
    Preprocess and structure tool outputs for LLM reporting.
    Extracts, deduplicates, and organizes subdomains, URLs, live URLs, errors, and tool metadata.
    """
    subdomains = set()
    urls = set()
    out_of_scope_urls = set()
    live_urls = set()
    errors = []
    tool_info = []
    evidence = []

    for tool, output in results.items():
        # Subdomains
        if output.get("subdomains"):
            subdomains.update(output["subdomains"])
            evidence.extend({
                "asset": subdomain,
                "type": "subdomain_discovered",
                "confidence": "observed",
                "source": tool,
            } for subdomain in output["subdomains"])
        # URLs
        if output.get("urls"):
            urls.update(output["urls"])
            evidence.extend({
                "asset": url,
                "type": "url_discovered",
                "confidence": "observed",
                "source": tool,
            } for url in output["urls"])
        # Live URLs (from httpx or similar)
        if output.get("results"):
            for r in output["results"]:
                status = str(r.get("status", ""))
                if status.startswith("2") or status.startswith("3"):
                    live_urls.add(r.get("url"))
                    evidence.append({
                        "asset": r.get("url"),
                        "type": "live_url_validated",
                        "confidence": "validated",
                        "source": tool,
                        "status": status,
                    })
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

    if target:
        target_host = urlparse(target if "://" in target else f"https://{target}").hostname
        if target_host:
            in_scope_urls = set()
            for url in urls:
                url_host = urlparse(url).hostname
                if url_host == target_host or (url_host and url_host.endswith(f".{target_host}")):
                    in_scope_urls.add(url)
                else:
                    out_of_scope_urls.add(url)
            urls = in_scope_urls
            live_urls = {
                url for url in live_urls
                if urlparse(url).hostname == target_host
                or (urlparse(url).hostname and urlparse(url).hostname.endswith(f".{target_host}"))
            }

    return {
        "subdomains": sorted(subdomains),
        "urls": sorted(urls),
        "out_of_scope_urls": sorted(out_of_scope_urls),
        "live_urls": sorted(live_urls),
        "live_probe_completed": "httpx" in results,
        "errors": errors,
        "tool_info": tool_info,
        "evidence": evidence,
    }
