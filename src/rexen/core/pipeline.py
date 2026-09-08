
"""
Adaptive recon pipeline integrating orchestrator and decision engine.
"""
class RAGStore:
    """
    Simple in-memory RAG store for tool outputs and context.
    """
    def __init__(self):
        self.data = []  # List of (step, tool_name, output)

    def add(self, step, tool_name, output):
        self.data.append({
            "step": step,
            "tool": tool_name,
            "output": output
        })

    def get_context(self):
        """Return all outputs so far as context for the LLM."""
        return self.data.copy()

from rexen.core.orchestrator import Orchestrator
from rexen.core.decision_engine import DecisionEngine
from rexen.core.tool_contracts import format_tool_contracts
from rexen.tools.base import Tool
from rexen.tools.crawlers.gospider import GospiderTool
from rexen.tools.crawlers.katana import KatanaTool
from rexen.tools.discovery.httpx import HttpxTool
from rexen.tools.discovery.subfinder import SubfinderTool
from rexen.reporting.generator import render_template_report


def run_pipeline(user_input=None, target=None):
    """
    Adaptive recon pipeline:
    1. Decision engine selects tools.
    2. Orchestrator runs tools, collects outputs.
    3. Decision engine decides next steps.
    4. Repeat until report.
    """

    # 0. Validate Docker runtime before attempting any tool execution.
    docker_ready, docker_error = Tool.ensure_docker_runtime()
    if not docker_ready:
        raise RuntimeError(f"Docker runtime check failed: {docker_error}")

    # 1. Initialize orchestrator, decision engine, and RAG store
    print("Initializing pipeline...")
    print("[pipeline] Initializing orchestrator, decision engine, and RAG store...")
    orchestrator = Orchestrator()
    decision_engine = DecisionEngine()
    rag_store = RAGStore()

    # 2. Gather available tools
    print("Gathering available tools...")
    print("[pipeline] Gathering available tools...")
    tool_objs = [
        GospiderTool(),
        KatanaTool(),
        HttpxTool(),
        SubfinderTool()
    ]
    tool_map = {tool.name: tool for tool in tool_objs}
    available_tools = list(tool_map.keys())
    tool_contracts = format_tool_contracts(available_tools)
    print(f"[pipeline] Tools available: {available_tools}")

    # 3. Decision engine selects initial tools
    if user_input is None:
        user_input = ""
    if target is None:
        raise ValueError("Target must be specified for the pipeline.")
    print(f"[pipeline] User input: '{user_input}' | Target: '{target}'")
    print("[pipeline] Calling decision engine to choose initial tools...")
    try:
        to_run_raw = decision_engine.choose_tools(
            user_input,
            available_tools,
            tool_contracts=tool_contracts,
        )
    except TypeError as error:
        if "tool_contracts" not in str(error):
            raise
        to_run_raw = decision_engine.choose_tools(user_input, available_tools)
    # Only keep valid tool names (ignore explanations or extra text)
    to_run = [t for t in to_run_raw if t in available_tools]
    print(f"[pipeline] Initial tools to run: {to_run}")
    results = {}
    already_run = set()
    step = 0

    def discovered_urls():
        return any(result.get("urls") for result in results.values())

    while to_run:
        print(f"[pipeline] Loop step {step} | Tools to run: {to_run}")
        # 4. Run selected tools and collect outputs
        for tool_name in to_run:
            if tool_name in already_run or tool_name not in tool_map:
                print(f"[pipeline] Skipping tool '{tool_name}' (already run or not found)")
                continue
            print(f"[pipeline] Running tool: {tool_name}")
            tool = tool_map[tool_name]
            # Httpx expects a list of URLs, others expect a string
            if tool_name == "httpx":
                url_list = []
                for r in results.values():
                    urls = r.get("urls") or r.get("subdomains")
                    if urls:
                        url_list.extend(urls)
                if not url_list:
                    url_list = [target]
                print(f"[pipeline] Calling orchestrator.run_tool for {tool_name} with URLs: {url_list}")
                output = orchestrator.run_tool(tool, target=url_list, args=[])
            else:
                print(f"[pipeline] Calling orchestrator.run_tool for {tool_name} with target: {target}")
                output = orchestrator.run_tool(tool, target, [])
            print(f"[pipeline] Output from {tool_name}: {output}")
            results[tool_name] = output
            rag_store.add(step, tool_name, output)
            already_run.add(tool_name)
            step += 1
        # 5. Decision engine decides next steps, using RAG context
        rag_context = rag_store.get_context()
        print(f"[pipeline] Calling decision engine for next action with results so far...")
        try:
            next_action_raw = decision_engine.next_action(
                results,
                available_tools,
                rag_context=rag_context,
                tool_contracts=tool_contracts,
            )
        except TypeError as error:
            if "tool_contracts" not in str(error):
                raise
            next_action_raw = decision_engine.next_action(
                results,
                available_tools,
                rag_context=rag_context,
            )

        # Only keep valid tool names (ignore explanations or extra text)
        if isinstance(next_action_raw, str):
            next_action = next_action_raw
        elif isinstance(next_action_raw, list):
            next_action = [t for t in next_action_raw if t in available_tools]
        else:
            print(f"[pipeline][warning] Unexpected next_action_raw type: {type(next_action_raw)}. Value: {next_action_raw}")
            # Fallback: if LLM failed, just stop and report
            next_action = "report"

        print(f"[pipeline] Decision engine next action: {next_action}")
        if next_action == "report":
            if "httpx" in tool_map and discovered_urls() and "httpx" not in already_run:
                print("[pipeline] Report deferred; URL discovery requires live URL validation with httpx.")
                to_run = ["httpx"]
                continue
            print("[pipeline] Decision engine requested report. Exiting loop.")
            break
        if isinstance(next_action, list):
            planned_tools = [t for t in next_action if t not in already_run]
            if planned_tools:
                to_run = planned_tools
            elif "httpx" in tool_map and discovered_urls() and "httpx" not in already_run:
                print("[pipeline] URL discovery completed; scheduling required live URL validation with httpx.")
                to_run = ["httpx"]
            else:
                to_run = []
        else:
            to_run = []

        if not to_run:
            print("[pipeline] No additional tools selected. Proceeding to report.")
            break


    # 6. Generate and return report path using template-based reporting with LLM narrative
    print("[pipeline] Generating report (template + LLM)...")
    from rexen.reporting.preprocessor import preprocess_results

    llm_engine = decision_engine

    def llm_generate_fn(prompt):
        """
        Default LLM generation function using a shared DecisionEngine instance.
        """
        query_llm = getattr(llm_engine, "_query_llm", None)
        if query_llm is None:
            return "LLM narrative unavailable; review the structured reconnaissance data below."
        return query_llm(prompt)

    preprocessed = preprocess_results(results, target=target)
    report_path = render_template_report(
        preprocessed=preprocessed,
        target=target,
        results=results,
        output_dir="reports",
        template_path=None,
        llm_generate_fn=llm_generate_fn
    )

    print(f"[pipeline] Report generated at: {report_path}")
    return {"results": results, "report_path": report_path}

if __name__ == "__main__":  # Call direct only for testing
    from rexen.core.pipeline import run_pipeline
    print("\033[33mWarning: Direct pipeline execution detected; this is for testing only.\033[0m")
    target = "https://httpbin.org"
    output = run_pipeline(user_input="Crawl this domain and find all live URLs", target=target)
    print(f"Pipeline completed. Report generated at: {output['report_path']}")