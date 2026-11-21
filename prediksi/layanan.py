"""Fungsi pembantu: memuat model, ringkasan, dan katalog (dibaca sekali lalu disimpan di memori)."""
import json
from functools import lru_cache
from pathlib import Path

import joblib

FOLDER_ML = Path(__file__).resolve().parent / "ml"


@lru_cache(maxsize=1)
def muat_ringkasan():
    return json.loads((FOLDER_ML / "ringkasan.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def muat_katalog():
    return json.loads((FOLDER_ML / "katalog.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def muat_model():
    return joblib.load(FOLDER_ML / "model_efisiensi.joblib")


def daftar_merek():
    return list(muat_katalog().keys())


def daftar_model(merek):
    return list(muat_katalog().get(merek, {}).keys())


def daftar_tahun(merek, model):
    tahun = muat_katalog().get(merek, {}).get(model, {})
    return sorted((int(t) for t in tahun), reverse=True)


# urutan nilai pada tiap varian di katalog.json
POSISI = ["mesin_liter", "silinder", "transmisi", "penggerak", "turbo", "hybrid", "diesel", "kelas", "kml", "kml_kota", "kml_tol"]


def daftar_varian(merek, model, tahun):
    """Varian unik (mesin, transmisi, dan seterusnya) untuk satu mobil pada satu tahun."""
    hasil, terlihat = [], set()
    for v in muat_katalog().get(merek, {}).get(model, {}).get(str(tahun), []):
        v = dict(zip(POSISI, v))
        kunci = tuple(v[k] for k in POSISI[:8])
        if kunci in terlihat:
            continue
        terlihat.add(kunci)
        nama = f"{v['mesin_liter']:.1f} L, {v['silinder']} silinder, {v['transmisi'].lower()}, {v['penggerak'].lower()}"
        for kunci_ekstra, teks in (("turbo", "turbo"), ("hybrid", "hybrid"), ("diesel", "diesel")):
            if v[kunci_ekstra] == "Ya":
                nama += ", " + teks
        v["label"] = nama.replace(".", ",")
        hasil.append(v)
    hasil.sort(key=lambda v: (v["mesin_liter"], v["label"]))
    return hasil


def angka_resmi(merek, model, tahun, spek):
    """Angka EPA untuk mobil yang spesifikasinya persis sama (None bila tidak ada yang cocok)."""
    cocok = []
    for v in muat_katalog().get(merek, {}).get(model, {}).get(str(tahun), []):
        v = dict(zip(POSISI, v))
        if all(v[k] == spek[k] for k in POSISI[:8]):
            cocok.append(v)
    if not cocok:
        return None
    rata = lambda kunci: sum(v[kunci] for v in cocok) / len(cocok)
    return {"kml": rata("kml"), "kota": rata("kml_kota"), "tol": rata("kml_tol")}