from bisect import bisect_right

import numpy as np
import pandas as pd
from django.http import JsonResponse
from django.shortcuts import render

from .forms import FormHitung
from .layanan import (angka_resmi, daftar_model, daftar_tahun, daftar_varian, muat_model, muat_ringkasan)
from .penjelas import NAMA_FITUR, _kecil, penjelasan_wawasan

def _rupiah(angka):
    return "Rp" + f"{angka:,.0f}".replace(",", ".")


def _koma(angka, desimal=1):
    return f"{angka:.{desimal}f}".replace(".", ",")


def beranda(request):
    r = muat_ringkasan()
    kelas = r["per_kelas"]
    silinder = dict(zip(r["per_silinder"]["label"], r["per_silinder"]["kml"]))
    konteks = {
        "jumlah_data": f"{r['jumlah_data']:,}".replace(",", "."),
        "jumlah_merek": r["jumlah_merek"],
        "jumlah_model": r["jumlah_model"],
        "tahun_awal": r["rentang"]["tahun"][0],
        "tahun_akhir": r["rentang"]["tahun"][1],
        "kelas_irit": list(zip(kelas["label"][:3], [_koma(v) for v in kelas["kml"][:3]])),
        "kelas_boros": list(zip(kelas["label"][-3:][::-1], [_koma(v) for v in kelas["kml"][-3:][::-1]])),
        "silinder_4": _koma(silinder[4]),
        "silinder_8": _koma(silinder[8]),
        "selisih_silinder": _koma(silinder[4] / silinder[8]),
        "pengaruh_mesin": round(r["pentingnya_fitur"]["mesin_liter"] * 100),
        "kml_awal": _koma(r["per_tahun"]["kml"][0]),
        "kml_akhir": _koma(r["per_tahun"]["kml"][-1]),
    }
    return render(request, "prediksi/beranda.html", konteks)


def _kategori(peringkat):
    """peringkat = persen mobil dalam data yang kalah irit dari mobil ini."""
    if peringkat >= 67:
        return "Irit", "success"
    if peringkat < 33:
        return "Boros", "danger"
    return "Sedang", "warning"


def hitung(request):
    r = muat_ringkasan()
    hasil = None

    if request.method == "POST":
        form = FormHitung(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            baris = pd.DataFrame([{
                "merek": d["merek"], "model": d["model"], "kelas": d["kelas"], "transmisi": d["transmisi"],
                "penggerak": d["penggerak"], "turbo": d["turbo"], "hybrid": d["hybrid"], "diesel": d["diesel"],
                "tahun": d["tahun"], "silinder": d["silinder"], "mesin_liter": d["mesin_liter"],
            }])[r["fitur"]]
            kml = float(np.exp(muat_model().predict(baris)[0]))

            peringkat = max(0, bisect_right(r["persentil_kml"], kml) - 1)   # 0 sampai 100
            kategori, warna = _kategori(peringkat)
            liter_100 = 100 / kml
            selisih = r["metrik"]["Gradient Boosting"]["persen_80"] / 100
            spek = {k: d[k] for k in ("mesin_liter", "silinder", "transmisi", "penggerak", "turbo", "hybrid", "diesel", "kelas")}
            spek["mesin_liter"] = round(spek["mesin_liter"], 1)
            resmi = angka_resmi(d["merek"], d["model"], d["tahun"], spek)

            hasil = {
                "nama": f"{d['merek']} {d['model']} {d['tahun']}",
                "kml": _koma(kml),
                "kategori": kategori,
                "warna": warna,
                "peringkat": peringkat,
                "lebih_irit_dari": peringkat,
                "liter_100": _koma(liter_100),
                "biaya_100": _rupiah(liter_100 * d["harga_bbm"]),
                "liter_bulan": _koma(d["jarak_bulan"] / kml),
                "biaya_bulan": _rupiah(d["jarak_bulan"] / kml * d["harga_bbm"]),
                "jarak_bulan": f"{d['jarak_bulan']:,}".replace(",", "."),
                "kisaran": f"{_koma(kml / (1 + selisih))} sampai {_koma(kml * (1 + selisih))}",
                "persen_selisih": _koma(selisih * 100, 0),
                "resmi": None if resmi is None else {k: _koma(v) for k, v in resmi.items()},
            }
    else:
        form = FormHitung()

    return render(request, "prediksi/hitung.html", {"form": form, "hasil": hasil})


# ---------- jawaban JSON untuk menu bertingkat (dipanggil JavaScript) ----------
def api_model(request):
    merek = request.GET.get("merek", "")
    return JsonResponse({"daftar": daftar_model(merek)})


def api_tahun(request):
    return JsonResponse({"daftar": daftar_tahun(request.GET.get("merek", ""), request.GET.get("model", ""))})


def api_varian(request):
    try:
        tahun = int(request.GET.get("tahun", ""))
    except ValueError:
        return JsonResponse({"daftar": []})
    return JsonResponse({"daftar": daftar_varian(request.GET.get("merek", ""), request.GET.get("model", ""), tahun)})



# ---------- halaman Wawasan ----------
def wawasan(request):
    r = muat_ringkasan()
    pk = r["persentil_kml"]
    silinder = dict(zip(r["per_silinder"]["label"], r["per_silinder"]["kml"]))
    urut = sorted(r["pentingnya_fitur"].items(), key=lambda p: -p[1])

    data_grafik = {
        # batas warna: di bawah "boros" = merah, di atas "irit" = hijau, di antaranya kuning
        "batas": {"boros": pk[33], "irit": pk[67]},
        "sebaran": [{"x": x, "y": y} for x, y in zip(r["sebaran"]["mesin_liter"], r["sebaran"]["kml"])],
        "silinder": {"label": [f"{s} silinder" for s in r["per_silinder"]["label"]], "nilai": r["per_silinder"]["kml"]},
        "tahun": {"label": r["per_tahun"]["label"], "nilai": r["per_tahun"]["kml"]},
        "kelas": {"label": r["per_kelas"]["label"], "nilai": r["per_kelas"]["kml"]},
        "merek": {"label": r["per_merek"]["label"], "nilai": r["per_merek"]["kml"]},
        "faktor": {"label": [NAMA_FITUR[k].capitalize() for k, _ in urut], "nilai": [round(v * 100, 1) for _, v in urut]},
    }
    konteks = {
        "data_grafik": data_grafik,
        "jumlah_data": f"{r['jumlah_data']:,}".replace(",", "."),
        "judul_silinder": f"Mobil 4 silinder {_koma(silinder[4])} km/L, 8 silinder hanya {_koma(silinder[8])} km/L",
        "judul_tahun": f"Rata-rata naik dari {_koma(r['per_tahun']['kml'][0])} ke {_koma(r['per_tahun']['kml'][-1])} km/L sejak {r['per_tahun']['label'][0]}",
        "judul_kelas": f"{r['per_kelas']['label'][0]} paling irit, {_kecil(r['per_kelas']['label'][-1])} paling boros",
        "judul_merek": f"{r['per_merek']['label'][0]} dan {r['per_merek']['label'][1]} paling irit secara rata-rata",
        "judul_faktor": f"{NAMA_FITUR[urut[0][0]].capitalize()} paling menentukan ({round(urut[0][1] * 100)}%)",
    }
    return render(request, "prediksi/wawasan.html", konteks)


def wawasan_penjelasan(request):
    """Dipanggil JavaScript saat halaman Wawasan dibuka; mengembalikan ringkasan sebagai JSON."""
    sumber, teks = penjelasan_wawasan()
    return JsonResponse({"sumber": sumber, "teks": teks})