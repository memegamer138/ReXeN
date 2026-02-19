"""
Decision engine for recon pipeline using Ollama LLM (llama3).
Analyzes tool outputs and decides next steps.
"""

import requests
import json

class DecisionEngine:
    def __init__(self, model="llama3"):
        self.model = model
        self.ollama_url = "http://localhost:11434/api/generate"

    def choose_tools(self, user_input, available_tools):
        """
        Decide which tools to run based on user input and available tools.
        Returns a list of tool names.
        """
        prompt = f"""
You are a recon workflow decision engine. The user provided: {user_input}
Available tools: {', '.join(available_tools)}
Which tools should be run first for optimal recon? Reply with a comma-separated list of tool names.
"""
        response = self._query_llm(prompt)
        return self._parse_tool_list(response)

    def next_action(self, tool_outputs, available_tools):
        """
        Decide next steps based on tool outputs.
        Returns: 'run_more', 'report', or a list of tool names to run next.
        """
        prompt = f"""
You are a recon workflow decision engine. Here are the outputs from previous tools:
{json.dumps(tool_outputs, indent=2)}
Available tools: {', '.join(available_tools)}
Should more tools be run, or should a report be generated? If more tools, list them. If report, reply 'report'.
"""
        response = self._query_llm(prompt)
        if "report" in response.lower():
            return "report"
        return self._parse_tool_list(response)

    def _query_llm(self, prompt):
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        try:
            resp = requests.post(self.ollama_url, json=data)
            resp.raise_for_status()
            result = resp.json()
            return result.get("response", "")
        except Exception as e:
            return f"Error querying LLM: {e}"

    def _parse_tool_list(self, response):
        # Extract comma-separated tool names
        tools = [t.strip() for t in response.split(",") if t.strip()]
        return tools
