"""Penjelasan tiap grafik di halaman Wawasan. Ditulis oleh Groq (LLM); bila tidak tersedia, dipakai penjelasan otomatis dari data.

Kunci API dibaca dari environment variable GROQ_API_KEY dan tidak pernah ditulis di kode.
"""
import json
import os
import urllib.request

from .layanan import muat_ringkasan

URL = "https://api.groq.com/openai/v1/chat/completions"
URL_MODEL = "https://api.groq.com/openai/v1/models"
UTAMA = ["llama-3.3-70b-versatile", "openai/gpt-oss-120b", "llama-3.1-8b-instant", "openai/gpt-oss-20b"]
BUKAN_CHAT = ("whisper", "guard", "tts", "orpheus", "playai", "embed")

# kunci penjelasan = satu kunci per grafik di halaman Wawasan
KUNCI = ["sebaran", "silinder", "tahun", "kelas", "merek", "faktor"]

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


def _rata(daftar):
    return sum(daftar) / len(daftar)


def _fakta():
    """Angka-angka penting dari data, dipakai untuk prompt LLM dan untuk penjelasan otomatis."""
    r = muat_ringkasan()
    silinder = dict(zip(r["per_silinder"]["label"], r["per_silinder"]["kml"]))
    urut = sorted(r["pentingnya_fitur"].items(), key=lambda p: -p[1])
    mesin, kml = r["sebaran"]["mesin_liter"], r["sebaran"]["kml"]
    kecil = [k for m, k in zip(mesin, kml) if m < 2.0]
    besar = [k for m, k in zip(mesin, kml) if m >= 4.0]
    return {
        "jumlah": r["jumlah_data"], "merek": r["jumlah_merek"],
        "tahun_awal": r["rentang"]["tahun"][0], "tahun_akhir": r["rentang"]["tahun"][1],
        "median": r["kml_median"],
        "mesin_kecil": _rata(kecil), "mesin_besar": _rata(besar),
        "silinder_4": silinder[4], "silinder_8": silinder[8],
        "kml_awal": r["per_tahun"]["kml"][0], "kml_akhir": r["per_tahun"]["kml"][-1],
        "kelas_irit": r["per_kelas"]["label"][0], "kelas_irit_kml": r["per_kelas"]["kml"][0],
        "kelas_boros": r["per_kelas"]["label"][-1], "kelas_boros_kml": r["per_kelas"]["kml"][-1],
        "merek_irit": r["per_merek"]["label"][0], "merek_irit_kml": r["per_merek"]["kml"][0],
        "merek_boros": r["per_merek"]["label_boros"][-1], "merek_boros_kml": r["per_merek"]["kml_boros"][-1],
        "penting": [(NAMA_FITUR[k], round(v * 100)) for k, v in urut[:4]],
    }


def penjelasan_otomatis():
    """Penjelasan tanpa AI, disusun langsung dari angka (dipakai bila Groq tidak tersedia)."""
    f = _fakta()
    return {
        "sebaran": f"Mobil bermesin di bawah 2 liter rata-rata menempuh {_koma(f['mesin_kecil'])} km per liter, "
                   f"sedangkan yang bermesin 4 liter ke atas hanya {_koma(f['mesin_besar'])} km per liter.",
        "silinder": f"Mobil 4 silinder rata-rata {_koma(f['silinder_4'])} km per liter, sedangkan 8 silinder hanya "
                    f"{_koma(f['silinder_8'])}. Makin banyak silinder, makin boros.",
        "tahun": f"Dari {f['tahun_awal']} sampai {f['tahun_akhir']}, rata-rata mobil makin irit: "
                 f"dari {_koma(f['kml_awal'])} menjadi {_koma(f['kml_akhir'])} km per liter.",
        "kelas": f"Jenis {_kecil(f['kelas_irit'])} paling irit ({_koma(f['kelas_irit_kml'])} km per liter), "
                 f"sedangkan {_kecil(f['kelas_boros'])} paling boros ({_koma(f['kelas_boros_kml'])} km per liter).",
        "merek": f"{f['merek_irit']} rata-rata paling irit ({_koma(f['merek_irit_kml'])} km per liter) dan "
                 f"{f['merek_boros']} paling boros ({_koma(f['merek_boros_kml'])}). Hasil ini ikut dipengaruhi jenis mobil yang dijual tiap merek.",
        "faktor": f"Ukuran mesin paling menentukan ({f['penting'][0][1]}%), disusul {f['penting'][1][0]} ({f['penting'][1][1]}%) "
                  f"dan {f['penting'][2][0]} ({f['penting'][2][1]}%).",
    }


def _prompt():
    f = _fakta()
    data = (
        f"sebaran: mobil bermesin di bawah 2 liter rata-rata {_koma(f['mesin_kecil'])} km/L; mesin 4 liter ke atas {_koma(f['mesin_besar'])} km/L.\n"
        f"silinder: 4 silinder rata-rata {_koma(f['silinder_4'])} km/L; 8 silinder {_koma(f['silinder_8'])} km/L.\n"
        f"tahun: rata-rata {f['tahun_awal']} = {_koma(f['kml_awal'])} km/L; {f['tahun_akhir']} = {_koma(f['kml_akhir'])} km/L.\n"
        f"kelas: paling irit {f['kelas_irit']} ({_koma(f['kelas_irit_kml'])} km/L); paling boros {f['kelas_boros']} ({_koma(f['kelas_boros_kml'])} km/L).\n"
        f"merek: paling irit {f['merek_irit']} ({_koma(f['merek_irit_kml'])} km/L); paling boros {f['merek_boros']} ({_koma(f['merek_boros_kml'])} km/L); "
        "hasil per merek dipengaruhi jenis mobil yang dijual.\n"
        "faktor: pengaruh pada model prediksi: " + ", ".join(f"{n} {p}%" for n, p in f["penting"]) + "."
    )
    return (
        "Kamu menjelaskan enam grafik pada website cek konsumsi BBM mobil kepada pengunjung awam, termasuk orang tua yang tidak paham grafik. "
        "Satuan: km per liter (km/L); angka LEBIH BESAR berarti LEBIH IRIT, angka lebih kecil berarti lebih boros. "
        "Jangan memakai kata 'konsumsi lebih rendah' atau 'konsumsi lebih tinggi'; pakai kata 'irit' dan 'boros' saja. "
        "Gunakan HANYA angka pada data di bawah dan jangan menambah angka lain. "
        "Untuk tiap grafik tulis 1 sampai 2 kalimat bahasa Indonesia yang sederhana tanpa istilah teknis: apa temuannya, "
        "lalu apa artinya bagi orang yang memilih mobil. "
        "Jawab HANYA dengan satu objek JSON dengan tepat enam kunci: sebaran, silinder, tahun, kelas, merek, faktor. "
        "Nilainya teks biasa tanpa format markdown.\n\nDATA:\n" + data
    )


def _header(kunci):
    return {"Authorization": f"Bearer {kunci}", "Content-Type": "application/json", "User-Agent": "ekobbm/1.0"}


def _model_chat(kunci):
    """Menanyakan ke Groq model apa yang boleh dipakai akun ini, lalu mengurutkan yang disukai di depan."""
    with urllib.request.urlopen(urllib.request.Request(URL_MODEL, headers=_header(kunci)), timeout=20) as jawaban:
        ada = [m["id"] for m in json.loads(jawaban.read().decode("utf-8"))["data"]]
    ada = [m for m in ada if not any(k in m for k in BUKAN_CHAT)]
    return [m for m in UTAMA if m in ada] + [m for m in ada if m not in UTAMA]


def _tanya(prompt, maks_token):
    """Mengirim prompt ke Groq. Mengembalikan teks jawaban, atau None bila gagal (kunci kosong, jaringan, dan sebagainya)."""
    kunci = os.environ.get("GROQ_API_KEY")
    if not kunci:
        return None
    try:
        daftar = _model_chat(kunci)
    except Exception:
        return None
    for model in daftar[:4]:
        isi = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                          "temperature": 0.2, "max_tokens": maks_token}).encode("utf-8")
        permintaan = urllib.request.Request(URL, data=isi, method="POST", headers=_header(kunci))
        try:
            with urllib.request.urlopen(permintaan, timeout=30) as jawaban:
                teks = json.loads(jawaban.read().decode("utf-8"))["choices"][0]["message"]["content"].strip()
            if teks:
                return teks
        except Exception:
            continue
    return None


def _baca_json(teks):
    """Mengambil objek JSON dari jawaban AI. Hanya diterima bila keenam kunci ada dan berisi teks; selain itu None."""
    try:
        objek = json.loads(teks[teks.index("{"): teks.rindex("}") + 1])
        hasil = {k: str(objek[k]).strip() for k in KUNCI}
    except Exception:
        return None
    return hasil if all(hasil.values()) else None


_cache = {}


def penjelasan_grafik():
    """Mengembalikan (sumber, dict). sumber = 'ai' bila dari Groq, 'otomatis' bila memakai penjelasan cadangan."""
    if "hasil" in _cache:
        return "ai", _cache["hasil"]
    jawaban = _tanya(_prompt(), 900)
    hasil = _baca_json(jawaban) if jawaban else None
    if hasil:
        _cache["hasil"] = hasil
        return "ai", hasil
    return "otomatis", penjelasan_otomatis()