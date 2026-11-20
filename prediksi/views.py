import pandas as pd
from django.shortcuts import render
from django.http import JsonResponse

from .forms import FormMobil
from .layanan import muat_model, muat_ringkasan
from .penjelas import penjelasan_grafik

SKALA_MAKS = 20  # km/L maksimum pada meteran (data tertinggi sekitar 19,8)


def beranda(request):
    ringkasan = muat_ringkasan()
    rf = ringkasan["metrik"]["Random Forest"]
    linear = ringkasan["metrik"]["Regresi Linear"]
    konteks = {
        "jumlah_data": ringkasan["jumlah_data"],
        "r2_uji": rf["r2_uji"],
        "mae_uji": rf["mae_uji"],
        "r2_linear": linear["r2_uji"],
        "tahun_awal": int(ringkasan["rentang"]["tahun"][0]),
        "tahun_akhir": int(ringkasan["rentang"]["tahun"][1]),
    }
    return render(request, "prediksi/beranda.html", konteks)


def _kategori(km_per_liter, batas):
    if km_per_liter >= batas["irit_di_atas"]:
        return "Irit", "success"
    if km_per_liter < batas["boros_di_bawah"]:
        return "Boros", "danger"
    return "Sedang", "warning"


def _rupiah(angka):
    return "Rp " + f"{angka:,.0f}".replace(",", ".")


def prediksi(request):
    ringkasan = muat_ringkasan()
    hasil = None

    if request.method == "POST":
        form = FormMobil(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            fitur = ringkasan["fitur"]

            # kasus batas: nilai di luar rentang data latih tetap dihitung, tetapi diberi peringatan
            peringatan = []
            for nama in fitur:
                kecil, besar = ringkasan["rentang"][nama]
                if not (kecil <= data[nama] <= besar):
                    peringatan.append(f"{form.fields[nama].label.lower()} ({data[nama]}) di luar rentang data latih")

            # susun input persis seperti saat latihan: kolom dan urutan yang sama
            baris = pd.DataFrame([{nama: data[nama] for nama in fitur}])[fitur]
            km_per_liter = float(muat_model().predict(baris)[0])
            kategori, warna = _kategori(km_per_liter, ringkasan["kategori"])
            liter_per_100km = 100 / km_per_liter

            hasil = {
                "km_per_liter": round(km_per_liter, 1),
                "liter_per_100km": round(liter_per_100km, 1),
                "biaya_100km": _rupiah(liter_per_100km * data["harga_bbm"]),
                "kategori": kategori,
                "warna": warna,
                "persen": min(100, round(km_per_liter / SKALA_MAKS * 100)),
                "peringatan": peringatan,
                "mae": ringkasan["metrik"]["Random Forest"]["mae_uji"],
            }
    else:
        form = FormMobil()

    return render(request, "prediksi/prediksi.html", {"form": form, "hasil": hasil})



NAMA_FITUR = {
    "silinder": "Jumlah silinder",
    "mesin_cc": "Kapasitas mesin",
    "tenaga_hp": "Tenaga",
    "berat_kg": "Berat",
    "akselerasi_detik": "Akselerasi",
    "tahun": "Tahun",
}


def grafik(request):
    r = muat_ringkasan()

    # titik sebaran: berat (sumbu x) dan km/L (sumbu y)
    titik = [{"x": b, "y": k} for b, k in zip(r["sebaran"]["berat_kg"], r["sebaran"]["km_per_liter"])]

    # fitur diurutkan dari yang paling berpengaruh
    urut = sorted(r["pentingnya_fitur"].items(), key=lambda p: p[1], reverse=True)

    data_grafik = {
        "titik": titik,
        "silinder": {"label": [f"{k} silinder" for k in r["per_silinder"]], "nilai": list(r["per_silinder"].values())},
        "tahun": {"label": list(r["per_tahun"].keys()), "nilai": list(r["per_tahun"].values())},
        "fitur": {"label": [NAMA_FITUR[k] for k, _ in urut], "nilai": [round(v * 100, 1) for _, v in urut]},
        "batas": r["kategori"],
    }
    konteks = {
        "data_grafik": data_grafik,
        "jumlah_data": r["jumlah_data"],
        "fitur_teratas": NAMA_FITUR[urut[0][0]],
        "silinder_irit": max(r["per_silinder"], key=r["per_silinder"].get),
        "silinder_boros": min(r["per_silinder"], key=r["per_silinder"].get),
    }
    return render(request, "prediksi/grafik.html", konteks)



def penjelasan(request):
    """Dipanggil lewat JavaScript saat tombol 'Buat penjelasan' diklik; mengembalikan JSON."""
    berhasil, teks = penjelasan_grafik()
    return JsonResponse({"berhasil": berhasil, "teks": teks})