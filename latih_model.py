"""Menyiapkan data EPA, melatih model konsumsi BBM, dan menyimpan hasilnya untuk website.

Jalankan sekali (atau setiap data/model diubah):  python latih_model.py
Masukan : data/vehicles.csv  (dari fueleconomy.gov, "All model years" - CSV)
Keluaran: prediksi/ml/model_efisiensi.joblib, ringkasan.json, katalog.json
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler

FOLDER = Path(__file__).resolve().parent
FILE_MENTAH = FOLDER / "data" / "vehicles.csv"
FOLDER_ML = FOLDER / "prediksi" / "ml"
MPG_KE_KML = 0.425144          # 1 mile per gallon = 0,425144 km per liter
TAHUN_AWAL = 2000
MIN_BARIS_MEREK = 100          # merek dengan data lebih sedikit tidak dipakai

KATEGORI = ["merek", "model", "kelas", "transmisi", "penggerak", "turbo", "hybrid", "diesel"]
ANGKA = ["tahun", "silinder", "mesin_liter"]
FITUR = KATEGORI + ANGKA


def kelas_mobil(teks):
    """Menyederhanakan 25 jenis kelas EPA menjadi 10 kelas yang mudah dipahami."""
    if "Minicompact" in teks or "Subcompact" in teks:
        return "Mobil kecil"
    if "Two Seaters" in teks:
        return "Mobil 2 kursi"
    if "Compact Cars" in teks:
        return "Mobil kompak"
    if "Midsize Cars" in teks:
        return "Sedan menengah"
    if "Large Cars" in teks:
        return "Sedan besar"
    if "Station Wagons" in teks:
        return "Station wagon"
    if "Small Sport Utility" in teks:
        return "SUV kecil"
    if "Sport Utility" in teks:
        return "SUV besar"
    if "Pickup" in teks:
        return "Pickup"
    if "Minivan" in teks or "Vans" in teks:
        return "Van / MPV"
    return "Lainnya"


def penggerak(teks):
    if pd.isna(teks):
        return "Tidak diketahui"
    if "Front" in teks:
        return "Roda depan"
    if "Rear" in teks:
        return "Roda belakang"
    return "4x4 / AWD"


# ---------- 1. baca dan bersihkan ----------
mentah = pd.read_csv(FILE_MENTAH, low_memory=False)
jumlah_mentah = len(mentah)

bensin_diesel = ["Regular Gasoline", "Premium Gasoline", "Midgrade Gasoline", "Diesel"]
m = mentah[
    mentah["fuelType1"].isin(bensin_diesel)                       # bukan listrik / hidrogen / gas
    & mentah["fuelType2"].isna()                                  # bukan bahan bakar ganda
    & ~mentah["atvType"].isin(["Plug-in Hybrid", "EV", "CNG"])
    & (mentah["year"] >= TAHUN_AWAL)
    & mentah[["displ", "cylinders", "trany"]].notna().all(axis=1)
].copy()

d = pd.DataFrame({
    "merek": m["make"],
    "model": m["baseModel"],
    "kelas": m["VClass"].map(kelas_mobil),
    "tahun": m["year"],
    "silinder": m["cylinders"].astype(int),
    "mesin_liter": m["displ"],
    "transmisi": np.where(m["trany"].str.startswith("Automatic"), "Otomatis", "Manual"),
    "penggerak": m["drive"].map(penggerak),
    "turbo": np.where((m["tCharger"] == True) | m["sCharger"].notna(), "Ya", "Tidak"),
    "hybrid": np.where(m["atvType"] == "Hybrid", "Ya", "Tidak"),
    "diesel": np.where(m["fuelType1"] == "Diesel", "Ya", "Tidak"),
    "kml": m["comb08"] * MPG_KE_KML,              # konsumsi gabungan, km per liter
    "kml_kota": m["city08"] * MPG_KE_KML,
    "kml_tol": m["highway08"] * MPG_KE_KML,
})
d = d.drop_duplicates()
d = d[d.groupby("merek")["kml"].transform("size") >= MIN_BARIS_MEREK].reset_index(drop=True)
print(f"Data: {jumlah_mentah} baris mentah -> {len(d)} setelah dibersihkan, {d['merek'].nunique()} merek, {d['model'].nunique()} model")

# ---------- 2. latih dan bandingkan ----------
X = d[FITUR]
y = np.log(d["kml"])
X_latih, X_uji, y_latih, y_uji = train_test_split(X, y, test_size=0.2, random_state=42)


def hasil(nama, pipa):
    pipa.fit(X_latih, y_latih)
    asli = np.exp(y_uji)
    tebak = np.exp(pipa.predict(X_uji))
    persen = np.abs(tebak - asli) / asli * 100
    r = {
        "r2_uji": round(r2_score(asli, tebak), 3),
        "mae_kml": round(mean_absolute_error(asli, tebak), 2),
        "mape": round(float(persen.mean()), 1),
        "persen_80": round(float(np.percentile(persen, 80)), 1),   # 80% tebakan meleset kurang dari ini
    }
    print(nama, r)
    return r


pipa_linear = Pipeline([
    ("p", ColumnTransformer([("c", OneHotEncoder(handle_unknown="ignore"), KATEGORI),
                             ("n", StandardScaler(), ANGKA)])),
    ("m", Ridge(alpha=1.0)),
])
pipa_hgb = Pipeline([
    ("p", ColumnTransformer([("c", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), KATEGORI)],
                            remainder="passthrough")),
    ("m", HistGradientBoostingRegressor(max_iter=500, learning_rate=0.08, random_state=42)),
])
metrik = {"Regresi Linear (Ridge)": hasil("Ridge", pipa_linear), "Gradient Boosting": hasil("Gradient Boosting", pipa_hgb)}

pi = permutation_importance(pipa_hgb, X_uji, y_uji, n_repeats=5, random_state=42)
penting = np.clip(pi.importances_mean, 0, None)
penting = penting / penting.sum()

# ---------- 3. latih ulang dengan semua data dan simpan ----------
pipa_hgb.fit(X, y)
FOLDER_ML.mkdir(parents=True, exist_ok=True)
joblib.dump(pipa_hgb, FOLDER_ML / "model_efisiensi.joblib", compress=3)

# ---------- 4. katalog pilihan untuk formulir: merek -> model -> tahun -> varian ----------
katalog = {}
for r in d.itertuples(index=False):
    varian = [round(r.mesin_liter, 1), r.silinder, r.transmisi, r.penggerak, r.turbo, r.hybrid, r.diesel,
              r.kelas, round(r.kml, 1), round(r.kml_kota, 1), round(r.kml_tol, 1)]
    katalog.setdefault(r.merek, {}).setdefault(r.model, {}).setdefault(str(r.tahun), []).append(varian)
katalog = {mk: dict(sorted(md.items())) for mk, md in sorted(katalog.items())}
(FOLDER_ML / "katalog.json").write_text(json.dumps(katalog, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

# ---------- 5. ringkasan untuk grafik dan halaman ----------
per_merek = d.groupby("merek")["kml"].agg(["median", "size"]).query("size >= 300").sort_values("median", ascending=False)
per_kelas = d.groupby("kelas")["kml"].median().sort_values(ascending=False)
per_tahun = d.groupby("tahun")["kml"].mean()
per_silinder = d[d["silinder"].isin([3, 4, 5, 6, 8, 10, 12])].groupby("silinder")["kml"].mean()
contoh = d.sample(600, random_state=1)
persentil = [round(float(v), 2) for v in np.percentile(d["kml"], np.arange(0, 101))]   # untuk "lebih irit dari X% mobil"

ringkasan = {
    "jumlah_data": int(len(d)),
    "jumlah_merek": int(d["merek"].nunique()),
    "jumlah_model": int(d["model"].nunique()),
    "fitur": FITUR,
    "rentang": {"tahun": [int(d["tahun"].min()), int(d["tahun"].max())],
                "mesin_liter": [float(d["mesin_liter"].min()), float(d["mesin_liter"].max())],
                "kml": [round(float(d["kml"].min()), 1), round(float(d["kml"].max()), 1)]},
    "kml_median": round(float(d["kml"].median()), 1),
    "persentil_kml": persentil,
    "metrik": metrik,
    "pentingnya_fitur": {f: round(float(v), 3) for f, v in zip(FITUR, penting)},
    "per_merek": {"label": list(per_merek.index[:10]), "kml": [round(v, 1) for v in per_merek["median"][:10]],
                  "label_boros": list(per_merek.index[-5:]), "kml_boros": [round(v, 1) for v in per_merek["median"][-5:]]},
    "per_kelas": {"label": list(per_kelas.index), "kml": [round(v, 1) for v in per_kelas.values]},
    "per_tahun": {"label": [int(t) for t in per_tahun.index], "kml": [round(v, 2) for v in per_tahun.values]},
    "per_silinder": {"label": [int(s) for s in per_silinder.index], "kml": [round(v, 1) for v in per_silinder.values]},
    "sebaran": {"mesin_liter": [round(v, 1) for v in contoh["mesin_liter"]], "kml": [round(v, 1) for v in contoh["kml"]]},
}
(FOLDER_ML / "ringkasan.json").write_text(json.dumps(ringkasan, ensure_ascii=False), encoding="utf-8")
print("Selesai. Model, katalog, dan ringkasan tersimpan di prediksi/ml/")