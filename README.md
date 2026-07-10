# KOPDES Backend

Backend API untuk dashboard SIMKOPDES/KOPDES dan asisten KOMI. Service ini menyediakan API dashboard, lookup data, auth sederhana, health check, ETL refresh, dan endpoint KOMI untuk insight/chat/export berbasis data koperasi.

## Tech Stack

- FastAPI
- SQLAlchemy
- PostgreSQL / SQLite dashboard cache
- Heroku-ready via `Procfile`

## Setup Lokal

```bash
cd ~/kopdes/kopdes-backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt pytest ruff
cp .env.example .env
```

Isi `.env` minimal:

```env
SOURCE_DATABASE_URL=postgresql://user:password@host:5432/source_db
DASHBOARD_DATABASE_URL=
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

Jalankan server:

```bash
uvicorn app.main:app --reload
```

URL lokal:

- API root: `http://localhost:8000/`
- Health: `http://localhost:8000/health`
- Docs: `http://localhost:8000/docs`

## Verifikasi

```bash
python3 -m ruff check app tests
python3 -m pytest
```

## ETL

ETL dipakai untuk refresh data dashboard/cache.

```bash
curl -X POST "http://localhost:8000/api/v1/etl/refresh-all"
curl "http://localhost:8000/api/v1/etl/status"
```

Tidak perlu run ETL setelah restart biasa. Run ETL saat database/cache kosong, logic ETL berubah, atau data dashboard belum muncul.

## Deploy Heroku

Set config penting:

```bash
heroku config:set APP_ENV=production APP_DEBUG=false -a kopdes-backend-prod
heroku config:set CORS_ORIGINS="https://komi-kopdes-beta.vercel.app,http://localhost:3000,http://127.0.0.1:3000" -a kopdes-backend-prod
heroku config:set KOMI_OPENROUTER_SITE_URL="https://komi-kopdes-beta.vercel.app" -a kopdes-backend-prod
```

Jika KOMI LLM aktif:

```bash
heroku config:set KOMI_LLM_ENABLED=true -a kopdes-backend-prod
heroku config:set KOMI_LLM_PROVIDER=openrouter -a kopdes-backend-prod
heroku config:set KOMI_OPENROUTER_API_KEY="ISI_API_KEY" -a kopdes-backend-prod
```

Deploy/check:

```bash
git push origin main
heroku logs --tail -a kopdes-backend-prod
curl https://kopdes-backend-prod-70b0b761e530.herokuapp.com/health
```

## Catatan

- Jangan commit `.env`.
- `.env.example` hanya template.
- `DATABASE_URL` biasanya otomatis dari Heroku Postgres.
