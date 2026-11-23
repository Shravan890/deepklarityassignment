# Tillpoint

Tillpoint is a small shop counter app with a browser UI, a Python JSON API, and SQLite storage. It supports product browsing, order checkout, coupons and tax logic, stock reservation, payment webhooks, cancellation, and daily reports. The local version uses a persistent SQLite file. The Vercel version uses SQLite in the function's temporary `/tmp` directory, so it is suitable for a demo/preview only (details below).

## 1. Requirements

- Python 3.10 or later for local use.
- Git for pushing the project to GitHub.
- A Vercel account to deploy a preview.
- No Python packages are required; the app uses the standard library.

## 2. Run locally on Windows PowerShell

Open PowerShell in this project folder:

```powershell
cd "C:\path\to\tillpoint_assignment"
```

Optionally create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Start the local server:

```powershell
python server.py tillpoint.db 8000
```

Leave that PowerShell window open while using the app. Visit <http://127.0.0.1:8000/> in your browser. Stop the server with `Ctrl+C`. The first run creates the SQLite schema. If the database has no products, add the demo mug using:

```powershell
python seed_demo.py tillpoint.db
```

The local API is also available at `/api/products` and `/api/orders`; older direct paths such as `/products` remain available for the assignment API.

## 3. Run the test suite

From the project folder:

```powershell
python -m unittest discover -s tests -v
```

## 4. Push the project to GitHub

Create an empty GitHub repository, then run these commands from the project folder (replace the URL with your repository URL):

```powershell
git add .
git commit -m "Prepare Tillpoint for Vercel"
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin HEAD
```

If a remote is already configured, skip `git remote add origin` and push with `git push`.

## 5. Deploy on Vercel

1. Sign in to Vercel and choose **Add New → Project**.
2. Import the GitHub repository containing this folder.
3. Keep the project root set to this folder (the one containing `vercel.json`).
4. Do not set a build command or output directory. Vercel serves `index.html` and `assets/` as static files and detects `api/index.py` as a Python Function.
5. Click **Deploy**. After deployment, open the assigned `https://...vercel.app/` URL. The `/api/...` requests from the UI are routed by `vercel.json` to the Python function.

There is no PostgreSQL dependency or database URL configuration. The Vercel function creates its SQLite database at `/tmp/tillpoint.db` and adds a demo MUG product when that database has no catalog entries.

### SQLite data on Vercel

Vercel function files are read-only except for temporary `/tmp` storage. That temporary database can be removed when an instance is recycled, and different function instances may have different SQLite files. Therefore the Vercel demo should load and allow checkout, but stock and orders are **not guaranteed to persist** across requests, deployments, or instances. Keep `tillpoint.db` for reliable local persistence. Durable shared order storage requires a persistent database or storage service; this project deliberately remains SQLite-only as requested.

## 6. API routes

| Method | Path | Body |
|---|---|---|
| GET | `/api/products` | List products |
| GET / PUT | `/api/products/<sku>` | PUT: `{"price_cents": 1200}` |
| POST | `/api/orders` | `{"customer", "items": [{"sku", "qty"}], "region", "coupon"}` |
| GET | `/api/orders/<id>` | Get an order |
| POST | `/api/orders/<id>/cancel` | Cancel an eligible order |
| POST | `/api/webhooks/payments` | Payment event JSON |
| GET | `/api/reports/daily/<YYYY-MM-DD>` | Daily report; optional `utc_offset_minutes` query |

Money is stored as integer cents. Timestamps are stored in UTC.

## 7. Project structure

```text
api/index.py          Vercel Python Function adapter (SQLite in /tmp)
assets/app.js          Browser UI behavior
assets/styles.css      Browser UI styling
index.html             Browser counter page
tillpoint/db.py        SQLite schema and time helpers
tillpoint/catalog.py   Products, stock, and read cache
tillpoint/pricing.py   Subtotal, coupons, and tax
tillpoint/orders.py    Create, cancel, ship, and list orders
tillpoint/payments.py  Payment webhook handling
tillpoint/reports.py   Daily sales and top products
tillpoint/api.py       JSON API and route handling
server.py              Local development HTTP server
seed_demo.py           Optional local demo catalog seeder
vercel.json            Static UI and API route configuration
tests/                 Regression test suite
```
