"""A tiny fake back-office (orders, refunds, knowledge base) the agent can act on."""
from __future__ import annotations

import json
import re

from .tools import Tool, ToolError


class Shop:
    def __init__(self) -> None:
        self.orders = {
            "ORD-1001": {"status": "delivered", "total": 49.90, "items": ["Headphones"], "delivered_days_ago": 3},
            "ORD-1002": {"status": "delivered", "total": 240.00, "items": ["Monitor"], "delivered_days_ago": 5},
            "ORD-1003": {"status": "delivered", "total": 89.00, "items": ["Keyboard"], "delivered_days_ago": 45},
            "ORD-1004": {"status": "in_transit", "total": 35.00, "items": ["Mouse"], "delivered_days_ago": None},
        }
        self.refunds: list[dict] = []
        self.escalations: list[str] = []
        self.kb = [
            ("Refund policy", "Items can be refunded within 30 days of delivery. Refunds are returned to the original payment method in 5 business days."),
            ("Shipping times", "Standard shipping takes 3 to 7 business days. Tracking is emailed when the order ships."),
            ("Password reset", "Use the Forgot password link on the login page. The reset email expires after 30 minutes."),
        ]

    # --- tool implementations -------------------------------------------------
    def get_order(self, order_id: str) -> str:
        order = self.orders.get(order_id)
        if not order:
            raise ToolError(f"order {order_id} not found")
        return json.dumps({"order_id": order_id, **order})

    def search_kb(self, query: str) -> str:
        words = set(re.findall(r"\w+", query.lower()))
        scored = sorted(((len(words & set(re.findall(r"\w+", (t + " " + b).lower()))), t, b) for t, b in self.kb),
                        reverse=True)
        best = [f"{t}: {b}" for s, t, b in scored[:2] if s > 0]
        return "\n".join(best) or "no relevant article found"

    def issue_refund(self, order_id: str, amount: float) -> str:
        order = self.orders.get(order_id)
        if not order:
            raise ToolError(f"order {order_id} not found")
        if order["status"] != "delivered":
            raise ToolError("only delivered orders can be refunded")
        if order["delivered_days_ago"] > 30:
            raise ToolError("outside the 30-day refund window")
        if amount <= 0 or amount > order["total"]:
            raise ToolError(f"amount must be between 0 and {order['total']}")
        if any(r["order_id"] == order_id for r in self.refunds):
            raise ToolError("order already refunded")
        self.refunds.append({"order_id": order_id, "amount": amount})
        return f"refund of {amount:.2f} issued for {order_id}"

    def escalate(self, reason: str) -> str:
        self.escalations.append(reason)
        return "ticket escalated to a human agent"


def build_tools(shop: Shop) -> list[Tool]:
    return [
        Tool("get_order", "Look up an order by id (format ORD-1234).",
             {"type": "object", "properties": {"order_id": {"type": "string"}}, "required": ["order_id"]},
             shop.get_order),
        Tool("search_kb", "Search the help-center knowledge base.",
             {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
             shop.search_kb),
        Tool("issue_refund", "Refund an order. Amounts above the automatic limit need human approval.",
             {"type": "object",
              "properties": {"order_id": {"type": "string"}, "amount": {"type": "number"}},
              "required": ["order_id", "amount"]},
             shop.issue_refund),
        Tool("escalate", "Hand the ticket to a human agent, with a reason.",
             {"type": "object", "properties": {"reason": {"type": "string"}}, "required": ["reason"]},
             shop.escalate),
    ]
