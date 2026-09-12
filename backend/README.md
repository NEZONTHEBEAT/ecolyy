# ReKart Backend

FastAPI + MongoDB (Motor async driver) backend for ReKart, India's organized
recycling platform. Matches the `frontend/{user,partner,institution,admin}`
structure with one API each.

## Stack
- **FastAPI** — REST API
- **MongoDB Atlas** (via **Motor**, async driver)
- **JWT** (access + refresh tokens) via `python-jose`
- **bcrypt** password hashing via `passlib`
- **Google Sign-In** verification via `google-auth`

## Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then fill in MONGO_URI, SECRET_KEY, GOOGLE_CLIENT_ID
uvicorn app.main:app --reload --port 8000
```

Swagger UI: http://localhost:8000/docs

## How each portal connects

| Frontend page(s)                          | Backend routes                          |
|--------------------------------------------|------------------------------------------|
| `pages/login.html`, `register.html`         | `/api/v1/auth/*`                          |
| `user/*.html`                               | `/api/v1/users/*`, `/api/v1/wallet/*`, `/api/v1/notifications/*`, `/api/v1/pickups/*`, `/api/v1/rewards/*` |
| `partner/*.html`                            | `/api/v1/partners/*`, `/api/v1/pickups/*` |
| `institution/*.html`                        | `/api/v1/institutions/*`                  |
| `admin/*.html`                              | `/api/v1/admin/*`                         |

## How a new customer's data reaches the admin dashboard

There is **one** `pickups` collection in MongoDB — every screen reads/writes
the same documents, so there's no separate "sync" step:

1. Customer registers/logs in via `POST /auth/register` or `/auth/login`
   → gets a JWT with `role: "user"`.
2. Customer books a pickup: `POST /pickups` (uses their saved address,
   waste category, date/slot). This inserts one document into `pickups`
   with `status: "pending"`.
3. **Admin dashboard** (`admin/pickups.html`) calls `GET /admin/pickups`
   (or `/admin/pickups/unassigned`) — same collection, filtered/paginated —
   and can assign a partner via `POST /pickups/{id}/assign`.
4. **Partner dashboard** sees it via `GET /partners/me/pickups`, updates
   status via `PATCH /pickups/{id}/status` (`in_progress` → `completed`
   with `actual_weight_kg`).
5. On `completed`, `pickup_service.update_status()` automatically:
   - credits **points** to the user (`users.points`, via waste-category rate)
   - credits the **wallet** (`wallets` + `wallet_transactions`)
   - updates partner stats (`partners.total_pickups`, `earnings_total`)
   - writes a `notifications` entry for the user
6. `GET /admin/stats` aggregates totals (users, partners, pickups by
   status, total points/wallet paid out) directly from these same
   collections — nothing is duplicated or needs manual syncing.
7. Every admin mutation (verify partner, disable user, add reward, etc.)
   is written to `audit_logs` for accountability — viewable via
   `GET /admin/audit-logs`.

## Admin access lock

Only the email in `SUPER_ADMIN_EMAIL` (`.env`) is ever granted the
`"admin"` role — enforced in `services/auth_service.google_login()` and
checked again on every request by `core/permissions.require_admin`.
Any other Google account hitting the admin sign-in button gets a 403,
and is never silently created as an admin user.

## Folder structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI app, includes app.api.v1.router.api_router
│   ├── core/                   # config, db connection, security, RBAC
│   ├── models/                 # Mongo document shape helpers
│   ├── schemas/                # Pydantic request/response models
│   ├── api/
│   │   └── v1/
│   │       ├── router.py       # aggregates every sub-router into api_router
│   │       ├── auth.py
│   │       ├── users.py        # profile + addresses
│   │       ├── wallet.py
│   │       ├── notifications.py
│   │       ├── pickups.py
│   │       ├── partners.py
│   │       ├── institutions.py
│   │       ├── rewards.py
│   │       └── admin.py
│   ├── services/                # business logic
│   ├── repositories/           # MongoDB data-access layer
│   └── utils/                  # helpers, logger, validators
├── tests/
├── requirements.txt
├── .env.example
└── README.md
```

## Next steps to go fully production-ready

- [ ] Add pagination metadata (total count) to all list endpoints
- [ ] Add rate limiting on `/auth/*` and `/otp/*`
- [ ] Wire a real SMTP/SMS provider in `.env` (email_service.py already supports SMTP; add an SMS provider for phone OTP if needed)
- [ ] Add file upload endpoint for partner documents (`partner/documents.html`) — e.g. S3/Cloudinary
- [ ] Add automated tests in `tests/` (pytest + httpx AsyncClient + mongomock or a test Mongo instance)
- [ ] Deploy: Docker + Render/Railway/Fly.io for the API, MongoDB Atlas for the DB
