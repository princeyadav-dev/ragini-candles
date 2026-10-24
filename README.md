# Ragini Candles — complete starter storefront

A plain HTML/CSS/vanilla JavaScript storefront with a Flask API, shared database-backed product catalogue, protected admin routes, WhatsApp order-enquiry flow, and optional Groq-powered assistant.

> **Before launch:** this project is a functional starter, not a deployed or pre-configured business. The WhatsApp number, Groq key, admin password, production database, and hosting accounts must be supplied by you. Delivery and return policies are intentionally not invented. Sample product copy and stock are demo data.

## Project map

- `frontend/` — static pages and assets; this is the only directory Netlify should publish.
- `backend/app.py` — Flask API, admin login, CSRF checks, catalogue CRUD, chatbot endpoint.
- `backend/requirements.txt` — Python dependencies.
- `.env.example` — safe placeholders, no secrets.
- `netlify.toml`, `render.yaml` — deployment configuration.

## 1. Extract and open in VS Code (Windows)

1. Extract `ragini-candles.zip` to a folder such as `C:\Projects\ragini-candles`.
2. Open VS Code → **File → Open Folder…** → select the extracted `ragini-candles` folder (the one containing `frontend`, `backend`, and `README.md`).
3. Install Python 3.11 or 3.12 if needed. In the VS Code terminal, run `py --version`.

## 2. Set up the backend

Open PowerShell in the project root:

```powershell
py -m venv .venv
py -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
Copy-Item .env.example backend\.env
```

Open `backend\.env` and set:
- `FLASK_SECRET_KEY`: a long random secret. Generate one with `py -c "import secrets; print(secrets.token_hex(32))"`.
- `ADMIN_EMAIL`: the email used to sign in at `/admin.html`.
- `ADMIN_PASSWORD`: a strong, unique password. Never commit it or share it in chat. For a production deployment use a secret environment variable in the hosting dashboard.
- `GROQ_API_KEY`: your own Groq API key, if you want AI replies. Leave blank to show a safe unavailable message.
- `GROQ_MODEL`: configurable model name; default is `llama-3.3-70b-versatile`. Model availability and rate limits depend on your Groq account.
- `FRONTEND_ORIGIN`: default local frontend origins shown in the example.
- `DATABASE_URL`: blank uses local SQLite for development. For production set it to a managed PostgreSQL connection URL.
- `COOKIE_SECURE=false` locally. Set `true` on HTTPS hosting.

You can also create a password hash rather than storing `ADMIN_PASSWORD` as plain environment configuration. Generate a Werkzeug hash using the backend virtualenv:

```powershell
.\.venv\Scripts\python.exe -c "from werkzeug.security import generate_password_hash; print(generate_password_hash(input('Password to hash: ')))"
```

Set the output as `ADMIN_PASSWORD_HASH` and leave `ADMIN_PASSWORD` blank. Keep the hash private too. The app accepts either configuration.

## 3. Configure WhatsApp

Open `frontend/js/config.js`. Set:

```js
WHATSAPP_NUMBER: "91YOURNUMBER",
```

Use the real business number with international country code, digits only—no plus sign, spaces, or dashes. Do not leave a fake/blank `wa.me` link. This same value is used for the contact link and cart order enquiry. The chatbot explains that WhatsApp contact is unavailable until configured; it does not invent a number.

## 4. Run locally

Start the Flask backend from the project root (this does not require activating the venv):

```powershell
.\.venv\Scripts\python.exe -m flask --app backend.app run --host 127.0.0.1 --port 5000
```

In a second VS Code terminal, serve the frontend using Python's static server:

```powershell
py -m http.server 5500 --directory frontend
```

Open `http://127.0.0.1:5500/` in your browser. Do not open the HTML with `file://`; browsers restrict API calls from file URLs.

- Shop: `http://127.0.0.1:5500/shop.html`
- Cart: `http://127.0.0.1:5500/cart.html`
- Admin: `http://127.0.0.1:5500/admin.html`
- API health: `http://127.0.0.1:5000/api/health`

Local development uses SQLite at `backend/local-dev.db` and seeds Vanilla Glow Candle (₹299) and Golden Rose Candle (₹399) on first startup. This database file is ignored by Git. Admin changes update this shared local database and are visible to every browser using this backend.

## 5. Test the features

1. Open the homepage and shop. The two seeded sample products should appear.
2. Add a product to the bag; refresh and verify the bag count and contents persist.
3. Change quantity or remove an item on the cart page.
4. Set a WhatsApp number in `frontend/js/config.js`, then submit the cart enquiry. WhatsApp opens with an enquiry; this does **not** place or confirm an order.
5. Open `admin.html`, sign in with `ADMIN_EMAIL` and the configured password. Add/edit/delete a product, then refresh the shop to confirm the shared catalogue changed.
6. Add `GROQ_API_KEY` in `backend/.env`, restart Flask, and send a question in the floating chat. Without a key the endpoint intentionally returns a helpful configuration error.
7. Check the health route. It reports service health only and never reveals secrets.

## 6. Frontend-to-backend URL

All browser API requests use one setting: `frontend/js/config.js` → `API_BASE_URL`.

- Local, same machine setup: leave `API_BASE_URL: ""` (the API URL is relative, so the local server must proxy it in a production-like setup). For the simple local two-port setup above, set it to `http://127.0.0.1:5000` because the frontend is served on port 5500. This is the recommended local setting.
- Netlify + Render: set it to your Render API base URL, e.g. `https://YOUR-SERVICE.onrender.com` (no trailing slash). This is a public API base URL, not a secret.
- On the backend set `FRONTEND_ORIGIN` to the exact frontend origin, e.g. `https://YOUR-SITE.netlify.app` (no trailing slash). For local use `http://127.0.0.1:5500,http://localhost:5500`.
- The admin session uses secure cookies on HTTPS. Cross-site cookies require `COOKIE_SECURE=true`, and browser privacy settings may still block third-party cookies depending on host/domain configuration. If the browser blocks the session cookie, use a same-site custom domain/reverse proxy or a hosting arrangement that keeps frontend and API under the same site.

## 7. Production database setup (important)

Local SQLite is for development only. A deployment filesystem may be temporary, so **do not rely on it for production catalogue persistence**.

1. Create a managed PostgreSQL database with a provider you choose (for example, Supabase Database or another managed PostgreSQL service).
2. In its database/connect settings, copy the PostgreSQL connection string. Keep it private.
3. In the backend host environment settings, add `DATABASE_URL` with that connection string. The app supports PostgreSQL via `psycopg`.
4. Redeploy. The app creates the `products` table and seeds the two demo products only when the table is empty.
5. For a database with network restrictions, configure allowed network access as required by your provider. Use SSL-required connection strings when the provider specifies them.

Do not use a local `.env` file in the frontend. Database credentials belong only in the backend host settings.

## 8. Free-tier deployment overview

Free plans and limits change; availability, sleeping, quotas, card/identity verification, and database retention must be checked on the provider's current pricing pages before relying on them. No provider or AI quota is guaranteed permanently free.

### Deploy the backend to Render

1. Push this project to a private or public Git repository **without any `.env` file**.
2. Create a Render Web Service from that repository. `render.yaml` points at `backend/`, installs `requirements.txt`, starts Gunicorn, and uses `/api/health` as the health check.
3. Add environment variables in Render: `ADMIN_EMAIL`, `ADMIN_PASSWORD` (or `ADMIN_PASSWORD_HASH`), `GROQ_API_KEY`, `FRONTEND_ORIGIN`, and `DATABASE_URL`. `FLASK_SECRET_KEY` is generated by the blueprint. Set `COOKIE_SECURE=true`.
4. Set `FRONTEND_ORIGIN` to your exact deployed Netlify origin. Redeploy after adding variables.
5. Open `https://YOUR-SERVICE.onrender.com/api/health`; expect `{"service":"ragini-candles-api","status":"ok"}`.

### Deploy the frontend to Netlify

1. Create a Netlify site from the same repository.
2. Set the publish directory to `frontend` (the included `netlify.toml` already does this).
3. Edit `frontend/js/config.js` and set `API_BASE_URL` to the Render service URL. Set `WHATSAPP_NUMBER` to the business number.
4. Set `FRONTEND_ORIGIN` on Render to the final Netlify URL, save, and redeploy the backend.
5. Redeploy Netlify so the new public API URL is published. Confirm the browser's network tab shows successful requests to `/api/products` and `/api/chat`.

### Accounts and cost notes

You need your own hosting accounts, a managed database account, and your own Groq API key if using AI. Check whether the selected plan requires a payment method, identity checks, usage limits, or a paid tier. A free backend may sleep when idle; the first request can be slow. Free databases can have quotas or retention limitations. No paid theme or frontend framework is used.

## 9. Troubleshooting

- **404:** confirm URL paths and that Render root directory is `backend`; API routes start with `/api/`.
- **CORS error:** make `FRONTEND_ORIGIN` exactly match the browser's origin including `https://`, with no trailing slash. Comma-separate multiple local origins.
- **500:** check backend logs without posting secrets publicly. Verify database connectivity and environment variable names.
- **502 / sleeping service:** wait for the host to wake, check service logs and health route, then retry.
- **Invalid Groq key / 401:** verify `GROQ_API_KEY` in backend settings, then restart/redeploy. Never put the key in `frontend/js/config.js`.
- **Model unavailable / rate limit:** choose a model currently enabled for your Groq account in `GROQ_MODEL`; respect account quotas and retry later.
- **Admin says not configured:** set `ADMIN_EMAIL` and either `ADMIN_PASSWORD` or `ADMIN_PASSWORD_HASH` on the backend.
- **Admin session fails on separate domains:** check HTTPS, `COOKIE_SECURE=true`, exact CORS origin, browser third-party cookie rules, and the browser network tab. Same-site frontend/API hosting is the most reliable cookie arrangement.
- **Products disappear after redeploy:** set a managed PostgreSQL `DATABASE_URL`; local SQLite or an ephemeral host disk is not production persistence.
- **Images do not load:** built-in SVG files are included. If using external image URLs, use a stable HTTPS URL or upload the image to `frontend/images/` and use its relative path.
- **Chat unavailable:** without a Groq key the endpoint returns a clear configuration error. Check backend health, API key, model name and rate limits.

## 10. Security and business setup checklist

- Replace all secrets in the hosting dashboard; never commit `.env`.
- Keep the admin password unique and strong; use HTTPS in production.
- Set the production frontend origin and PostgreSQL URL.
- Configure the WhatsApp business number.
- Review sample product descriptions, stock, images, prices and fragrance attributes before selling.
- Supply actual delivery/return policies and customer support details before launch.
- Testimonials are not fabricated or included as real reviews.
- The WhatsApp checkout is an order enquiry, not payment processing or an order-management system.
