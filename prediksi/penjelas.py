"""Ringkasan grafik untuk halaman Wawasan. Dibuat oleh Groq (LLM); bila tidak tersedia, dipakai ringkasan otomatis dari data.

Kunci API dibaca dari environment variable GROQ_API_KEY dan tidak pernah ditulis di kode.
"""
import json
import os
import urllib.error
import urllib.request

from .layanan import muat_ringkasan

URL = "https://api.groq.com/openai/v1/chat/completions"
URL_MODEL = "https://api.groq.com/openai/v1/models"
UTAMA = ["llama-3.3-70b-versatile", "openai/gpt-oss-120b", "llama-3.1-8b-instant", "openai/gpt-oss-20b"]
BUKAN_CHAT = ("whisper", "guard", "tts", "orpheus", "playai", "embed")

NAMA_FITUR = {
    "merek": "merek", "model": "model", "kelas": "jenis mobil", "transmisi": "transmisi", "penggerak": "penggerak roda",
    "turbo": "turbo", "hybrid": "hybrid", "diesel": "mesin diesel", "tahun": "tahun pembuatan",
    "silinder": "jumlah silinder", "mesin_liter": "ukuran mesin",
}


def _koma(angka):
    return f"{angka:.1f}".replace(".", ",")


def _kecil(teks):
    """Huruf kecil, tetapi MPV tetap kapital."""
    return teks.lower().replace("mpv", "MPV")


def _fakta():
    """Angka-angka penting dari data, dipakai untuk prompt LLM dan untuk ringkasan otomatis."""
    r = muat_ringkasan()
    silinder = dict(zip(r["per_silinder"]["label"], r["per_silinder"]["kml"]))
    urut = sorted(r["pentingnya_fitur"].items(), key=lambda p: -p[1])
    return {
        "jumlah": r["jumlah_data"], "merek": r["jumlah_merek"],
        "tahun_awal": r["rentang"]["tahun"][0], "tahun_akhir": r["rentang"]["tahun"][1],
        "median": r["kml_median"],
        "silinder_4": silinder[4], "silinder_8": silinder[8],
        "kml_awal": r["per_tahun"]["kml"][0], "kml_akhir": r["per_tahun"]["kml"][-1],
        "kelas_irit": r["per_kelas"]["label"][0], "kelas_irit_kml": r["per_kelas"]["kml"][0],
        "kelas_boros": r["per_kelas"]["label"][-1], "kelas_boros_kml": r["per_kelas"]["kml"][-1],
        "penting": [(NAMA_FITUR[k], round(v * 100)) for k, v in urut[:4]],
    }


def ringkasan_otomatis():
    """Ringkasan tanpa AI, disusun langsung dari angka (dipakai bila Groq tidak tersedia)."""
    f = _fakta()
    return "\n".join([
        f"- Ukuran mesin adalah faktor yang paling menentukan ({f['penting'][0][1]}% pengaruh): mesin lebih besar umumnya lebih boros.",
        f"- Mobil 4 silinder rata-rata {_koma(f['silinder_4'])} km/L, sedangkan 8 silinder hanya {_koma(f['silinder_8'])} km/L.",
        f"- Dari {f['tahun_awal']} sampai {f['tahun_akhir']}, rata-rata efisiensi naik dari {_koma(f['kml_awal'])} menjadi {_koma(f['kml_akhir'])} km/L.",
        f"- Jenis mobil paling irit adalah {_kecil(f['kelas_irit'])} ({_koma(f['kelas_irit_kml'])} km/L), paling boros {_kecil(f['kelas_boros'])} ({_koma(f['kelas_boros_kml'])} km/L).",
    ])


def _prompt():
    f = _fakta()
    data = (
        f"Data: {f['jumlah']} varian mobil dari {f['merek']} merek, tahun {f['tahun_awal']}-{f['tahun_akhir']}; "
        f"nilai tengah konsumsi {_koma(f['median'])} km/L.\n"
        f"Rata-rata km/L: mobil 4 silinder {_koma(f['silinder_4'])}, mobil 8 silinder {_koma(f['silinder_8'])}.\n"
        f"Rata-rata km/L menurut tahun: {f['tahun_awal']} = {_koma(f['kml_awal'])}, {f['tahun_akhir']} = {_koma(f['kml_akhir'])}.\n"
        f"Jenis mobil paling irit: {f['kelas_irit']} ({_koma(f['kelas_irit_kml'])} km/L); paling boros: {f['kelas_boros']} ({_koma(f['kelas_boros_kml'])} km/L).\n"
        "Faktor paling berpengaruh pada model prediksi: " + ", ".join(f"{n} {p}%" for n, p in f["penting"]) + "."
    )
    return (
        "Kamu menjelaskan grafik pada website cek konsumsi BBM mobil kepada pengunjung awam. "
        "Satuan yang dipakai adalah km per liter (km/L): angka LEBIH BESAR berarti LEBIH IRIT, angka lebih kecil berarti lebih boros. "
        "Jangan memakai kata 'konsumsi lebih rendah' atau 'konsumsi lebih tinggi'; pakai kata 'irit' dan 'boros' saja. "
        "Gunakan HANYA angka pada data di bawah dan jangan menambah angka lain. "
        "Tulis dalam bahasa Indonesia yang sederhana tanpa istilah teknis, tepat 4 poin, tiap poin satu atau dua kalimat, "
        "diawali tanda '- ' dan tanpa format markdown lain. "
        "Poin: (1) mesin yang lebih besar dan silinder yang lebih banyak membuat mobil LEBIH BOROS (km/L lebih kecil), "
        "(2) perbandingan 4 dan 8 silinder, (3) tren dari tahun ke tahun, "
        "(4) jenis mobil paling irit dan paling boros, ditutup satu kalimat bahwa faktor-faktor ini saling berkaitan "
        "dan data berasal dari uji EPA di Amerika Serikat.\n\nDATA:\n" + data
    )


def _header(kunci):
    return {"Authorization": f"Bearer {kunci}", "Content-Type": "application/json", "User-Agent": "ekobbm/1.0"}


def _model_chat(kunci):
    """Menanyakan ke Groq model apa yang boleh dipakai akun ini, lalu mengurutkan yang disukai di depan."""
    with urllib.request.urlopen(urllib.request.Request(URL_MODEL, headers=_header(kunci)), timeout=20) as jawaban:
        ada = [m["id"] for m in json.loads(jawaban.read().decode("utf-8"))["data"]]
    ada = [m for m in ada if not any(k in m for k in BUKAN_CHAT)]
    return [m for m in UTAMA if m in ada] + [m for m in ada if m not in UTAMA]


_cache = {}


def penjelasan_wawasan():
    """Mengembalikan (sumber, teks). sumber = 'ai' bila dari Groq, 'otomatis' bila memakai ringkasan cadangan."""
    if "teks" in _cache:
        return "ai", _cache["teks"]

    kunci = os.environ.get("GROQ_API_KEY")
    if not kunci:
        return "otomatis", ringkasan_otomatis()
    try:
        daftar = _model_chat(kunci)
    except Exception:
        return "otomatis", ringkasan_otomatis()

    for model in daftar[:4]:
        isi = json.dumps({"model": model, "messages": [{"role": "user", "content": _prompt()}], "temperature": 0.2}).encode("utf-8")
        permintaan = urllib.request.Request(URL, data=isi, method="POST", headers=_header(kunci))
        try:
            with urllib.request.urlopen(permintaan, timeout=30) as jawaban:
                teks = json.loads(jawaban.read().decode("utf-8"))["choices"][0]["message"]["content"].strip()
            if teks:
                _cache["teks"] = teks
                return "ai", teks
        except Exception:
            continue
    return "otomatis", ringkasan_otomatis()