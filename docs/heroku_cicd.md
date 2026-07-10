# Heroku CI/CD Guide

## Architecture

This backend needs two database URLs in production:

- `SOURCE_DATABASE_URL`: read-only SIMKOPDES/KOPI PostgreSQL source.
- `DASHBOARD_DATABASE_URL`: writable dashboard/auth database.

Do not use SQLite on Heroku for production. Heroku dyno filesystem is ephemeral, so `data_backup/dashboard.db` can disappear after restart/redeploy.

## Files Added For Deploy

- `Procfile`: starts FastAPI with Uvicorn on Heroku `$PORT`.
- `.python-version`: pins Python minor version for Heroku and GitHub Actions.
- `requirements.txt`: dependencies Heroku Python buildpack installs.
- `.github/workflows/heroku-deploy.yml`: CI/CD from `main` to Heroku.

## 1. Create Heroku App

```bash
heroku login
heroku create kopdes-backend-prod
heroku stack:set heroku-24 -a kopdes-backend-prod
heroku buildpacks:set heroku/python -a kopdes-backend-prod
```

## 2. Add Dashboard Database

```bash
heroku addons:create heroku-postgresql:essential-0 -a kopdes-backend-prod
```

Use Heroku Postgres as the writable dashboard/auth DB:

```bash
heroku config:set DASHBOARD_DATABASE_URL="$(heroku config:get DATABASE_URL -a kopdes-backend-prod)" -a kopdes-backend-prod
```

## 3. Set Config Vars

```bash
heroku config:set \
  APP_ENV=production \
  APP_DEBUG=false \
  API_PREFIX=/api/v1 \
  TABLE_PREFIX=group9_ \
  DEFAULT_PERIOD=2026-07 \
  ENABLE_ADMIN_ETL_ENDPOINT=false \
  ENABLE_SLOW_FALLBACK=false \
  CORS_ORIGINS=https://your-frontend-domain.com \
  SOURCE_DATABASE_URL='postgresql://readonly_user:password@host:5432/simkopdes?sslmode=require' \
  -a kopdes-backend-prod
```

If source database is also Heroku Postgres, copy its URL into `SOURCE_DATABASE_URL`.

## 4. Setup GitHub Secrets

Repository Settings -> Secrets and variables -> Actions -> New repository secret:

- `HEROKU_API_KEY`: from Heroku Account Settings -> API Key.
- `HEROKU_APP_NAME`: `kopdes-backend-prod`.
- `HEROKU_EMAIL`: your Heroku account email.

## 5. Deploy Via CI/CD

Push to `main`:

```bash
git push origin main
```

GitHub Actions runs:

- install dependencies
- compile-check app code
- deploy to Heroku
- healthcheck `https://<HEROKU_APP_NAME>.herokuapp.com/`

Manual deploy is also available from GitHub Actions -> `CI/CD Heroku` -> Run workflow.

## 6. Initialize Dashboard Data

After first deploy, run ETL once from Heroku:

```bash
heroku run "python -m app.etl.jobs.refresh_all --period 2026-07" -a kopdes-backend-prod
```

Refresh screenshot backup tables if needed:

```bash
heroku run "python -m app.etl.jobs.refresh_ui_screens" -a kopdes-backend-prod
```

## 7. Verify Production

```bash
curl https://kopdes-backend-prod.herokuapp.com/
curl https://kopdes-backend-prod.herokuapp.com/health
curl https://kopdes-backend-prod.herokuapp.com/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"change-me-now","name":"Admin"}'
```

Login:

```bash
curl https://kopdes-backend-prod.herokuapp.com/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"change-me-now"}'
```

Use returned token in frontend:

```text
Authorization: Bearer <token>
```

## Notes

- Full local smoke tests need `data_backup/dashboard.db`, which is gitignored. CI uses compile-check only until a CI-safe fixture DB exists.
- `ENABLE_ADMIN_ETL_ENDPOINT=false` keeps public ETL refresh endpoint off in production. Use `heroku run` for ETL.
- Dashboard endpoints need ETL-created `group9_*` tables before they contain data.
