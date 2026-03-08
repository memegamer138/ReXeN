
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
from rexen.tools.crawlers.gospider import GospiderTool
from rexen.tools.crawlers.katana import KatanaTool
from rexen.tools.discovery.httpx import HttpxTool
from rexen.tools.discovery.subfinder import SubfinderTool
from rexen.reporting.generator import generate_report


def run_pipeline(user_input=None, target=None):
    """
    Adaptive recon pipeline:
    1. Decision engine selects tools.
    2. Orchestrator runs tools, collects outputs.
    3. Decision engine decides next steps.
    4. Repeat until report.
    """

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
    print(f"[pipeline] Tools available: {available_tools}")

    # 3. Decision engine selects initial tools
    if user_input is None:
        user_input = ""
    if target is None:
        raise ValueError("Target must be specified for the pipeline.")
    print(f"[pipeline] User input: '{user_input}' | Target: '{target}'")
    print("[pipeline] Calling decision engine to choose initial tools...")
    to_run_raw = decision_engine.choose_tools(user_input, available_tools)
    # Only keep valid tool names (ignore explanations or extra text)
    to_run = [t for t in to_run_raw if t in available_tools]
    print(f"[pipeline] Initial tools to run: {to_run}")
    results = {}
    already_run = set()
    step = 0

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
                output = orchestrator.run_tool(tool, target="", args=url_list)
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
        next_action_raw = decision_engine.next_action(results, available_tools, rag_context=rag_context)
        # Only keep valid tool names (ignore explanations or extra text)
        if isinstance(next_action_raw, str):
            next_action = next_action_raw
        else:
            next_action = [t for t in next_action_raw if t in available_tools]
        print(f"[pipeline] Decision engine next action: {next_action}")
        if next_action == "report":
            print("[pipeline] Decision engine requested report. Exiting loop.")
            break
        to_run = [t for t in next_action if t not in already_run]

    # 6. Generate and return report path
    print("[pipeline] Generating report...")
    report_path = generate_report(results, target)
    print(f"[pipeline] Report generated at: {report_path}")
    return {"results": results, "report_path": report_path}

if __name__ == "__main__":
    from rexen.core.pipeline import run_pipeline
    target = "https://httpbin.org"
    output = run_pipeline(user_input="Crawl this domain and find all live URLs", target=target)
    print(f"Pipeline completed. Report generated at: {output['report_path']}")