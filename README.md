# Asset Tracker

A deliberately small employee asset tracker for HR/IT. Single role — the
logged-in admin manages every employee and asset record; there is no
per-employee login and no multi-tenant scoping, since this is one admin's
view of their org. React + Vite + TypeScript frontend, Django REST
Framework backend, PostgreSQL database. No Celery/Redis — there is no
background work to run.

## Data model

- **User** — Django's `AbstractUser` with `email` as `USERNAME_FIELD`. Used
  only for admin login; not linked to Employee records.
- **Employee** — `name`, `email` (unique), `department`, `job_title`,
  `hire_date`, `is_active` (default `True`).
- **Asset** — `asset_tag` (unique), `name`, `category`
  (`laptop`/`monitor`/`phone`/`peripheral`/`other`), `serial_number`
  (optional), `purchase_date` (optional), `is_retired` (manually set by the
  admin). `status` is **derived**, not stored — see below.
- **AssetAssignment** — `asset`, `employee`, `assigned_date`,
  `returned_date` (nullable — null means still assigned), `notes`.

### Derived asset status and its precedence

`Asset.status` is a Python property, computed from `is_retired` and
whether the asset has an open (`returned_date IS NULL`) `AssetAssignment`.
Precedence, highest to lowest:

1. **`retired`** — `is_retired=True`. This wins even over an open
   assignment, representing an asset pulled from service (broken, lost,
   decommissioned) without necessarily having gone through a formal return
   first.
2. **`assigned`** — not retired, and there's an open `AssetAssignment`.
3. **`available`** — neither of the above.

### One open assignment per asset

At most one `AssetAssignment` with `returned_date IS NULL` may exist per
asset at a time. This is enforced two ways:

- A partial unique constraint,
  `UniqueConstraint(fields=["asset"], condition=Q(returned_date__isnull=True))`
  (supported on both PostgreSQL and SQLite) — the ultimate source of truth.
- An application-level check inside `transaction.atomic()` in
  `POST /api/assets/{id}/assign/`, so a violation returns a clean `409`
  instead of a raw `IntegrityError`/500. The `IntegrityError` is still
  caught as a backstop for the race between the check and the insert.

Deleting an `Employee` or `Asset` that has assignment history is blocked
(`on_delete=PROTECT`, surfaced as a `409`) — return/retire instead of
deleting, to keep assignment history intact.

## REST API

- `POST /api/auth/login/` (JWT), `POST /api/auth/refresh/`,
  `POST /api/auth/logout/`, `GET /api/auth/me/`
- `/api/employees/` — list/create/retrieve/update/delete,
  `?department=`, `?is_active=`, `?search=`
- `/api/assets/` — list/create/retrieve/update/delete, `?category=`,
  `?status=` (`available`/`assigned`/`retired`), `?search=`
  - `POST /api/assets/{id}/assign/` — body `{employee_id, assigned_date?, notes?}`.
    409 if the asset is retired or already assigned.
  - `POST /api/assets/{id}/retire/` / `POST /api/assets/{id}/unretire/`
- `/api/assignments/` — list (read-only) + `?asset=`, `?employee=`,
  `?open=true|false`
  - `POST /api/assignments/{id}/return/` — body `{returned_date?}` (defaults
    to today). 400 if already returned or if `returned_date` precedes
    `assigned_date`.
- `GET /api/dashboard/` — asset counts by status and by category,
  employees with their currently-assigned asset counts (based on open
  assignments — a retired-but-still-checked-out asset still counts against
  the employee holding it), and assets that have never been assigned.

## Demo / seed data

A data migration (`apps/assets/migrations/0002_seed_demo_data.py`, `RunPython`)
creates, on first `migrate`:

- One admin user: `admin@example.com` / `demo12345`
- 6 employees across Engineering, Sales, HR and IT (one marked inactive)
- 10 assets across all 5 categories (one marked retired)
- 8 assignment rows — some open, some returned, including a retired asset
  with an open assignment on record (demonstrating the status precedence
  rule) and 2 assets that have never been assigned (underutilized stock,
  surfaced on the dashboard)

Every row is looked up with `get_or_create` on a real unique field
(`User.email`, `Employee.email`, `Asset.asset_tag`, and
`(asset, employee, assigned_date)` for assignments), so re-running
`migrate` — or re-invoking the seed function directly — does not create
duplicates. Covered by `apps/assets/tests/test_seed_data.py`.

## Running locally with Docker (Postgres)

```bash
cp .env.example .env
docker compose up --build
```

Backend on http://localhost:8000, frontend on http://localhost:5173.

## Running the backend without Docker (dev-only SQLite override)

No Postgres/Docker needed for this — same `USE_SQLITE` pattern used by the
sibling apps in this workspace. **Never set `USE_SQLITE=True` in
docker-compose or production.**

```bash
cd backend
python -m venv venv
source venv/Scripts/activate   # Windows Git Bash; use venv\Scripts\activate.bat on cmd
pip install -r requirements.txt

export USE_SQLITE=True
export DJANGO_SETTINGS_MODULE=config.settings.dev

python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py test
python manage.py runserver
```

## Running the frontend

```bash
cd frontend
npm install
npm run dev      # dev server on :5173
npm run build    # production build (tsc -b && vite build)
```

Set `VITE_API_BASE_URL` (see `frontend/.env.example`) if the backend isn't
at `http://localhost:8000/api`.

## What's left for a real Postgres/Docker setup

This was built and verified with `USE_SQLITE=True` only (no Docker/Postgres
available in the build environment). Before relying on the Postgres/Docker
path:

- Run `docker compose up --build` end to end at least once and confirm the
  seed migration applies cleanly against a fresh Postgres volume.
- Double-check the partial unique constraint's generated SQL against
  Postgres (`\d assets_assetassignment` in `psql`) — it's standard
  behaviour in Django but worth a sanity check.
- Review `DJANGO_ALLOWED_HOSTS` / `CORS_ALLOWED_ORIGINS` for the actual
  deployment host(s) before using `config.settings.prod`.
- Rotate `DJANGO_SECRET_KEY` and the demo admin password before any
  non-local use.
