from typing import Any


def _num(value: Any) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _fact_value(facts: list[dict], key: str) -> Any:
    for f in facts:
        if f.get("key") == key:
            return f.get("value")
    return None


def _table_rows(context: dict, key: str) -> list[dict]:
    for t in context.get("tables", []):
        if t.get("key") == key:
            return t.get("rows", [])
    return []


def build_correlations(context_pack: dict) -> list[dict]:
    correlations = []
    facts = context_pack.get("facts", [])
    scope = context_pack.get("scope", {})
    dashboard_key = scope.get("dashboard_key")

    if dashboard_key == "pengurus-koperasi":
        correlations.extend(_correlations_pengurus(facts, context_pack))
    elif dashboard_key == "satgas-kdmp":
        correlations.extend(_correlations_satgas(facts, context_pack))
    elif dashboard_key == "kepala-desa":
        correlations.extend(_correlations_kepala_desa(facts, context_pack))
    else:
        correlations.extend(_correlations_generic(facts, context_pack))

    return correlations


def _correlations_pengurus(facts: list[dict], ctx: dict) -> list[dict]:
    result = []
    transaksi = _num(_fact_value(facts, "jumlah_transaksi"))
    paid_ratio = _num(_fact_value(facts, "rasio_simpanan_terbayar"))
    gerai_status = str(_fact_value(facts, "gerai_status") or "").lower()
    rat_status = str(_fact_value(facts, "status_rat_terakhir") or "").lower()
    docs_complete = _fact_value(facts, "dokumen_wajib_lengkap")
    potensi = _fact_value(facts, "potensi_desa_utama")
    slow = _table_rows(ctx, "slow_moving_products")

    if transaksi == 0 and paid_ratio < 60:
        result.append({
            "key": "transaksi_0_simpanan_rendah",
            "title": "Aktivitas transaksi nol dan partisipasi simpanan rendah",
            "evidence": [
                {"label": "Jumlah Transaksi", "value": "0"},
                {"label": "Rasio Simpanan Terbayar", "value": f"{paid_ratio:.0f}%"},
            ],
            "meaning": "Tidak ada aktivitas usaha tercatat dan simpanan anggota banyak yang belum terbayar. Koperasi perlu dorongan aktivitas ekonomi dan penagihan simpanan.",
            "severity": "danger",
            "sources": ["koperasi_monthly_metrics"],
        })

    if "aktif" in gerai_status and transaksi == 0:
        result.append({
            "key": "gerai_aktif_transaksi_0",
            "title": "Gerai aktif tetapi transaksi belum berjalan",
            "evidence": [
                {"label": "Status Gerai", "value": gerai_status.title()},
                {"label": "Jumlah Transaksi", "value": "0"},
            ],
            "meaning": "Gerai sudah siap secara status tetapi belum menghasilkan aktivitas ekonomi. Perlu evaluasi kesiapan operasional gerai.",
            "severity": "warning",
            "sources": ["gerai_asset_snapshot", "koperasi_monthly_metrics"],
        })

    if ("belum" in rat_status or "tidak" in rat_status) and not docs_complete:
        result.append({
            "key": "rat_belum_dokumen_tidak_lengkap",
            "title": "RAT belum dan dokumen tidak lengkap",
            "evidence": [
                {"label": "Status RAT", "value": rat_status or "Belum"},
                {"label": "Dokumen Wajib", "value": "Tidak Lengkap" if not docs_complete else "Lengkap"},
            ],
            "meaning": "RAT belum terpenuhi dan dokumen wajib belum lengkap. Ini risiko kepatuhan yang perlu ditindaklanjuti segera.",
            "severity": "danger",
            "sources": ["rat_compliance_snapshot"],
        })

    if slow:
        produk_names = [p.get("nama_produk", "-") for p in slow[:3]]
        result.append({
            "key": "produk_lambat_stok_tertahan",
            "title": "Produk lambat dan stok tertahan",
            "evidence": [
                {"label": "Produk Lambat", "value": ", ".join(produk_names)},
                {"label": "Jumlah", "value": str(len(slow))},
            ],
            "meaning": f"Ada {len(slow)} produk dengan pergerakan lambat. Stok tertahan mengikat modal kerja.",
            "severity": "warning",
            "sources": ["product_monthly_metrics"],
        })

    if potensi and transaksi == 0:
        result.append({
            "key": "potensi_ada_transaksi_0",
            "title": "Potensi desa ada tapi transaksi nol",
            "evidence": [
                {"label": "Potensi Utama", "value": str(potensi)},
                {"label": "Jumlah Transaksi", "value": "0"},
            ],
            "meaning": "Potensi desa teridentifikasi tetapi belum terkonversi menjadi aktivitas ekonomi koperasi.",
            "severity": "warning",
            "sources": ["village_potential_snapshot", "koperasi_monthly_metrics"],
        })

    return result


def _correlations_satgas(facts: list[dict], ctx: dict) -> list[dict]:
    result = []
    belum_rat = _num(_fact_value(facts, "belum_rat"))
    total = _num(_fact_value(facts, "total_koperasi"))
    gerai_aktif = _num(_fact_value(facts, "gerai_aktif"))
    paid_ratio = _num(_fact_value(facts, "simpanan_paid_ratio"))
    transaksi = _num(_fact_value(facts, "volume_transaksi"))
    wilayah_prioritas = _num(_fact_value(facts, "wilayah_prioritas_pembinaan"))

    if belum_rat > 0 and total > 0 and belum_rat / total > 0.5:
        result.append({
            "key": "satgas_belum_rat_prioritas",
            "title": "Mayoritas koperasi belum RAT",
            "evidence": [
                {"label": "Belum RAT", "value": str(int(belum_rat))},
                {"label": "Total Koperasi", "value": str(int(total))},
            ],
            "meaning": f"{int(belum_rat)} dari {int(total)} koperasi belum RAT. Ini prioritas utama pembinaan.",
            "severity": "danger",
            "sources": ["regional_monthly_metrics"],
        })

    if gerai_aktif > 0 and transaksi == 0:
        result.append({
            "key": "gerai_aktif_nol_transaksi",
            "title": "Gerai aktif tetapi transaksi nol",
            "evidence": [
                {"label": "Gerai Aktif", "value": str(int(gerai_aktif))},
                {"label": "Volume Transaksi", "value": "0"},
            ],
            "meaning": "Gerai sudah aktif tetapi belum menghasilkan transaksi. Perlu evaluasi kesiapan operasional.",
            "severity": "warning",
            "sources": ["gerai_asset_snapshot", "regional_monthly_metrics"],
        })

    if paid_ratio < 60:
        result.append({
            "key": "simpanan_unpaid_health_drop",
            "title": "Rasio simpanan terbayar rendah",
            "evidence": [
                {"label": "Rasio Terbayar", "value": f"{paid_ratio:.0f}%"},
            ],
            "meaning": "Simpanan anggota banyak belum terbayar. Berpotensi mempengaruhi likuiditas dan partisipasi anggota.",
            "severity": "warning",
            "sources": ["regional_monthly_metrics"],
        })

    if wilayah_prioritas > 0:
        result.append({
            "key": "ada_wilayah_prioritas",
            "title": "Ada wilayah prioritas pembinaan",
            "evidence": [
                {"label": "Wilayah Prioritas", "value": str(int(wilayah_prioritas))},
            ],
            "meaning": f"Ada {int(wilayah_prioritas)} wilayah yang masuk prioritas pembinaan. Perlu alokasi sumber daya satgas.",
            "severity": "warning",
            "sources": ["regional_monthly_metrics"],
        })

    return result


def _correlations_kepala_desa(facts: list[dict], ctx: dict) -> list[dict]:
    result = []
    belum_rat = _num(_fact_value(facts, "koperasi_belum_rat"))
    total = _num(_fact_value(facts, "total_koperasi_desa"))
    gerai_aktif = _num(_fact_value(facts, "gerai_aktif"))
    gerai_belum = _num(_fact_value(facts, "gerai_belum_aktif"))
    transaksi = _num(_fact_value(facts, "total_nilai_transaksi_desa"))
    potensi = _fact_value(facts, "potensi_komoditas_utama")

    if belum_rat > 0 and total > 0:
        result.append({
            "key": "desa_belum_rat",
            "title": "Ada koperasi desa belum RAT",
            "evidence": [
                {"label": "Belum RAT", "value": str(int(belum_rat))},
                {"label": "Total Koperasi", "value": str(int(total))},
            ],
            "meaning": f"{int(belum_rat)} dari {int(total)} koperasi desa belum RAT. Perlu pembinaan lanjutan.",
            "severity": "warning",
            "sources": ["regional_monthly_metrics"],
        })

    if gerai_belum > 0 and gerai_aktif == 0:
        result.append({
            "key": "desa_gerai_belum_aktif",
            "title": "Gerai desa belum ada yang aktif",
            "evidence": [
                {"label": "Gerai Belum Aktif", "value": str(int(gerai_belum))},
            ],
            "meaning": "Belum ada gerai aktif di desa ini. Perlu prioritas pembangunan dan aktivasi.",
            "severity": "warning",
            "sources": ["regional_monthly_metrics"],
        })

    if potensi and transaksi == 0:
        result.append({
            "key": "desa_potensi_tanpa_transaksi",
            "title": "Potensi desa ada tapi transaksi nol",
            "evidence": [
                {"label": "Komoditas Utama", "value": str(potensi)},
                {"label": "Total Transaksi", "value": "Rp 0"},
            ],
            "meaning": "Potensi komoditas desa teridentifikasi tetapi belum ada transaksi koperasi. Peluang untuk dikembangkan.",
            "severity": "warning",
            "sources": ["village_potential_snapshot", "regional_monthly_metrics"],
        })

    return result


def _correlations_generic(facts: list[dict], ctx: dict) -> list[dict]:
    return []
