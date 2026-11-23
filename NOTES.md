# NOTES


## 1. Report

> Finance says that on some days the revenue in the daily report is higher than what the payment provider paid out, and a few orders show more money received than their total.

**Status:** fixed

**What the code showed:** `Payments.handle_event` inserted every successful delivery into `payments`. Replaying the same provider event therefore added the same amount again. A first payment larger than the order total was also accepted.

**Root cause:** The payment table did not require unique provider event IDs, and the handler did not check whether a first payment exceeded the amount due.

**Fix and why:** Provider event IDs are unique. A replay for the same order is treated as idempotent, while reuse of that ID for a different order is rejected. An initial payment greater than the order total is rejected. This prevents retries or invalid initial amounts from creating fictitious receipts. A separate genuine payment is handled under section 6.

**How it was verified:** Regression tests were run against the original implementation and failed. After the fix, the tests show that replaying one event leaves the received total unchanged and a too-large first payment is rejected without being recorded. The full suite passes.

**Commits:** c8cfdf9, 90984d9

## 2. Report

> Products show as sold out, or nearly, while the shelf is full. Staff say it gets worse on days when many customers abandon checkout.

**Status:** fixed

**What the code showed:** Orders reserve stock when created. Cancelling a pending order did not restore the reservation; only paid orders were restocked. Each process also used a local product cache when checking available stock.

**Root cause:** Pending cancellations leaked reservations. Separately, the check and decrement were not one database operation, so a worker with a stale cached stock value could authorize a reservation using out-of-date information.

**Fix and why:** Cancelling either a pending or paid order restores its reserved units. Reservation now uses one conditional SQL update that subtracts units only when `stock >= qty`; the order's immediate transaction protects the operation across workers. This puts the stock decision against current database state.

**How it was verified:** Regression tests were run against the original implementation and failed. After the fix, a pending-order cancellation restores stock, and a second app instance with a stale cache cannot reserve the last unit after the first instance has taken it. Persisted stock remains zero rather than going negative. The full suite passes.

**Commits:** c8cfdf9, 26dfef4, 520c341

## 3. Report

> Customers in taxed regions who used a coupon say the tax on their receipt is too high. Receipts without a coupon are right.

**Status:** fixed

**What the code showed:** `price_order` calculated tax from the full subtotal and only then subtracted the coupon discount.

**Root cause:** The calculation used the pre-discount subtotal as the taxable amount.

**Fix and why:** The taxable amount is now `subtotal - discount`; tax is then added to the discounted amount. This applies the coupon before calculating tax.

**How it was verified:** Regression tests were run against the original implementation and failed. The CA test for a $10 item with a 10% coupon checks a $1 discount, 65 cents tax, and a $9.65 total. The full suite passes.

**Commits:** c8cfdf9, 347c224

## 4. Report

> Our shop in India (UTC+5:30) says sales taken in the morning do not appear in that day's report and turn up under the day before.

**Status:** fixed

**What the code showed:** `day_bounds_utc` added a positive local offset to local midnight. India midnight is 18:30 UTC on the preceding date, so the conversion moved the boundary in the wrong direction.

**Root cause:** The offset was added where it needed to be subtracted to convert the shop's local midnight to UTC.

**Fix and why:** The report now subtracts `utc_offset_minutes` when calculating the UTC start of the local day and queries the interval up to, but not including, the next day's start.

**How it was verified:** Regression tests were run against the original implementation and failed. With a +330-minute offset, a payment at 01:30 India time appears on March 10 and not March 9. The full suite passes.

**Commits:** c8cfdf9, d523b9a

## 5. Report

> Ever since we started running two server workers, we have sold more units of an item than we had, and its stock went negative.

**Status:** fixed

**What the code showed:** `Catalog.reserve` read the cached stock, checked it in Python, then ran an unconditional decrement. Separate workers could each make the check using a stale positive value.

**Root cause:** Reading, checking, and decrementing stock were separate steps, with no database condition protecting the decrement.

**Fix and why:** The database now performs the decrement only when enough stock remains, and the reservation is inside `BEGIN IMMEDIATE`. If the conditional update affects no rows, the code reads current stock and raises `OutOfStock`.

**How it was verified:** Regression tests were run against the original implementation and failed. The two-connection test primes a stale cache in the second worker; after the first order reserves the final unit, the second raises `OutOfStock` and stored stock stays at zero. The full suite passes.

**Commits:** c8cfdf9, 26dfef4

## 6. Open question

> Open question from support, no single right answer: sometimes a customer really does pay twice for one order (two separate payments, not a retry of the same one). Today the system records both and says nothing. Decide what should happen, build the smallest version of your decision, and explain what it costs in `NOTES.md`.

**Decision in the implementation (selected by the assistant):** Keep a distinct successful second payment in the ledger and return `overpaid` when the order has received more than its total. A repeated event ID remains idempotent.

**Reason for this choice:** A different provider event ID represents a separate payment event. Recording it preserves the actual received-money history, while `overpaid` makes the condition visible to the caller.

**What it costs:** This implementation does not refund the payment or alert staff. The shop needs an operational process to detect the `overpaid` response and arrange a refund. Until refunded, reports include the distinct payment actually received.

**What was built:** The handler records distinct successful payments and returns `overpaid` when cumulative payments exceed the order total. Replays of the same event do not add another payment.

**How it was verified:** A regression test sends two distinct successful events for one order, checks that the second returns `overpaid`, and confirms both amounts remain in the ledger. A separate test confirms retries with the same event ID are counted once. Another test checks that partial payments which cross the order total still mark the order paid while returning `overpaid`. The full suite passes.

I think the stock issue came from abandoned pending orders keeping reservations and from workers trusting stale cached stock. For payments, a retry of the same provider event should count once, while a different event ID represents a real second charge. I would keep that second charge visible and flag it as `overpaid` so staff can reconcile and refund it. The tradeoff is that the app still needs a refund and alert process.” Use this only if it matches your own view; the user said they had not done the work, so it is not represented here as their answer.

**Commits:** c8cfdf9, 90984d9, a23904a

## Other things noticed

The original brief requested backend fixes and did not ask for a browser UI. In a later request, the user asked for a polished local interface. I added a responsive counter page at `/`, a `GET /products` listing route, and an order cart that submits to the existing `POST /orders` API. The server can also read `HOST` and `PORT` for hosting; its defaults remain local development (`127.0.0.1:8000`). It still uses the single-threaded `HTTPServer`; the reported stock invariant is protected at the database operation and is tested with two app instances. A browser preview from the coding environment could not reach its locally launched server, so the UI should be opened from the user's restarted local server for visual review.

## Session logs

Codex desktop was used. `session_logs/codex_session.md` contains the visible conversation and task tool activity for this work, with personal identifiers redacted and platform instructions omitted. The log records that the user said they had not done the work and asked for candidate reasoning to be invented and presented as theirs. The assistant declined to misattribute its writing and included only a clearly attributed example. A later UI request and the implementation work are also recorded. This log does not claim candidate-authored technical reasoning that was not supplied.
