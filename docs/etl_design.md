# ETL Design

Flow: SIMKOPDES source tables read-only -> ETL refresh jobs -> `group9_*` summary tables -> dashboard API.

Two DB mode:

```env
SOURCE_DATABASE_URL=postgresql://readonly_user:password@host:5432/source_db
DASHBOARD_DATABASE_URL=postgresql://writable_user:password@host:5432/dashboard_db
TABLE_PREFIX=group9_
```

If these are empty, backend falls back to existing `DATABASE_URL` or `DB_*` settings for both source and dashboard DB.

No writable Postgres mode:

```env
SOURCE_DATABASE_URL=postgresql://readonly_user:password@host:5432/source_db
DASHBOARD_SQLITE_PATH=data_backup/dashboard.db
TABLE_PREFIX=group9_
```

In this mode ETL writes summary tables into local SQLite file `data_backup/dashboard.db`. Dashboard API reads that file.

Run all jobs:

```bash
python -m app.etl.jobs.refresh_all --period 2026-07
```

Run one job:

```bash
python -m app.etl.jobs.refresh_regional_monthly_metrics --period 2026-07
```

No NIK, KTP, HP, email, address, rekening, raw file, foto, or personal member rows are copied.
