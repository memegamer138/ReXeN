"""
Decision engine for recon pipeline using Ollama LLM (llama3).
Analyzes tool outputs and decides next steps.
"""

import requests
import json
from rexen.core.tool_contracts import format_tool_contracts

class DecisionEngine:
    def __init__(self, model="llama3.1:8b"):
        self.model = model
        self.ollama_url = "http://localhost:11434/api/generate"

    def choose_tools(self, user_input, available_tools, tool_contracts=None):
        """
        Decide which tools to run based on user input and available tools.
        Returns a list of tool names.
        """
        prompt = f"""
You are a recon workflow decision engine.
The user provided: {user_input}
Available tools: {', '.join(available_tools)}
Tool contracts:
{tool_contracts or format_tool_contracts(available_tools)}
Return JSON only in this shape:
{{"action": "continue", "tools": ["subfinder", "katana"], "reason": "brief reason"}}
Choose only from the available tools. Do not include explanations outside the JSON object.
"""
        response = self._query_structured(prompt)
        parsed = self._parse_plan(response)
        return parsed.get("tools", [])

    def next_action(self, tool_outputs, available_tools, rag_context=None, tool_contracts=None):
        """
        Decide next steps based on tool outputs and optional RAG context.
        Returns: 'report' or a list of tool names to run next.
        rag_context: Optional, additional context (e.g., all previous tool outputs) for LLM.
        """
        prompt = f"""
You are a recon workflow decision engine. Here are the outputs from previous tools:
{json.dumps(tool_outputs, indent=2)}
Available tools: {', '.join(available_tools)}
Tool contracts:
{tool_contracts or format_tool_contracts(available_tools)}
Return JSON only in this shape:
{{"action": "continue", "tools": ["httpx"], "reason": "brief reason"}}
or:
{{"action": "report", "tools": [], "reason": "brief reason"}}
Choose only from the available tools. Do not include explanations outside the JSON object.
"""
        if rag_context is not None:
            prompt += f"\nAdditional context (RAG):\n{json.dumps(rag_context, indent=2)}\n"
        response = self._query_structured(prompt)
        parsed = self._parse_plan(response)
        if parsed.get("action") == "report":
            return "report"
        return parsed.get("tools", [])

    def _query_llm(self, prompt, json_mode=False):
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        if json_mode:
            data["format"] = "json"
        try:
            resp = requests.post(self.ollama_url, json=data)
            resp.raise_for_status()
            result = resp.json()
            return result.get("response", "")
        except Exception as e:
            return f"Error querying LLM: {e}"

    def _query_structured(self, prompt):
        """Request structured output while supporting simple test doubles."""
        try:
            return self._query_llm(prompt, json_mode=True)
        except TypeError as error:
            if "json_mode" not in str(error):
                raise
            return self._query_llm(prompt)

    def _parse_tool_list(self, response):
        # Extract comma-separated tool names
        tools = [t.strip() for t in response.split(",") if t.strip()]
        return tools

    def _parse_plan(self, response):
        """Parse a structured plan, with a legacy text fallback."""
        text = response.strip()
        try:
            plan = json.loads(text)
            if isinstance(plan, dict):
                tools = plan.get("tools", [])
                if isinstance(tools, list):
                    return {
                        "action": plan.get("action", "continue"),
                        "tools": [tool.strip() for tool in tools if isinstance(tool, str)],
                        "reason": plan.get("reason", ""),
                    }
        except json.JSONDecodeError:
            pass

        if "report" in text.lower():
            return {"action": "report", "tools": [], "reason": "Legacy planner response requested a report."}
        return {"action": "continue", "tools": self._parse_tool_list(text), "reason": "Legacy planner response."}
