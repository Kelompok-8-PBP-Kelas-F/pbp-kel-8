# Local Development Setup

## Prerequisites
- Python 3.x
- SQLite3 CLI (optional, see alternatives below)

## Steps

### 1. Clone & install dependencies
```bash
git clone <repo-url>
cd thriftio
python -m venv env
env\Scripts\activate        # Windows
# source env/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

### 2. Fix migration inconsistency (required for all new contributors)

The project uses `core/migrations/0000_create_schema.py` which runs a PostgreSQL-only
`CREATE SCHEMA` command. This fails silently on SQLite, causing an inconsistency error
when running migrations.

**If `db.sqlite3` already exists** (e.g. pulled from repo or ran something before):

Option A — using SQLite CLI:
```bash
sqlite3 db.sqlite3 "INSERT INTO django_migrations (app, name, applied) VALUES ('core', '0000_create_schema', datetime('now'));"
```

Option B — using Python (if `sqlite3` CLI is not installed):
```bash
python -c "import sqlite3; conn = sqlite3.connect('db.sqlite3'); conn.execute(\"INSERT INTO django_migrations (app, name, applied) VALUES ('core', '0000_create_schema', datetime('now'))\"); conn.commit(); conn.close()"
```

**If `db.sqlite3` does not exist yet** (fresh setup):
```bash
python manage.py migrate core 0000_create_schema --fake
```

### 3. Run migrations
```bash
python manage.py migrate
```

### 4. Create a superuser (for Django admin access)
```bash
python manage.py createsuperuser
```

### 5. Run the development server
```bash
python manage.py runserver
```

The app will be available at `http://127.0.0.1:8000`.
Django admin is at `http://127.0.0.1:8000/admin`.

## Environment Variables

Create a `.env` file at the project root. For local development, only this is required:

```
PRODUCTION=False
```

For the news module to work locally, also add:
```
NEWS_API_KEY=your_api_key_here
```

## Notes
- Local development uses SQLite — no database setup needed.
- Uploaded media files (item images, etc.) are stored in the `media/` folder locally.
- `PRODUCTION=True` switches to PostgreSQL and requires additional DB env vars.