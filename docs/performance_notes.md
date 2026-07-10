# Performance Notes

Dashboard request path now reads `group9_*` summary tables by default.

Before: dashboard services queried raw SIMKOPDES tables and repeated joins per request.

After: ETL precomputes koperasi, product, RAT, gerai, village, and regional summaries. API applies indexed filters on `koperasi_ref`, `period_month`, `kode_wilayah`, `scope_level`, and `scope_code`.

For read-only SIMKOPDES credentials, use `SOURCE_DATABASE_URL` for source reads and `DASHBOARD_DATABASE_URL` for writable summary tables.

If no writable Postgres exists, leave `DASHBOARD_DATABASE_URL` empty and use `DASHBOARD_SQLITE_PATH=data_backup/dashboard.db`.

Slow fallback to raw joins stays disabled unless `ENABLE_SLOW_FALLBACK=true`; current implementation returns empty dashboard contract with warning instead.

Development slow query check:

```sql
EXPLAIN ANALYZE
SELECT *
FROM group9_regional_monthly_metrics
WHERE scope_level = 'desa'
  AND scope_code = '...'
  AND period_month = '2026-07';
```
