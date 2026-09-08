"""Contracts describing the inputs and outputs of recon tools."""

TOOL_CONTRACTS = {
    "subfinder": {
        "description": "Discover subdomains for the target domain.",
        "requires": ["target"],
        "provides": ["subdomains"],
    },
    "gospider": {
        "description": "Crawl the target and discover URLs and endpoints.",
        "requires": ["target"],
        "provides": ["urls"],
    },
    "katana": {
        "description": "Crawl the target, including JavaScript-linked endpoints.",
        "requires": ["target"],
        "provides": ["urls"],
    },
    "httpx": {
        "description": "Probe candidate URLs and identify live HTTP services.",
        "requires": ["urls"],
        "provides": ["live_urls"],
    },
}


def format_tool_contracts(available_tools):
    """Format contracts for inclusion in a planner prompt."""
    lines = []
    for tool_name in available_tools:
        contract = TOOL_CONTRACTS.get(tool_name)
        if contract is None:
            lines.append(f"- {tool_name}: no contract metadata available")
            continue
        lines.append(
            f"- {tool_name}: {contract['description']} "
            f"Requires: {', '.join(contract['requires'])}. "
            f"Provides: {', '.join(contract['provides'])}."
        )
    return "\n".join(lines)