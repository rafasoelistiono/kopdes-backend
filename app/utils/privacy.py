SENSITIVE_PATTERNS = [
    "nik", "ktp", "email", "phone", "hp", "telp",
    "alamat", "rekening", "file", "foto", "lampiran",
    "attachment", "document_url", "dokumen_file",
]

SENSITIVE_FIELD_NAMES = {
    "nik", "no_ktp", "nomor_ktp", "file_ktp",
    "email", "email_pribadi",
    "nomor_hp", "nomor_penanggung_jawab",
    "phone", "telp", "no_hp",
    "alamat", "alamat_lengkap", "alamat_pada_dokumen",
    "no_rekening", "nomor_rekening", "nama_rekening",
    "foto_utama", "foto_sekunder", "foto_profil", "foto_gerai",
    "lampiran", "unggahan_dokumen",
    "file_perjanjian", "formulir_permohonan",
    "ktp_penanggung_jawab", "formulir_permohonan_pembiayaan",
    "dokumen_utama", "dokumen_sekunder", "dokumen_lainnya",
    "laporan_posisi_keuangan", "laporan_hasil_usaha",
    "rapb_posisi_keuangan", "rapb_hasil_usaha",
    "koordinat_dibulatkan",
    "nik_koperasi",
    "foto",
}


def is_sensitive_key(key: str) -> bool:
    kl = key.lower().replace("_", "").replace(" ", "")
    for pattern in SENSITIVE_PATTERNS:
        if pattern in kl:
            return True
    if key in SENSITIVE_FIELD_NAMES:
        return True
    return False


def redact_sensitive_fields(record: dict) -> dict:
    return {k: v for k, v in record.items() if not is_sensitive_key(k)}


def redact_nested_payload(payload):
    if isinstance(payload, dict):
        return {k: redact_nested_payload(v) for k, v in payload.items() if not is_sensitive_key(k)}
    if isinstance(payload, list):
        return [redact_nested_payload(item) for item in payload]
    return payload


def safe_project(record: dict, allowed_fields: list[str]) -> dict:
    result = {}
    for field in allowed_fields:
        if field in record:
            result[field] = record[field]
    return result


SENSITIVE_TABLES = {
    "anggota_koperasi",
    "karyawan_koperasi",
    "pengurus_koperasi",
    "pengajuan_pembiayaan",
    "pengajuan_kemitraan",
    "pengajuan_rekening_bank",
}

SENSITIVE_TABLE_COLUMNS = {
    "anggota_koperasi": {"nik", "file_ktp"},
    "karyawan_koperasi": {"nik", "nomor_hp_karyawan", "email"},
    "pengurus_koperasi": {"nik", "no_hp", "email", "alamat", "foto_profil", "file_ktp"},
    "pengajuan_pembiayaan": {"nik", "nomor_penanggung_jawab"},
    "pengajuan_kemitraan": {"nik", "nomor_penanggung_jawab", "ktp_penanggung_jawab"},
    "pengajuan_rekening_bank": {"nik", "nomor_penanggung_jawab"},
}
