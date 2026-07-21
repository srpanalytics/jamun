# PromptSphere — Full Working Website

A complete, deployable marketplace web app: buyers browse and purchase AI prompts,
creators publish and get paid, reviews build reputation. Built with:

- **Frontend:** HTML, CSS, vanilla JavaScript (server-rendered pages + fetch-based interactivity)
- **Backend:** Python (Flask)
- **Database:** SQL (SQLite — a single file, zero setup)

---

## 1. Run it locally (2 minutes)

```bash
cd promptsphere
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open **http://localhost:5000** — the database is created and seeded with demo
creators, prompts, and reviews automatically on first run. No manual DB setup needed.

### Demo accounts (password for all: `password123`)
| Email | Role |
|---|---|
| ava@promptsphere.ai | Creator |
| marcus@promptsphere.ai | Creator |
| priya@promptsphere.ai | Creator |
| buyer@promptsphere.ai | Buyer |

Or just click **Sign up free** and create your own account as a buyer or creator.

---

## 2. What's included

- **Marketplace** with live search, category/model filters, and sorting (`/marketplace`)
- **Prompt detail pages** with locked/blurred content until purchased, star ratings, and reviews
- **Auth**: signup, login, logout, hashed passwords (Werkzeug), session-based auth
- **Creator dashboard**: publish/edit/delete prompts, see sales + revenue per prompt
- **Buyer dashboard**: purchase history
- **JSON API** (`/api/prompts`, `/api/prompts/<id>/purchase`, `/api/prompts/<id>/reviews`, `/api/me`)
  used by the frontend JS — this is a clean seam if you later want a mobile app or SPA frontend
- Full SQL schema in `schema.sql` (`users`, `prompts`, `purchases`, `reviews`, with foreign keys and indexes)

### Not included (by design, since this is a demo build)
- **Real payments.** The "Buy now" button completes a purchase instantly in the database — there's
  no actual money movement. Before taking real transactions, integrate a processor such as Stripe
  Checkout or Stripe Payment Intents in the `/api/prompts/<id>/purchase` route in `app.py`.
- **Email verification / password reset.** Add a mail provider (e.g. SendGrid, Postmark) and token-based
  flows if you need this for production.
- **CSRF tokens on forms.** Fine for a demo behind auth; add `flask-wtf` or similar before a public launch.

---

## 3. Project structure

```
promptsphere/
├── app.py                # Flask app: routes, API endpoints, auth
├── seed.py                # Demo data (creators, prompts, reviews)
├── schema.sql              # SQL schema (SQLite)
├── requirements.txt
├── Procfile                # For Render / Railway / Heroku-style platforms
├── static/
│   ├── css/style.css
│   └── js/{main,api,marketplace,prompt-detail}.js
└── templates/
    ├── base.html, index.html, marketplace.html, prompt_detail.html
    ├── login.html, signup.html, dashboard.html, create_prompt.html, 404.html
```

The SQLite file `promptsphere.db` is created next to `app.py` the first time you run the app.
It is gitignored — don't commit it; each environment (local, staging, production) gets its own.

---

## 4. Deploying

### Option A — Render.com (recommended, free tier available)
1. Push this folder to a GitHub repo.
2. On Render: **New → Web Service** → connect the repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Add an environment variable `SECRET_KEY` set to a long random string.
6. Deploy. Render gives you a public URL immediately.

> Note: Render's free tier disks are ephemeral on redeploy. For a persistent SQLite file across
> deploys, attach a Render **Disk** mounted at the project folder, or move to Render's managed
> Postgres for real production use (see Option C below).

### Option B — Railway.app
1. Push to GitHub, then **New Project → Deploy from GitHub repo** on Railway.
2. Railway auto-detects Python; it will use the `Procfile` (`gunicorn app:app`) automatically.
3. Add the `SECRET_KEY` variable under **Variables**.
4. Attach a **Volume** mounted at `/app` if you want the SQLite file to persist across deploys.

### Option C — Any VPS (DigitalOcean, EC2, etc.)
```bash
git clone <your-repo>
cd promptsphere
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
gunicorn --bind 0.0.0.0:8000 app:app
```
Put Nginx in front for TLS/HTTPS, or use Caddy for automatic HTTPS with a domain name.

### Moving from SQLite to Postgres (recommended once you have real users)
SQLite is perfect for launch and for platforms with ephemeral disks, but a single file doesn't
handle concurrent writes at scale. When you outgrow it:
1. Provision a Postgres database (Render, Railway, and most hosts offer one-click Postgres).
2. Replace the `sqlite3` calls in `app.py` with `psycopg2` or SQLAlchemy, and adjust `schema.sql`
   syntax slightly (e.g. `SERIAL` instead of `AUTOINCREMENT`).
3. Everything else (routes, templates, JS) stays the same — only the DB layer changes.

---

## 5. Environment variables

| Variable | Purpose | Required in production? |
|---|---|---|
| `SECRET_KEY` | Signs session cookies | **Yes** — set a long random value |
| `PORT` | Port Flask binds to (used by some hosts) | No — defaults to 5000 |
| `FLASK_DEBUG` | Set to `0` in production | Recommended: `0` |

---

## 6. Resetting the database

To wipe and reseed:
```bash
rm promptsphere.db
python app.py   # recreates + reseeds automatically
```
Or, with the Flask CLI (wipes schema only, no seed data):
```bash
flask --app app init-db
```
