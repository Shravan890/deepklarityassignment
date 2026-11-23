"""Payment provider webhooks. The provider retries a delivery until it gets a 2xx, so events can repeat."""
from . import db


class PaymentError(Exception):
    pass


class Payments:
    def __init__(self, conn):
        self.conn = conn

    def handle_event(self, event, now=None):
        """event: dict(id, type, order_id, amount_cents). Returns the order's status after the event."""
        if event.get("type") != "payment.succeeded":
            return None
        order = self.conn.execute("SELECT * FROM orders WHERE id = ?", (event["order_id"],)).fetchone()
        if order is None:
            raise PaymentError(f"payment for unknown order {event['order_id']}")
        if order["status"] == "cancelled":
            raise PaymentError(f"order {order['id']} is cancelled")
        existing = self.conn.execute("SELECT order_id FROM payments WHERE event_id = ?", (event["id"],)).fetchone()
        if existing is not None:
            if existing["order_id"] != order["id"]:
                raise PaymentError(f"event {event['id']} was already used for another order")
            return "overpaid" if self.paid_cents(order["id"]) > order["total_cents"] else order["status"]

        amount = event["amount_cents"]
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise PaymentError("payment amount must be a positive integer number of cents")
        received = self.paid_cents(order["id"])
        if received == 0 and amount > order["total_cents"]:
            raise PaymentError("payment exceeds the order total")

        self.conn.execute(
            "INSERT INTO payments (order_id, event_id, amount_cents, received_at) VALUES (?, ?, ?, ?)",
            (order["id"], event["id"], amount, db.to_iso(now or db.utcnow())),
        )
        paid = self.paid_cents(order["id"])
        if order["status"] == "pending" and paid >= order["total_cents"]:
            self.conn.execute("UPDATE orders SET status = 'paid' WHERE id = ?", (order["id"],))
            if paid > order["total_cents"]:
                return "overpaid"
            return "paid"
        if paid > order["total_cents"]:
            return "overpaid"
        return order["status"]

    def paid_cents(self, order_id):
        row = self.conn.execute(
            "SELECT COALESCE(SUM(amount_cents), 0) AS paid FROM payments WHERE order_id = ?", (order_id,)
        ).fetchone()
        return row["paid"]
