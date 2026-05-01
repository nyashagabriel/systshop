Render deployment — Official guide

Prerequisites
- A Render account and GitHub repo connected.
- This repo contains `Procfile` with:

  web: gunicorn sys_shop.wsgi:application

Recommended Build & Start (Render service settings)
- Build command:

  pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate && python manage.py seed_user

- Start command:

  gunicorn sys_shop.wsgi:application

Environment variables (set in Render → Service → Environment)
- SECRET_KEY — a secure random string.
- DEBUG — `False` for production.
- DATABASE_URL — Render Postgres connection string (create a Postgres DB in Render and attach it to the service).
- ALLOWED_HOSTS — your Render domain (e.g. `systshop.onrender.com`) or `.onrender.com` to allow Render subdomains.

Notes & verification
- The project auto-falls back to SQLite locally when `DATABASE_URL` is not present.
- `STATIC_ROOT` is `staticfiles/`; `collectstatic` will populate this directory.
- Use the provided management command to create an admin user on deploy: `python manage.py seed_user` (build command above runs it).

Troubleshooting
- 400 (Bad Request): ensure `ALLOWED_HOSTS` includes the site domain.
- 405 on `/logout/`: templates in this repo submit logout via POST with CSRF token; ensure templates were redeployed.
- If Procfile is ignored by Render, set the Start Command explicitly in the Render dashboard to `gunicorn sys_shop.wsgi:application`.

Security
- Do NOT commit `SECRET_KEY` into the repo. Use Render's environment variables to store secrets.
- Set `DEBUG=False` in production.

Optional: create a Render health check
- Add a health check path (e.g. `/`) in the Render service settings to let Render detect unhealthy instances.

If you'd like, I can also:
- Add a GitHub Actions workflow to automatically deploy to Render.
- Add a small `docs/deploy.md` with screenshots for the Render dashboard.
