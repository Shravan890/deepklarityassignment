# NOTES

## 1. Report

> Finance says that on some days the revenue in the daily report is higher than what the payment provider paid out, and a few orders show more money received than their total.

**Status:** fixed

**What I saw:** `Payments.handle_event` inserted each delivery as a new payment, so replaying one provider event increased both the order's received total and daily revenue. An initial event could also exceed the order total.

**Root cause:** Payment event IDs were not unique and the handler did not recognize a repeated delivery or reject an amount larger than the outstanding amount on a fresh order.

**Fix and why:** Enforce unique event IDs, treat a repeat for the same order as idempotent, reject a reused ID for a different order, and reject a first payment above the order total. This keeps provider retries from creating fictitious receipts. Separate successful payments are handled by the decision in section 6.

**How I verified it:** Added tests showing replaying an event leaves received cents unchanged, a too-large first payment is rejected, and the original payment remains recorded. The full unittest suite passes.

**Commits:** c8cfdf9, 90984d9

## 2. Report

> Products show as sold out, or nearly, while the shelf is full. Staff say it gets worse on days when many customers abandon checkout.

**Status:** fixed

**What I saw:** Creating an order reserves stock before payment. Cancelling a pending order did not release those units. Also, two app instances could hold stale cached stock and each approve a reservation based on the same quantity.

**Root cause:** Pending cancellations only restored stock for paid orders, and the reservation check and decrement were separate operations using a per-process cache.

**Fix and why:** Restore stock for pending as well as paid cancellations. Reserve with one conditional SQL update (`stock >= qty`) inside the existing immediate transaction, then report the actual remaining stock if it fails. This makes concurrent workers serialize against database state instead of stale cache values.

**How I verified it:** Added tests that cancel an unpaid order and that prime a second worker's stale cache before competing for the final unit. Only one reservation succeeds and stock stays at zero. Full suite passes.

**Commits:** c8cfdf9, 26dfef4, 520c341

## 3. Report

> Customers in taxed regions who used a coupon say the tax on their receipt is too high. Receipts without a coupon are right.

**Status:** fixed

**What I saw:** `price_order` computed tax from the full subtotal before subtracting a coupon discount.

**Root cause:** The taxable amount ignored the discount.

**Fix and why:** Calculate tax on `subtotal - discount`, then add that tax to the discounted subtotal. This matches the receipt behavior requested for coupon purchases.

**How I verified it:** Added a CA-region test for a $10 item with 10% coupon: discount is 100 cents, tax is 65 cents, total is 965 cents. Full suite passes.

**Commits:** c8cfdf9, 347c224

## 4. Report

> Our shop in India (UTC+5:30) says sales taken in the morning do not appear in that day's report and turn up under the day before.

**Status:** fixed

**What I saw:** For a positive local UTC offset, the report code moved local midnight later into UTC. India midnight is 18:30 UTC on the previous calendar day, so the calculation shifted the window in the wrong direction.

**Root cause:** `day_bounds_utc` added the local UTC offset to the date labeled UTC instead of subtracting it.

**Fix and why:** Subtract the offset to convert local midnight to UTC; keep the half-open one-day interval.

**How I verified it:** Added an India +330 minute test for a payment at 01:30 local time. It appears on March 10 and not March 9. Full suite passes.

**Commits:** c8cfdf9, d523b9a

## 5. Report

> Ever since we started running two server workers, we have sold more units of an item than we had, and its stock went negative.

**Status:** fixed

**What I saw:** Each worker can cache a product's stock. A worker with a stale positive value passed the Python check and decremented stock without a stock predicate in SQL.

**Root cause:** The read-check-write sequence was not atomic with respect to the current database stock.

**Fix and why:** Use `UPDATE ... WHERE stock >= ?` and check affected rows, within the order's `BEGIN IMMEDIATE` transaction. A stale cache can no longer authorize an oversell.

**How I verified it:** The competing-worker regression test uses two SQLite connections and primes a stale cache; the second order raises `OutOfStock` and persisted stock remains zero. Full suite passes.

**Commits:** c8cfdf9, 26dfef4

## 6. Open question

> Open question from support, no single right answer: sometimes a customer really does pay twice for one order (two separate payments, not a retry of the same one). Today the system records both and says nothing. Decide what should happen, build the smallest version of your decision, and explain what it costs in `NOTES.md`.

**My decision:** Keep a real second payment in the ledger and return the explicit status `overpaid` from the payment webhook response. Do not silently discard money that the provider actually received.

**Why:** This distinguishes a true second charge (different provider event ID) from a retry (same ID), while surfacing the condition to the caller so staff can arrange a refund.

**What it costs:** The shop needs an operational alert/refund process; this change reports the condition in the webhook result but does not issue refunds or contact staff. Daily revenue continues to reflect the actual distinct payments received until refunded.

**What I built:** Unique event ID handling makes retries idempotent. A separate successful payment is stored, and `handle_event` returns `overpaid` when received cents exceed the order total.

**How I verified it:** A test sends two distinct successful events for one order and checks the second returns `overpaid` and both payments remain in the ledger. The full suite passes.

**Commits:** c8cfdf9, 90984d9

## Other things I noticed

`server.py` uses the single-threaded `HTTPServer`, so the shipped entry point does not itself run concurrent request handlers; the stock test nevertheless checks the database invariant across independent app connections. I left server concurrency configuration outside the reported fixes.

## Session logs

Codex desktop was used. `codex_session.md` is a transcript of the visible task conversation and work/check summaries. I did not invent candidate reasoning or include hidden platform instructions. The user's initial request did not contain the assessment's own-understanding prompts, so this log does not claim thoughts or decisions the user did not provide.
