# Single POV Scope Analysis

## Conclusion

```json
{
  "recommended_scope": "koperasi_ref",
  "reason": "Most operational UI tables are scoped by koperasi_ref: pengurus_koperasi, kbli_koperasi, modal_koperasi, simpanan_anggota, pengajuan_pembiayaan.",
  "secondary_scope": "kode_wilayah",
  "used_for": "Potensi Desa, wilayah labels, village profile, and regional dashboard aggregation.",
  "user_uuid_available": false,
  "user_uuid_table": null
}
```

This is not a direct one-person UUID POV in the available source DB. It is best modeled as one koperasi POV.

## Main Scope

Primary scope key:

- `profil_koperasi.koperasi_ref`

Child tables using `koperasi_ref`:

- `pengurus_koperasi`
- `kbli_koperasi`
- `modal_koperasi`
- `simpanan_anggota`
- `pengajuan_pembiayaan`
- `referensi_koperasi_wilayah`

Secondary scope key:

- `referensi_koperasi_wilayah.kode_wilayah`

Tables using `kode_wilayah`:

- `referensi_wilayah`
- `referensi_profil_desa`
- `referensi_komoditas_desa`

Join path:

```text
profil_koperasi.koperasi_ref
-> referensi_koperasi_wilayah.koperasi_ref
-> referensi_koperasi_wilayah.kode_wilayah
-> referensi_wilayah / referensi_profil_desa / referensi_komoditas_desa
```

## User/Manager Mapping

No user/account/manager table was found in the known 27 public tables.

Observed columns do not show a stable `user_uuid`, `manager_id`, or `created_by` scope for these six screens.

Recommended interpretation:

- Logged-in manager identifies auth session outside this DB.
- Backend should authorize user to one or more `koperasi_ref` values.
- Dashboard/filter API should use `koperasi_ref` for operational screens.
- Potensi Desa should use `kode_wilayah`, derived from `koperasi_ref` when needed.

## Recommended Frontend Filters

Use these query keys:

- Pengurus: `koperasi_ref`
- KBLI: `koperasi_ref`
- Modal: `koperasi_ref`
- Simpanan: `koperasi_ref`
- Pinjaman: `koperasi_ref`
- Potensi Desa: `kode_wilayah`, or `koperasi_ref` if backend resolves wilayah

Do not use person UUID as dashboard data scope unless a separate auth/access mapping table is provided.

## Privacy

Sensitive fields found and excluded/masked from backup/API:

- `pengurus_koperasi.no_hp`
- `pengurus_koperasi.nik`
- `pengurus_koperasi.email`
- `pengurus_koperasi.alamat`
- `pengurus_koperasi.foto_profil`
- `pengurus_koperasi.file_ktp`
- `simpanan_anggota.anggota_ref`
- `pengajuan_pembiayaan.nik`
- `pengajuan_pembiayaan.penanggung_jawab`
- `pengajuan_pembiayaan.nomor_penanggung_jawab`
- `pengajuan_pembiayaan.formulir_permohonan_pembiayaan`
- `modal_koperasi.file_perjanjian`
