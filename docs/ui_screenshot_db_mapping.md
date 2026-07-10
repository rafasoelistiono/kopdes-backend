# UI Screenshot DB Mapping

Exploration date: 2026-07-10

Mode: read-only source DB exploration, safe extracted backup written to `data_backup/dashboard.db`.

## Summary

| Screen | Data Found | Main Table(s) | Scope Key | UI Count Match |
| --- | --- | --- | --- | --- |
| Potensi Desa | yes | `referensi_komoditas_desa`, `referensi_profil_desa`, `referensi_wilayah` | `kode_wilayah` | partial |
| Pengurus | yes | `pengurus_koperasi` | `koperasi_ref` | yes for candidate `KOP-8F17A99DB403` |
| KBLI | yes | `kbli_koperasi` | `koperasi_ref` | yes for multiple koperasi |
| Modal | yes | `modal_koperasi` | `koperasi_ref` | yes for `KOP-B6E872120528` |
| Simpanan | yes | `simpanan_anggota` | `koperasi_ref` | structure differs from UI |
| Pinjaman | partial | `pengajuan_pembiayaan` | `koperasi_ref` | no exact UI total found |

No single `koperasi_ref` matched all six screenshot metrics at once. Best combined candidate is `KOP-8F17A99DB403`: potensi 8, pengurus 8, pengurus status 5/3, KBLI 27, but no modal/pinjaman rows.

## Potensi Desa

Visible UI metrics:

- Potensi Desa: 8
- Dana Desa: `-`
- Total Penduduk: 1.418
- Penduduk Laki-Laki: 732
- Penduduk Wanita: 686
- Rows include Cengkeh, Batok Kelapa, Elektronik, Emas, Kebun Kunyit, Cabai Rawit.

Actual tables found:

- `referensi_komoditas_desa`
- `referensi_profil_desa`
- `referensi_wilayah`
- `referensi_koperasi_wilayah`

Actual columns:

- `referensi_komoditas_desa.komoditas_ref`
- `referensi_komoditas_desa.kode_wilayah`
- `referensi_komoditas_desa.nama_komoditas`
- `referensi_komoditas_desa.luas_area`
- `referensi_komoditas_desa.volume`
- `referensi_komoditas_desa.jumlah_sdm_terlibat`
- `referensi_komoditas_desa.nilai_potensi_desa`
- `referensi_profil_desa.total_penduduk`
- `referensi_profil_desa.penduduk_laki_laki`
- `referensi_profil_desa.penduduk_perempuan`
- `referensi_profil_desa.anggaran_dana_desa`

Counts:

- `referensi_komoditas_desa`: 8.191 rows
- `referensi_profil_desa`: 1.026 rows
- `referensi_wilayah`: 1.026 rows

UI match:

- `potensi_count=8` exists for multiple `kode_wilayah`.
- Exact population `1418/732/686` was not found in `referensi_profil_desa`.
- Requested commodity names only partially found together; no exact six-row set found.

Backup table:

- `group9_ui_potensi_desa`: 8.191 rows

Privacy warning:

- Safe aggregate/village data. No personal data copied.

## Pengurus

Visible UI metrics:

- Total Pengurus & Pengawas: 8
- Pengurus: 5
- Pengawas: 3
- Phone masked in UI.

Actual table found:

- `pengurus_koperasi`

Actual columns:

- `pengurus_ref`
- `koperasi_ref`
- `nama`
- `jabatan`
- `status`
- `no_hp`
- sensitive: `nik`, `email`, `alamat`, `foto_profil`, `file_ktp`

Counts:

- Source rows: 8.482
- Candidate `KOP-8F17A99DB403`: total 8, `PENGURUS=5`, `PENGAWAS=3`

UI match:

- Match found for count/status split.

Backup table:

- `group9_ui_pengurus`: 8.482 rows
- `nama` stored as `nama_masked`
- `no_hp` stored as `no_hp_masked`
- NIK/email/address/file/foto not copied

## KBLI

Visible UI metrics:

- KBLI count: 27
- Columns: Kode KBLI, Nama KBLI

Actual table found:

- `kbli_koperasi`

Actual columns:

- `__row_id`
- `koperasi_ref`
- `kode_kbli`
- `nama_kbli`
- `tipe_izin_usaha`
- `tahun_kbli`

Counts:

- Source rows: 35.591
- Multiple koperasi have exactly 27 KBLI rows.
- Candidate `KOP-8F17A99DB403` has 27 KBLI rows.

UI match:

- Match found for count 27.

Backup table:

- `group9_ui_kbli`: 35.591 rows

Privacy warning:

- Safe business classification data.

## Modal

Visible UI metrics:

- Visible rows: 3
- Columns: Nomor Perjanjian, Tipe Sumber, Nama Sumber, Tipe Modal, Jumlah, Tanggal Diterima

Actual table found:

- `modal_koperasi`

Actual columns:

- `modal_ref`
- `koperasi_ref`
- `nomor_perjanjian`
- `tipe_sumber`
- `nama_sumber`
- `tipe_modal`
- `jumlah`
- `tanggal_diterima`
- sensitive: `file_perjanjian`

Counts:

- Source rows: 26
- `KOP-B6E872120528` has exactly 3 modal rows.
- Total for that candidate: 111.000.000

UI match:

- Count 3 exists, but example values from screenshot were not found as exact same total.

Backup table:

- `group9_ui_modal`: 26 rows
- `file_perjanjian` not copied

## Simpanan

Visible UI metrics:

- Title: Tagihan Simpanan Koperasi
- Rows include Simpanan Pokok, Simpanan Sukarela, Simpanan Wajib
- Total pembayaran examples include Rp70.000, Rp45.000, `-`

Actual table found:

- `simpanan_anggota`

Actual columns:

- `simpanan_ref`
- `koperasi_ref`
- `anggota_ref`
- `periode_pembayaran`
- `jumlah_simpanan`
- `status`
- `dibuat_pada`
- `dibayar_pada`

Counts:

- Source rows: 372.407
- Backup aggregated rows: 6.987

Interpretation:

- Source table stores member-payment-level rows, not pure tagihan master rows.
- UI tagihan rows can be approximated by grouping `koperasi_ref + periode_pembayaran + status`.
- `periode_pembayaran` contains labels like `Simpanan Pokok`, `Simpanan Wajib - Juni 2025`.

UI match:

- Structure exists, but exact UI tagihan model is not a separate table in this DB.

Backup table:

- `group9_ui_simpanan_summary`: 6.987 aggregate rows
- `anggota_ref` not copied

## Pinjaman

Visible UI metrics:

- Jumlah Pinjaman Aktif: 2
- Keseluruhan Pinjaman: 4
- Total Nominal Pinjaman: Rp15.000.000
- Sisa Pinjaman: Rp15.600.000

Actual table found:

- `pengajuan_pembiayaan`

Actual columns:

- `pengajuan_pembiayaan_ref`
- `koperasi_ref`
- `status_permohonan`
- `nominal_permohonan`
- `tenor`
- `tujuan_permohonan`
- sensitive: `nik`, `penanggung_jawab`, `nomor_penanggung_jawab`, `formulir_permohonan_pembiayaan`

Counts:

- Source rows: 118
- No exact `count=4` with total nominal `15.000.000` found.
- No source column for `sisa_pembayaran` found.

Interpretation:

- This DB has pembiayaan application data, not complete loan installment/billing ledger.
- Pinjaman UI likely uses another service/table not present, or derives from application + repayment data outside this DB.

Backup table:

- `group9_ui_pinjaman`: 118 rows
- NIK/person-in-charge/phone/form file not copied

## Extracted Backup Tables

Stored in `data_backup/dashboard.db`:

- `group9_ui_scope_candidates`: 1.026 rows
- `group9_ui_potensi_desa`: 8.191 rows
- `group9_ui_pengurus`: 8.482 rows, masked
- `group9_ui_kbli`: 35.591 rows
- `group9_ui_modal`: 26 rows
- `group9_ui_simpanan_summary`: 6.987 rows, aggregate only
- `group9_ui_pinjaman`: 118 rows, sensitive fields removed
- `group9_ui_penjualan`: 1.000 rows, `nama_pelanggan` removed, product items summarized in `produk_ringkas`
