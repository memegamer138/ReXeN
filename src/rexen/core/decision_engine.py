"""
Decision engine for recon pipeline using Ollama LLM (llama3).
Analyzes tool outputs and decides next steps.
"""

import requests
import json

class DecisionEngine:
    def __init__(self, model="llama3.1:8b"):
        self.model = model
        self.ollama_url = "http://localhost:11434/api/generate"

    def choose_tools(self, user_input, available_tools):
        """
        Decide which tools to run based on user input and available tools.
        Returns a list of tool names.
        """
        prompt = f"""
You are a recon workflow decision engine.
The user provided: {user_input}
Available tools: {', '.join(available_tools)}
Reply ONLY with a comma-separated list of tool names to run first. Do NOT include any explanation, reasoning, or extra text. Example: subfinder,katana
"""
        response = self._query_llm(prompt)
        return self._parse_tool_list(response)

    def next_action(self, tool_outputs, available_tools, rag_context=None):
        """
        Decide next steps based on tool outputs and optional RAG context.
        Returns: 'report' or a list of tool names to run next.
        rag_context: Optional, additional context (e.g., all previous tool outputs) for LLM.
        """
        prompt = f"""
You are a recon workflow decision engine. Here are the outputs from previous tools:
{json.dumps(tool_outputs, indent=2)}
Available tools: {', '.join(available_tools)}
If more tools should be run, reply ONLY with a comma-separated list of tool names. If a report should be generated, reply ONLY with 'report'. Do NOT include any explanation, reasoning, or extra text.
"""
        if rag_context is not None:
            prompt += f"\nAdditional context (RAG):\n{json.dumps(rag_context, indent=2)}\n"
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
