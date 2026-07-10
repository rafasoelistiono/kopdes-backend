# Frontend API Guide

Base URL local:

```text
http://localhost:8000
```

All API routes use prefix:

```text
/api/v1
```

Dashboard APIs read precomputed summary data from `group9_*` tables stored in `data_backup/dashboard.db`. Frontend does not need to aggregate raw SIMKOPDES data.

## Health

```http
GET /health
```

Response:

```json
{
  "success": true,
  "status": "ok"
}
```

## Valid Dashboards

Only these dashboards exist:

- `pengurus-koperasi`
- `kepala-desa`
- `satgas-kdmp`

Removed dashboards return `404`:

- `operator-koperasi`
- `bank-reviewer`

## Common Dashboard Response

Every dashboard returns same top-level shape:

```json
{
  "success": true,
  "dashboard_key": "pengurus-koperasi",
  "dashboard_title": "Cooperative Performance & Finance",
  "role": "pengurus_koperasi",
  "scope": {
    "koperasi_ref": "KOP-0008016CB39E",
    "kode_wilayah": null,
    "scope_level": null,
    "scope_code": null
  },
  "filters": {
    "period": "2026-07",
    "year": null,
    "month": null,
    "limit": null
  },
  "kpis": [],
  "sections": [],
  "charts": [],
  "tables": [],
  "metadata": {
    "source_mode": "summary_tables",
    "source_tables": [],
    "summary_tables": ["group9_koperasi_snapshot"],
    "generated_at": "2026-07-10T13:33:04Z",
    "data_freshness": {
      "last_etl_at": "2026-07-10T13:33:04Z",
      "is_stale": false,
      "stale_after_minutes": 15
    },
    "warnings": []
  }
}
```

Frontend should render even when `metadata.data_freshness.is_stale=true`. Show warning badge, do not block page.

## KPI Object

```json
{
  "key": "omzet_bulan_ini",
  "label": "Omzet Bulan Ini",
  "value": 67000000,
  "formatted_value": "Rp67.000.000",
  "unit": "currency",
  "trend": {
    "direction": "up",
    "percentage": 12.5,
    "label": "12.5% dari bulan lalu"
  },
  "status": "success"
}
```

Known `unit` values:

- `number`
- `currency`
- `percent`

Known `status` values:

- `success`
- `warning`
- `danger`
- `neutral`

## Chart Object

```json
{
  "key": "omzet_trend",
  "title": "Tren Omzet",
  "type": "line",
  "x_key": "period",
  "y_key": "value",
  "data": [
    {"period": "2026-07", "value": 56201961}
  ]
}
```

Known `type` values:

- `line`
- `bar`
- `donut`
- `gauge`

## Table Object

```json
{
  "key": "priority_koperasi_table",
  "title": "Prioritas Koperasi",
  "columns": [
    {"key": "koperasi_ref", "label": "Ref"},
    {"key": "nama_koperasi", "label": "Koperasi"}
  ],
  "rows": [
    {"koperasi_ref": "KOP-001", "nama_koperasi": "Koperasi Desa"}
  ]
}
```

Use `columns[].key` to read each row value.

## Pengurus Koperasi Dashboard

```http
GET /api/v1/dashboards/pengurus-koperasi?koperasi_ref=KOP-0008016CB39E&period=2026-07&limit=20
```

Required query:

- `koperasi_ref`

Optional query:

- `period`, default `2026-07`
- `limit`, default `20`, max `100`

Sections:

- `business_performance`
- `product_performance`
- `inventory_optimization`
- `savings_liquidity`
- `capital_summary`
- `rat_compliance`
- `financing_summary`
- `gerai_asset_summary`
- `village_potential`

Important KPI keys:

- `omzet_bulan_ini`
- `omzet_bulan_lalu`
- `growth_omzet_bulanan`
- `jumlah_transaksi`
- `average_transaction_value`
- `produk_terlaris`
- `produk_tidak_bergerak`
- `nilai_stok_tertahan`
- `total_simpanan`
- `rasio_simpanan_terbayar`
- `total_modal`
- `status_rat_terakhir`
- `status_pengajuan_pembiayaan_terakhir`
- `dokumen_wajib_lengkap`
- `gerai_status`
- `potensi_desa_utama`

Important table keys:

- `top_products`
- `slow_moving_products`
- `rat_compliance`

## Kepala Desa Dashboard

```http
GET /api/v1/dashboards/kepala-desa?kode_wilayah=36.72.06.1001&period=2026-07&limit=20
```

Required query:

- `kode_wilayah`

Optional query:

- `period`, default `2026-07`
- `limit`, default `20`, max `100`

Sections:

- `village_profile`
- `koperasi_coverage`
- `compliance_summary`
- `economic_activity`
- `gerai_readiness`
- `asset_progress`
- `village_potential`
- `financing_risk_summary`
- `koperasi_health_table`

Important KPI keys:

- `total_koperasi_desa`
- `koperasi_aktif`
- `total_anggota_agregat`
- `rasio_anggota_terhadap_penduduk`
- `total_nilai_transaksi_desa`
- `koperasi_sudah_rat`
- `koperasi_belum_rat`
- `gerai_aktif`
- `gerai_belum_aktif`
- `gerai_akses_listrik`
- `gerai_akses_internet`
- `pembangunan_100_persen`
- `potensi_komoditas_utama`

Important table keys:

- `koperasi_health_table`
- `village_potential`

## Satgas KDMP Dashboard

```http
GET /api/v1/dashboards/satgas-kdmp?period=2026-07&limit=20
```

Optional query:

- `period`, default `2026-07`
- `year`
- `month`
- `provinsi`
- `kab_kota`
- `kecamatan`
- `kode_wilayah`
- `scope_level`
- `scope_code`
- `limit`, default `20`, max `100`

Scope examples:

```http
GET /api/v1/dashboards/satgas-kdmp?scope_level=nasional&scope_code=nasional&period=2026-07
GET /api/v1/dashboards/satgas-kdmp?provinsi=BANTEN&period=2026-07
GET /api/v1/dashboards/satgas-kdmp?kode_wilayah=36.72.06.1001&period=2026-07
```

Sections:

- `regional_coverage`
- `account_legality_summary`
- `economic_impact`
- `rat_activity`
- `savings_summary`
- `gerai_readiness`
- `asset_development`
- `financing_summary`
- `partnership_summary`
- `priority_region_table`
- `priority_koperasi_table`

Important KPI keys:

- `total_koperasi`
- `koperasi_memiliki_nib`
- `koperasi_memiliki_npwp`
- `total_simpanan`
- `simpanan_paid_ratio`
- `volume_transaksi`
- `nilai_transaksi`
- `total_rat`
- `rat_draft`
- `rat_terverifikasi`
- `belum_rat`
- `total_gerai`
- `gerai_aktif`
- `gerai_belum_aktif`
- `pembangunan_belum_mulai`
- `pembangunan_berjalan`
- `pembangunan_100_persen`
- `total_pengajuan_pembiayaan`
- `total_nominal_pembiayaan`
- `kemitraan_diajukan`
- `wilayah_prioritas_pembinaan`

Important table keys:

- `priority_region_table`
- `priority_koperasi_table`

## Lookups

### Wilayah

```http
GET /api/v1/lookups/wilayah
GET /api/v1/lookups/wilayah?provinsi=BANTEN
GET /api/v1/lookups/wilayah?provinsi=BANTEN&kab_kota=KOTA%20CILEGON
```

Response:

```json
{
  "success": true,
  "data": [
    {
      "kode_wilayah": "36.72.06.1001",
      "provinsi": "BANTEN",
      "kab_kota": "KOTA CILEGON",
      "kecamatan": "Gerogol",
      "desa_kelurahan": "Kotasari"
    }
  ]
}
```

### Koperasi

```http
GET /api/v1/lookups/koperasi
GET /api/v1/lookups/koperasi?provinsi=BANTEN
```

Response:

```json
{
  "success": true,
  "data": [
    {
      "koperasi_ref": "KOP-0008016CB39E",
      "nama_koperasi": "KOPERASI KELURAHAN MERAH PUTIH LESTARI KOTASARI BUKIT"
    }
  ]
}
```

### Periods

```http
GET /api/v1/lookups/periods
```

Response:

```json
{
  "success": true,
  "data": [
    {"period": "2026-07", "year": 2026, "month": 7}
  ]
}
```

## ETL Status

```http
GET /api/v1/etl/status
```

Use this for admin/debug screen only.

Manual refresh:

```http
POST /api/v1/etl/refresh-all?period=2026-07
POST /api/v1/etl/refresh?job=regional_monthly_metrics&period=2026-07
```

Known jobs:

- `koperasi_snapshot`
- `koperasi_monthly_metrics`
- `product_monthly_metrics`
- `rat_compliance`
- `gerai_asset`
- `village_potential`
- `regional_monthly_metrics`
- `ui_screens`

Refresh screenshot backup data:

```http
POST /api/v1/etl/refresh?job=ui_screens
```

CLI equivalent:

```bash
python3 -m app.etl.jobs.refresh_ui_screens
```

## UI Screenshot Backup APIs

These endpoints read extracted safe backup tables in `data_backup/dashboard.db`.

Available screens:

- `potensi_desa`
- `pengurus`
- `kbli`
- `modal`
- `simpanan`
- `pinjaman`
- `penjualan`

### Scope Candidates

Use this to find koperasi candidates that best match screenshot counts.

```http
GET /api/v1/ui-screens/scope-candidates/list?limit=20
```

Response:

```json
{
  "success": true,
  "data": [
    {
      "koperasi_ref": "KOP-8F17A99DB403",
      "nama_koperasi": "KOPERASI DESA MERAH PUTIH SUMBER MANDIRI BELUMBANG",
      "kode_wilayah": "51.02.04.2004",
      "potensi_count": 8,
      "pengurus_count": 8,
      "pengurus_pengurus_count": 5,
      "pengurus_pengawas_count": 3,
      "kbli_count": 27,
      "modal_count": 0,
      "simpanan_count": 175,
      "pinjaman_count": 0,
      "match_score": 5
    }
  ]
}
```

### Potensi Desa

```http
GET /api/v1/ui-screens/potensi_desa?kode_wilayah=51.02.04.2004&limit=20
GET /api/v1/ui-screens/potensi_desa?koperasi_ref=KOP-8F17A99DB403&limit=20
```

Rows include:

- `komoditas_ref`
- `kode_wilayah`
- `koperasi_ref`
- `nama_koperasi`
- `provinsi`
- `kab_kota`
- `kecamatan`
- `desa_kelurahan`
- `total_penduduk`
- `penduduk_laki_laki`
- `penduduk_perempuan`
- `anggaran_dana_desa`
- `nama_komoditas`
- `luas_area`
- `volume`
- `jumlah_sdm_terlibat`
- `nilai_potensi_desa`

### Pengurus

```http
GET /api/v1/ui-screens/pengurus?koperasi_ref=KOP-8F17A99DB403&limit=20
```

Rows include masked personal data only:

- `pengurus_ref`
- `koperasi_ref`
- `nama_masked`
- `jabatan`
- `status`
- `no_hp_masked`

Raw `nik`, `email`, `alamat`, `foto`, and `file_ktp` are not copied.

### KBLI

```http
GET /api/v1/ui-screens/kbli?koperasi_ref=KOP-8F17A99DB403&limit=100
```

Rows include:

- `metric_ref`
- `koperasi_ref`
- `kode_kbli`
- `nama_kbli`
- `tipe_izin_usaha`
- `tahun_kbli`

### Modal

```http
GET /api/v1/ui-screens/modal?koperasi_ref=KOP-B6E872120528&limit=20
```

Rows include:

- `modal_ref`
- `koperasi_ref`
- `nomor_perjanjian`
- `tipe_sumber`
- `nama_sumber`
- `tipe_modal`
- `jumlah`
- `tanggal_diterima`

`file_perjanjian` is not copied.

### Simpanan

```http
GET /api/v1/ui-screens/simpanan?koperasi_ref=KOP-8F17A99DB403&limit=50
```

Rows are aggregate rows from member-payment data:

- `metric_ref`
- `koperasi_ref`
- `periode_pembayaran`
- `status`
- `row_count`
- `total_pembayaran`
- `paid_count`
- `unpaid_count`

Raw `anggota_ref` is not copied.

### Pinjaman

```http
GET /api/v1/ui-screens/pinjaman?koperasi_ref=KOP-81F1971705B8&limit=20
```

Rows include safe pembiayaan fields:

- `pengajuan_pembiayaan_ref`
- `koperasi_ref`
- `status_permohonan`
- `nominal_permohonan`
- `tenor`
- `tujuan_permohonan`
- `dibuat_pada`

Raw `nik`, `penanggung_jawab`, phone, and form file are not copied.

### Penjualan

```http
GET /api/v1/ui-screens/penjualan?koperasi_ref=KOP-0008016CB39E&period=2026-07&limit=50
```

Rows include safe sales fields:

- `transaksi_sample_id`
- `koperasi_ref`
- `tanggal_dibuat`
- `period_month`
- `total_pembayaran`
- `status_transaksi`
- `metode_pembayaran`
- `total_item`
- `total_volume`
- `produk_ringkas`

`nama_pelanggan` is not copied.

`produk_ringkas` is an array:

```json
[
  {
    "produk_sample_id": "PRD-001",
    "nama_produk": "Beras",
    "jumlah_keluar": 2,
    "harga": 15000,
    "total_nilai": 30000,
    "status": "SOLD"
  }
]
```

## Frontend Fetch Example

```ts
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function getPengurusDashboard(koperasiRef: string, period = "2026-07") {
  const params = new URLSearchParams({ koperasi_ref: koperasiRef, period });
  const res = await fetch(`${API_BASE}/api/v1/dashboards/pengurus-koperasi?${params}`);
  if (!res.ok) throw new Error(`Dashboard API failed: ${res.status}`);
  return res.json();
}
```

KPI helper:

```ts
export function getKpi(payload: any, key: string) {
  return payload.kpis?.find((item: any) => item.key === key);
}
```

Table helper:

```ts
export function getTable(payload: any, key: string) {
  return payload.tables?.find((item: any) => item.key === key);
}
```

Chart helper:

```ts
export function getChart(payload: any, key: string) {
  return payload.charts?.find((item: any) => item.key === key);
}
```

## Error Handling

Missing required scope returns `400`:

```json
{
  "detail": "pengurus_koperasi requires koperasi_ref"
}
```

Unknown dashboard returns `404`:

```json
{
  "detail": "Unknown dashboard: operator-koperasi"
}
```

Empty summary data still returns `success=true` with warning in `metadata.warnings`. Frontend should show empty state, not crash.
