# AHS (Automanager HealthCare Systems)

Minimal README to run the project locally.

## Prerequisites
- Python 3.10+ (use the virtualenv `prohclsenv` included or create a new one)
- MySQL server (if you plan to use MySQL as configured), or change `DATABASES` to use sqlite3

## Quick start (development)

1. Activate virtualenv (PowerShell):

```powershell
prohclsenv\Scripts\Activate.ps1
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create environment variables (optional but recommended). Example `.env` content or set in environment:

```
DJANGO_SECRET_KEY=replace-with-your-secret
DJANGO_DEBUG=True
DB_ENGINE=django.db.backends.mysql
DB_NAME=hclsdb
DB_USER=root
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=3306
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
```

4. Run migrations and start server:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

5. Open in browser:
- App: http://127.0.0.1:8000/
- Swagger: http://127.0.0.1:8000/swagger/
- Redoc: http://127.0.0.1:8000/redoc/

## Notes
- `settings.py` now reads secrets and DB config from environment variables. If none are set, it falls back to development defaults (do not use defaults in production).
- For production, set `DJANGO_DEBUG=False`, configure `DJANGO_ALLOWED_HOSTS`, and provide secure `DJANGO_SECRET_KEY`.
- To use SQLite instead of MySQL for quick testing, edit `HclsPro/HclsPro/settings.py` and set `DATABASES` ENGINE to `django.db.backends.sqlite3` and `NAME` to BASE_DIR / 'db.sqlite3'.

## Recommended next tasks
- Move sensitive values to a secure vault or CI/CD secrets manager.
- Add `requirements.txt` to your environment and pin versions as needed.
- Add unit tests for critical flows (auth, sessions, API endpoints).
