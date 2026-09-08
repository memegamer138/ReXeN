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
    live_url_records = []
    probed_urls = set()
    failed_urls = set()
    failed_url_records = []
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
                url = r.get("url")
                status = str(r.get("status", ""))
                if url:
                    probed_urls.add(url)
                if status.startswith("2") or status.startswith("3"):
                    live_urls.add(url)
                    live_url_records.append({"url": url, "status": status})
                    evidence.append({
                        "asset": url,
                        "type": "live_url_validated",
                        "confidence": "validated",
                        "source": tool,
                        "status": status,
                    })
                elif status.startswith(("4", "5")):
                    failed_urls.add(url)
                    failed_url_records.append({"url": url, "status": status})
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
            probed_urls = {
                url for url in probed_urls
                if urlparse(url).hostname == target_host
                or (urlparse(url).hostname and urlparse(url).hostname.endswith(f".{target_host}"))
            }
            failed_urls = {
                url for url in failed_urls
                if urlparse(url).hostname == target_host
                or (urlparse(url).hostname and urlparse(url).hostname.endswith(f".{target_host}"))
            }
            failed_url_records = [
                record for record in failed_url_records
                if record["url"] in failed_urls
            ]
            live_url_records = [
                record for record in live_url_records
                if record["url"] in live_urls
            ]

    live_url_records = sorted(
        { (record["url"], record["status"]): record for record in live_url_records }.values(),
        key=lambda record: record["url"],
    )

    return {
        "subdomains": sorted(subdomains),
        "urls": sorted(urls),
        "out_of_scope_urls": sorted(out_of_scope_urls),
        "live_urls": sorted(live_urls),
        "live_url_records": live_url_records,
        "failed_url_records": sorted(failed_url_records, key=lambda record: record["url"]),
        "live_probe_completed": "httpx" in results,
        "counts": {
            "subdomains": len(subdomains),
            "discovered_urls": len(urls),
            "out_of_scope_urls": len(out_of_scope_urls),
            "probed_urls": len(probed_urls),
            "live_urls": len(live_urls),
            "failed_urls": len(failed_urls),
        },
        "errors": errors,
        "tool_info": tool_info,
        "evidence": evidence,
    }
