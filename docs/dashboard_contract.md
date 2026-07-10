# Dashboard Contract

All dashboards return:

```json
{
  "success": true,
  "dashboard_key": "pengurus-koperasi",
  "dashboard_title": "Cooperative Performance & Finance",
  "role": "pengurus_koperasi",
  "scope": {},
  "filters": {},
  "kpis": [],
  "sections": [],
  "charts": [],
  "tables": [],
  "metadata": {
    "source_mode": "summary_tables",
    "source_tables": [],
    "summary_tables": [],
    "generated_at": "2026-07-10T10:00:00Z",
    "data_freshness": {
      "last_etl_at": null,
      "is_stale": true,
      "stale_after_minutes": 15
    },
    "warnings": []
  }
}
```

Valid dashboards only:

- `pengurus-koperasi`
- `kepala-desa`
- `satgas-kdmp`
