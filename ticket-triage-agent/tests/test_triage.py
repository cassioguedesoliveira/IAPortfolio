import json
import unittest

from triage import Agent, Shop, build_tools
from triage.guardrails import redact_pii
from triage.llm import AnthropicToolLLM, PolicyLLM, ScriptedLLM
from triage.tools import ToolError, ToolRegistry, validate_args
from triage.types import Message, Reply, ToolCall


def make(llm, **kw):
    shop = Shop()
    return shop, Agent(llm, ToolRegistry(build_tools(shop)), **kw)


def final(**over):
    data = {"category": "billing", "priority": "normal", "reply": "ok", "needs_human": False} | over
    return Reply(text=json.dumps(data))


class RedactionTests(unittest.TestCase):
    def test_redacts_common_pii(self):
        text = "Mail me at ana@example.com, CPF 123.456.789-09, card 4111 1111 1111 1111"
        out = redact_pii(text)
        self.assertNotIn("ana@example.com", out)
        self.assertNotIn("123.456.789-09", out)
        self.assertNotIn("4111", out)
        self.assertIn("[EMAIL]", out)

    def test_order_ids_survive(self):
        self.assertIn("ORD-1001", redact_pii("refund ORD-1001 please"))


class ToolValidationTests(unittest.TestCase):
    schema = {"properties": {"amount": {"type": "number"}}, "required": ["amount"]}

    def test_rejects_bad_calls(self):
        for bad in ({}, {"amount": "10"}, {"amount": True}, {"amount": 1, "extra": 2}):
            with self.assertRaises(ToolError):
                validate_args(self.schema, bad)

    def test_accepts_good_call(self):
        validate_args(self.schema, {"amount": 10})


class AgentBehaviourTests(unittest.TestCase):
    def test_small_refund_is_executed_automatically(self):
        shop, agent = make(PolicyLLM())
        result = agent.run("Please refund ORD-1001, headphones broke")
        self.assertEqual(result.status, "resolved")
        self.assertEqual(shop.refunds, [{"order_id": "ORD-1001", "amount": 49.90}])
        self.assertEqual([a["tool"] for a in result.actions], ["get_order", "issue_refund"])

    def test_large_refund_is_blocked_and_escalated(self):
        shop, agent = make(PolicyLLM())
        result = agent.run("I want a refund for ORD-1002")
        self.assertEqual(result.status, "needs_human")
        self.assertEqual(shop.refunds, [])  # money never moved
        self.assertIn("exceeds the automatic limit", result.reason)

    def test_policy_overrides_a_model_that_claims_no_human_needed(self):
        llm = ScriptedLLM([
            Reply(tool_calls=[ToolCall("1", "issue_refund", {"order_id": "ORD-1002", "amount": 240.0})]),
            final(needs_human=False),
        ])
        shop, agent = make(llm)
        self.assertEqual(agent.run("refund").status, "needs_human")
        self.assertEqual(shop.refunds, [])

    def test_business_rule_errors_go_back_to_the_model(self):
        shop, agent = make(PolicyLLM())
        result = agent.run("refund ORD-1003 please")  # delivered 45 days ago
        self.assertEqual(result.status, "needs_human")
        self.assertIn("refund window", result.trace[-1]["result"])
        self.assertEqual(shop.refunds, [])

    def test_unknown_tool_does_not_crash_the_run(self):
        llm = ScriptedLLM([Reply(tool_calls=[ToolCall("1", "delete_database", {})]), final()])
        _, agent = make(llm)
        result = agent.run("hello")
        self.assertIn("unknown tool", result.trace[0]["result"])
        self.assertEqual(result.status, "resolved")

    def test_infinite_loop_is_stopped(self):
        _, agent = make(ScriptedLLM([]), max_steps=3)
        result = agent.run("hello")
        self.assertEqual(result.status, "aborted")
        self.assertIn("3 steps", result.reason)

    def test_tool_call_budget(self):
        many = Reply(tool_calls=[ToolCall(str(i), "search_kb", {"query": "x"}) for i in range(5)])
        _, agent = make(ScriptedLLM([many, many]), max_tool_calls=6)
        result = agent.run("hello")
        self.assertEqual(result.status, "aborted")
        self.assertIn("budget", result.reason)

    def test_invalid_final_answer_goes_to_human(self):
        _, agent = make(ScriptedLLM([Reply(text="sure, all done!")]))
        self.assertEqual(agent.run("hello").status, "needs_human")
        _, agent = make(ScriptedLLM([final(category="made-up")]))
        self.assertEqual(agent.run("hello").status, "needs_human")

    def test_pii_never_reaches_the_model(self):
        llm = ScriptedLLM([final()])
        _, agent = make(llm)
        agent.run("My email is ana@example.com and my card is 4111 1111 1111 1111")
        shown = " ".join(m.content for m in llm.seen[0])
        self.assertNotIn("ana@example.com", shown)
        self.assertNotIn("4111", shown)


class AnthropicAdapterTests(unittest.TestCase):
    def test_message_conversion_groups_tool_results(self):
        msgs = [
            Message("user", "hi"),
            Message("assistant", "checking", tool_calls=[ToolCall("a", "get_order", {"order_id": "ORD-1"}),
                                                          ToolCall("b", "search_kb", {"query": "x"})]),
            Message("tool", "r1", tool_call_id="a"),
            Message("tool", "r2", tool_call_id="b"),
        ]
        out = AnthropicToolLLM.convert(msgs)
        self.assertEqual([m["role"] for m in out], ["user", "assistant", "user"])
        self.assertEqual(len(out[2]["content"]), 2)
        self.assertEqual(out[1]["content"][1]["type"], "tool_use")


if __name__ == "__main__":
    unittest.main()
