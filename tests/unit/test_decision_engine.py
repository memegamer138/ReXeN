import pytest
from unittest.mock import patch, MagicMock
from rexen.core.decision_engine import DecisionEngine

def test_choose_tools_returns_list():
    engine = DecisionEngine(model="llama3")
    # Patch _query_llm to return a fake tool list
    engine._query_llm = lambda prompt: "httpx, katana"
    tools = engine.choose_tools("example.com", ["httpx", "katana", "gospider"])
    assert tools == ["httpx", "katana"]

def test_next_action_report():
    engine = DecisionEngine(model="llama3")
    engine._query_llm = lambda prompt: "report"
    action = engine.next_action({"httpx": {"success": True}}, ["httpx", "katana"])
    assert action == "report"

def test_next_action_run_more():
    def test_next_action_includes_rag_context_in_prompt():
        engine = DecisionEngine(model="llama3")
        # We'll capture the prompt passed to _query_llm
        captured = {}
        def fake_query_llm(prompt):
            captured['prompt'] = prompt
            return "report"
        engine._query_llm = fake_query_llm
        rag_context = [{"step": 0, "tool": "httpx", "output": {"success": True}}]
        action = engine.next_action({"httpx": {"success": True}}, ["httpx", "katana"], rag_context=rag_context)
        assert action == "report"
        # Check that the RAG context is present in the prompt
        assert "Additional context (RAG):" in captured['prompt']
        assert 'httpx' in captured['prompt']
    engine = DecisionEngine(model="llama3")
    engine._query_llm = lambda prompt: "katana, gospider"
    action = engine.next_action({"httpx": {"success": True}}, ["httpx", "katana", "gospider"])
    assert action == ["katana", "gospider"]