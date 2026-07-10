# DB Mapping Generated

Generated from `information_schema` on `public` schema. No declared foreign keys found; joins are inferred by shared reference columns.

## Inferred Join Keys

| Key | Tables |
| --- | --- |
| `koperasi_ref` | `profil_koperasi`, `referensi_koperasi_wilayah`, `anggota_koperasi`, `simpanan_anggota`, `transaksi_penjualan`, `barang_keluar_produk`, `barang_masuk_produk`, `produk_koperasi`, `inventaris_produk`, `rat_koperasi`, `dokumen_koperasi`, `gerai_koperasi`, `aset_koperasi`, `modal_koperasi`, `pengajuan_pembiayaan`, `pengajuan_kemitraan`, `akun_bank_koperasi`, `kbli_koperasi` |
| `kode_wilayah` | `referensi_wilayah`, `referensi_koperasi_wilayah`, `referensi_profil_desa`, `referensi_komoditas_desa`, `anggota_koperasi` |
| `anggota_ref` | `anggota_koperasi`, `simpanan_anggota` |
| `produk_sample_id` | `produk_koperasi`, `barang_keluar_produk`, `barang_masuk_produk`, `inventaris_produk` |
| `transaksi_sample_id` | `transaksi_penjualan`, `barang_keluar_produk` |
| `jenis_dokumen_ref` | `dokumen_koperasi`, `referensi_dokumen_koperasi` |
| `jenis_gerai_ref` | `gerai_koperasi`, `referensi_gerai_koperasi` |

## Table Mapping

| Table | Columns | Safe Columns Used | Sensitive Columns | Dashboard Domains |
| --- | --- | --- | --- | --- |
| `akun_bank_koperasi` | `akun_bank_ref`, `koperasi_ref`, `nama_rekening`, `nama_bank`, `dibuat_pada`, `diperbarui_pada` | `koperasi_ref`, `nama_bank` | `nama_rekening` | pengurus_koperasi |
| `anggota_koperasi` | `anggota_ref`, `koperasi_ref`, `nama`, `nik`, `kode_wilayah`, `jenis_kelamin`, `status_keanggotaan`, `tanggal_terdaftar`, `dibuat_pada`, `diperbarui_pada`, `file_ktp`, `status_akun`, `pekerjaan` | aggregate counts by `koperasi_ref`, `status_keanggotaan` | `nama`, `nik`, `file_ktp` | kepala_desa, satgas_kdmp |
| `aset_koperasi` | `aset_ref`, `koperasi_ref`, `nama_aset`, `tipe_aset`, `status`, `progres_pembangunan`, `foto_utama`, `foto_sekunder`, `dokumen_utama`, `dokumen_sekunder`, `dokumen_lainnya`, `luas_lahan`, `panjang_lahan`, `lebar_lahan`, `akses_jalan`, `koordinat_dibulatkan`, `dibuat_pada`, `diperbarui_pada` | `koperasi_ref`, `status`, `progres_pembangunan`, dimensions | `foto_*`, `dokumen_*`, `koordinat_dibulatkan` | kepala_desa, satgas_kdmp |
| `barang_keluar_produk` | `__row_id`, `transaksi_sample_id`, `produk_sample_id`, `koperasi_ref`, `kode_barcode`, `tanggal_keluar`, `status`, `nama_produk`, `nama_tampilan`, `jumlah_keluar`, `harga`, `total_nilai`, `status_transaksi`, `dibuat_pada`, `diperbarui_pada` | product movement aggregates | none | pengurus_koperasi, satgas_kdmp |
| `barang_masuk_produk` | `barang_masuk_ref`, `produk_sample_id`, `koperasi_ref`, `kode_barcode`, `nama_produk`, `nama_tampilan`, `jumlah_masuk`, `jumlah_tersedia`, `harga_beli`, `harga_jual`, `total_biaya`, `keterangan`, `status`, `tanggal_masuk`, `dibuat_pada`, `diperbarui_pada` | inventory movement aggregates | none | pengurus_koperasi |
| `dokumen_koperasi` | `dokumen_ref`, `koperasi_ref`, `jenis_dokumen_ref`, `nomor`, `tanggal_berlaku`, `tanggal_kadaluarsa`, `alamat_pada_dokumen`, `unggahan_dokumen`, `dibuat_pada`, `diperbarui_pada` | document counts, expiry dates, `jenis_dokumen_ref` | `nomor`, `alamat_pada_dokumen`, `unggahan_dokumen` | pengurus_koperasi, kepala_desa, satgas_kdmp |
| `gerai_koperasi` | `gerai_ref`, `koperasi_ref`, `jenis_gerai_ref`, `status_gerai`, `foto_gerai`, `pengisi`, `akses_internet`, `akses_listrik`, `status_kepemilikan_aset_gerai`, `status_pemanfaatan_aset_gerai`, `sumber_air_bersih`, `jenis_bangunan`, `koordinat_dibulatkan`, `dibuat_pada`, `diperbarui_pada` | gerai status/infrastructure aggregates | `foto_gerai`, `koordinat_dibulatkan` | kepala_desa, satgas_kdmp |
| `inventaris_produk` | `inventaris_ref`, `produk_sample_id`, `koperasi_ref`, `nama_produk`, `stok`, `dibuat_pada`, `diperbarui_pada`, `kode_barcode` | `nama_produk`, `stok`, stock-risk aggregate | none | pengurus_koperasi |
| `kbli_koperasi` | `__row_id`, `koperasi_ref`, `kode_kbli`, `nama_kbli`, `tipe_izin_usaha`, `tahun_kbli`, `dibuat_pada`, `diperbarui_pada` | legality/sector aggregates | none | satgas_kdmp |
| `modal_koperasi` | `modal_ref`, `koperasi_ref`, `nomor_perjanjian`, `tipe_sumber`, `nama_sumber`, `tipe_modal`, `jumlah`, `tanggal_diterima`, `file_perjanjian`, `dibuat_pada`, `diperbarui_pada` | capital sum by `koperasi_ref` | `nomor_perjanjian`, `file_perjanjian` | pengurus_koperasi, satgas_kdmp |
| `pengajuan_kemitraan` | `pengajuan_kemitraan_ref`, `koperasi_ref`, `nik`, `penanggung_jawab`, `nomor_penanggung_jawab`, `status_permohonan`, `bisnis_kemitraan`, `paket_kemitraan`, `formulir_permohonan`, `ktp_penanggung_jawab`, `tipe_kemitraan`, `catatan`, `dibuat_pada`, `diperbarui_pada` | aggregate by status | `nik`, `penanggung_jawab`, `nomor_penanggung_jawab`, `formulir_permohonan`, `ktp_penanggung_jawab` | satgas_kdmp |
| `pengajuan_pembiayaan` | `pengajuan_pembiayaan_ref`, `koperasi_ref`, `nik`, `penanggung_jawab`, `nomor_penanggung_jawab`, `status_permohonan`, `formulir_permohonan_pembiayaan`, `nominal_permohonan`, `tenor`, `tujuan_permohonan`, `dibuat_pada`, `diperbarui_pada` | aggregate by status and nominal | `nik`, `penanggung_jawab`, `nomor_penanggung_jawab`, `formulir_permohonan_pembiayaan` | pengurus_koperasi, kepala_desa, satgas_kdmp |
| `pengurus_koperasi` | `pengurus_ref`, `koperasi_ref`, `nama`, `jabatan`, `status`, `no_hp`, `nik`, `jenis_kelamin`, `foto_profil`, `email`, `alamat`, `kode_pos`, `tanggal_lahir`, `status_pendidikan`, `periode_mulai`, `periode_selesai`, `file_ktp`, `sumber_data`, `dibuat_pada`, `diperbarui_pada` | none in dashboard responses | `nama`, `no_hp`, `nik`, `foto_profil`, `email`, `alamat`, `tanggal_lahir`, `file_ktp` | not exposed |
| `produk_koperasi` | `produk_sample_id`, `koperasi_ref`, `kode_barcode`, `nama_produk`, `unit`, `dibuat_pada`, `diperbarui_pada` | product reference fields | none | pengurus_koperasi |
| `profil_koperasi` | `koperasi_ref`, `nama_koperasi`, `status_registrasi`, `bentuk_koperasi`, `kategori_usaha`, `nik_koperasi`, `alamat_lengkap`, `kode_pos`, `koordinat_dibulatkan`, `modal_awal`, `sumber_persetujuan`, `tentang_koperasi`, `pola_pengelolaan`, `metode_pengisian`, `dibuat_pada`, `diperbarui_pada` | `koperasi_ref`, `nama_koperasi`, status/category fields | `nik_koperasi`, `alamat_lengkap`, `koordinat_dibulatkan` | all dashboards |
| `rat_koperasi` | `rat_sample_id`, `koperasi_ref`, `jenis_sektor_koperasi`, `urutan_rat`, `tahun_buku`, `tahun_rencana_kerja`, `tahun_rencana_anggaran`, `tanggal_rat`, `jumlah_peserta_rat`, `status_rat`, `tahap_rat`, `laporan_posisi_keuangan`, `laporan_hasil_usaha`, `rapb_posisi_keuangan`, `rapb_hasil_usaha`, `dibuat_pada`, `diperbarui_pada` | RAT status/year/counts | report file columns | pengurus_koperasi, kepala_desa, satgas_kdmp |
| `referensi_dokumen_koperasi` | `jenis_dokumen_ref`, `nama_dokumen`, `dibuat_pada`, `diperbarui_pada` | reference labels | none | pengurus_koperasi |
| `referensi_gerai_koperasi` | `jenis_gerai_ref`, `nama_jenis_gerai`, `dibuat_pada`, `diperbarui_pada` | reference labels | none | kepala_desa, satgas_kdmp |
| `referensi_komoditas_desa` | `komoditas_ref`, `kode_wilayah`, `nama_komoditas`, `luas_area`, `volume`, `jumlah_sdm_terlibat`, `nilai_potensi_desa`, `dibuat_pada`, `diperbarui_pada` | commodity potential | none | pengurus_koperasi, kepala_desa, satgas_kdmp |
| `referensi_koperasi_wilayah` | `koperasi_ref`, `kode_wilayah`, `dibuat_pada`, `diperbarui_pada` | join table | none | all regional dashboards |
| `referensi_profil_desa` | `kode_wilayah`, `tahun_populasi`, `total_penduduk`, `penduduk_laki_laki`, `penduduk_perempuan`, `tahun_pendanaan`, `anggaran_dana_desa`, `dibuat_pada`, `diperbarui_pada` | village aggregate profile | none | kepala_desa, satgas_kdmp |
| `referensi_wilayah` | `provinsi`, `kab_kota`, `kecamatan`, `desa_kelurahan`, `kode_wilayah`, `dibuat_pada`, `diperbarui_pada` | wilayah labels | none | lookups, kepala_desa, satgas_kdmp |
| `simpanan_anggota` | `simpanan_ref`, `koperasi_ref`, `anggota_ref`, `periode_pembayaran`, `jumlah_simpanan`, `status`, `dibuat_pada`, `dibayar_pada` | savings aggregate by period/status | `anggota_ref` not exposed | pengurus_koperasi, kepala_desa, satgas_kdmp |
| `transaksi_penjualan` | `transaksi_sample_id`, `koperasi_ref`, `nama_pelanggan`, `tanggal_dibuat`, `total_pembayaran`, `status_transaksi`, `metode_pembayaran`, `dibuat_pada`, `diperbarui_pada` | transaction aggregate/trend | `nama_pelanggan` | pengurus_koperasi, kepala_desa, satgas_kdmp |

Tables present but not currently exposed in dashboards: `karyawan_koperasi`, `pengajuan_domain`, `pengajuan_rekening_bank`, `pengurus_koperasi`.
