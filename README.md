# SystShop

Minimal Django inventory app.

## Local setup

1. Create and activate the virtual environment.
2. Install dependencies from `requirements.txt`.
3. Run `python3 manage.py migrate`.
4. Start the app with `python3 manage.py runserver`.

## Render deployment

Use these settings on Render:

- Build command: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
- Start command: `gunicorn sys_shop.wsgi:application`
- Environment variables:
  - `SECRET_KEY`: your Django secret key
  - `DEBUG`: `False`
  - `DATABASE_URL`: the Render Postgres connection string
  - `ALLOWED_HOSTS`: your Render app domain, or `.onrender.com` if you want to cover the generated subdomain

This project uses WhiteNoise with `STATIC_ROOT = staticfiles/`.

- Run `python manage.py collectstatic` before deploying.
- The `staticfiles/` directory is generated and ignored by Git, so it may need to be created or populated in fresh environments.