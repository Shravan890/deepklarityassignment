import os
import tempfile
import threading
import unittest
from datetime import datetime, timezone

from tillpoint import db, reports
from tillpoint.api import App
from tillpoint.catalog import OutOfStock
from tillpoint.payments import PaymentError


class RegressionTest(unittest.TestCase):
    def setUp(self):
        self.conn = db.connect()
        self.app = App(self.conn)
        self.app.catalog.add_product("SKU", "Test", 1000, stock=5)
        self.conn.execute("INSERT INTO coupons (code, kind, value) VALUES ('TEN', 'percent', 10)")

    def tearDown(self):
        self.conn.close()

    def payment(self, order, event_id, amount, now=None):
        return self.app.payments.handle_event({"id": event_id, "type": "payment.succeeded",
                                                "order_id": order["id"], "amount_cents": amount}, now=now)

    def test_duplicate_webhook_is_idempotent_and_overpayment_rejected(self):
        order = self.app.orders.create("a", [("SKU", 1)])
        with self.assertRaises(PaymentError):
            self.payment(order, "too_large", 1001)
        self.assertEqual(self.app.payments.paid_cents(order["id"]), 0)
        self.assertEqual(self.payment(order, "evt", 1000), "paid")
        self.assertEqual(self.payment(order, "evt", 1000), "paid")
        self.assertEqual(self.app.payments.paid_cents(order["id"]), 1000)

    def test_second_distinct_payment_is_recorded_and_reported_as_overpaid(self):
        order = self.app.orders.create("a", [("SKU", 1)])
        self.assertEqual(self.payment(order, "evt1", 1000), "paid")
        self.assertEqual(self.payment(order, "evt2", 1000), "overpaid")
        self.assertEqual(self.app.payments.paid_cents(order["id"]), 2000)

    def test_abandoned_checkout_cancel_releases_stock(self):
        order = self.app.orders.create("a", [("SKU", 3)])
        self.app.orders.cancel(order["id"])
        self.assertEqual(self.app.catalog.get_product("SKU").stock, 5)

    def test_coupon_reduces_taxable_amount(self):
        order = self.app.orders.create("a", [("SKU", 1)], region="CA", coupon_code="TEN")
        self.assertEqual(order["discount_cents"], 100)
        self.assertEqual(order["tax_cents"], 65)
        self.assertEqual(order["total_cents"], 965)

    def test_daily_report_uses_shop_local_offset(self):
        order = self.app.orders.create("a", [("SKU", 1)])
        utc = datetime(2025, 3, 9, 20, 0, tzinfo=timezone.utc)  # Mar 10 at 01:30 in India
        self.payment(order, "india", 1000, utc)
        self.assertEqual(reports.daily_sales(self.conn, "2025-03-10", 330)["revenue_cents"], 1000)
        self.assertEqual(reports.daily_sales(self.conn, "2025-03-09", 330)["revenue_cents"], 0)

    def test_competing_workers_cannot_oversell(self):
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        c1 = db.connect(path)
        c2 = db.connect(path)
        app1, app2 = App(c1), App(c2)
        app1.catalog.add_product("ONE", "One", 100, stock=1)
        # Prime the second worker's stale cache before the first reserves stock.
        app2.catalog.get_product("ONE")
        app1.orders.create("first", [("ONE", 1)])
        with self.assertRaises(OutOfStock):
            app2.orders.create("second", [("ONE", 1)])
        self.assertEqual(c1.execute("SELECT stock FROM products WHERE sku='ONE'").fetchone()[0], 0)
        c1.close(); c2.close(); os.unlink(path)


if __name__ == "__main__":
    unittest.main()


