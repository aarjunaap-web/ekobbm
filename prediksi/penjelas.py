"""Meminta Groq menjelaskan grafik. Kunci API dibaca dari environment variable, tidak pernah ditulis di kode."""
import json
import os
import urllib.error
import urllib.request

from .layanan import muat_ringkasan

URL = "https://api.groq.com/openai/v1/chat/completions"
URL_MODEL = "https://api.groq.com/openai/v1/models"
UTAMA = ["llama-3.3-70b-versatile", "openai/gpt-oss-120b", "llama-3.1-8b-instant", "openai/gpt-oss-20b"]
BUKAN_CHAT = ("whisper", "guard", "tts", "orpheus", "playai", "embed")
NAMA = {"silinder": "jumlah silinder", "mesin_cc": "kapasitas mesin", "tenaga_hp": "tenaga",
        "berat_kg": "berat", "akselerasi_detik": "akselerasi", "tahun": "tahun pembuatan"}


def _header(kunci):
    return {"Authorization": f"Bearer {kunci}", "Content-Type": "application/json", "User-Agent": "ekobbm/1.0"}


def _model_chat(kunci):
    """Menanyakan ke Groq model apa saja yang boleh dipakai oleh akun ini, lalu mengurutkan yang disukai di depan."""
    permintaan = urllib.request.Request(URL_MODEL, headers=_header(kunci))
    with urllib.request.urlopen(permintaan, timeout=20) as jawaban:
        ada = [m["id"] for m in json.loads(jawaban.read().decode("utf-8"))["data"]]
    ada = [m for m in ada if not any(k in m for k in BUKAN_CHAT)]
    return [m for m in UTAMA if m in ada] + [m for m in ada if m not in UTAMA]


def _susun_data():
    """Mengubah ringkasan hasil analisis menjadi teks pendek untuk dibaca LLM."""
    r = muat_ringkasan()
    baris = [
        f"Data: {r['jumlah_data']} mobil tahun {int(r['rentang']['tahun'][0])}-{int(r['rentang']['tahun'][1])}.",
        "Rata-rata km/L menurut jumlah silinder: "
        + ", ".join(f"{k} silinder = {v}" for k, v in r["per_silinder"].items()) + ".",
        "Rata-rata km/L menurut tahun: " + ", ".join(f"{k} = {v}" for k, v in r["per_tahun"].items()) + ".",
        "Pengaruh fitur menurut Random Forest: "
        + ", ".join(f"{NAMA[k]} = {round(v * 100, 1)}%" for k, v in sorted(r["pentingnya_fitur"].items(), key=lambda p: -p[1])) + ".",
        f"Rentang berat mobil {int(r['rentang']['berat_kg'][0])}-{int(r['rentang']['berat_kg'][1])} kg; "
        "pada grafik sebaran, makin berat mobil makin kecil km/L.",
    ]
    return "\n".join(baris)


def _prompt():
    return (
        "Kamu menjelaskan grafik pada website prediksi efisiensi BBM mobil kepada pengunjung awam. "
        "Gunakan HANYA angka pada data di bawah, jangan menambah angka lain. "
        "Tulis dalam bahasa Indonesia yang sederhana, tepat 4 poin, tiap poin satu kalimat atau dua kalimat, "
        "diawali tanda '- ' dan tanpa format markdown lain. "
        "Poin: (1) hubungan berat dengan km/L, (2) perbandingan jumlah silinder, (3) tren menurut tahun, "
        "(4) fitur paling berpengaruh dan satu catatan bahwa fitur saling berkaitan.\n\n"
        "DATA:\n" + _susun_data()
    )


_cache = {}


def penjelasan_grafik():
    """Mengembalikan (berhasil, teks). Hasil sukses disimpan agar tidak memanggil API berulang."""
    if "teks" in _cache:
        return True, _cache["teks"]

    kunci = os.environ.get("GROQ_API_KEY")
    if not kunci:
        return False, "Kunci GROQ_API_KEY belum diatur di komputer ini, sehingga penjelasan otomatis belum bisa dibuat."

    galat_terakhir = ""
    try:
        daftar_model = _model_chat(kunci)
    except urllib.error.HTTPError as e:
        return False, f"Kunci ditolak atau tidak bisa dipakai (HTTP {e.code}). Periksa kembali GROQ_API_KEY."
    except Exception as e:
        return False, f"Tidak bisa menghubungi Groq ({type(e).__name__}). Periksa koneksi internet."

    for model in daftar_model[:4]:
        isi = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": _prompt()}],
            "temperature": 0.3,
        }).encode("utf-8")
        permintaan = urllib.request.Request(URL, data=isi, method="POST", headers=_header(kunci))
        try:
            with urllib.request.urlopen(permintaan, timeout=30) as jawaban:
                teks = json.loads(jawaban.read().decode("utf-8"))["choices"][0]["message"]["content"].strip()
            _cache["teks"] = teks
            return True, teks
        except urllib.error.HTTPError as e:
            pesan = e.read().decode("utf-8", "ignore")[:150]
            galat_terakhir = f"{model}: HTTP {e.code} {pesan}"
        except Exception as e:  # jaringan putus, waktu habis, dan sebagainya
            galat_terakhir = f"{model}: {type(e).__name__}"
    return False, f"Penjelasan otomatis gagal dibuat ({galat_terakhir})."