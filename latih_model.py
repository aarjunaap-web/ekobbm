"""Melatih model efisiensi BBM dan menyimpan hasilnya untuk website Django.

Jalankan sekali dari folder website_bbm:   python latih_model.py
Hasil:
  data/auto_mpg.csv            salinan dataset (Auto MPG, UCI Machine Learning Repository)
  prediksi/ml/model_bbm.joblib model yang sudah dilatih
  prediksi/ml/ringkasan.json   metrik, rentang data, dan data grafik untuk halaman web
"""
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split

FOLDER = Path(__file__).resolve().parent
FILE_DATA = FOLDER / "data" / "auto_mpg.csv"
FOLDER_MODEL = FOLDER / "prediksi" / "ml"
URL_DATA = "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/mpg.csv"

# --- 1. Membaca data (unduh sekali, lalu pakai salinan lokal) ---
FILE_DATA.parent.mkdir(exist_ok=True)
FOLDER_MODEL.mkdir(parents=True, exist_ok=True)
if not FILE_DATA.exists():
    pd.read_csv(URL_DATA).to_csv(FILE_DATA, index=False)
df = pd.read_csv(FILE_DATA)

# --- 2. Membersihkan dan mengubah satuan agar mudah dibaca ---
df["horsepower"] = df["horsepower"].fillna(df["horsepower"].median())   # 6 data kosong
data = pd.DataFrame({
    "silinder": df["cylinders"],
    "mesin_cc": df["displacement"] * 16.387,      # inci kubik -> cc
    "tenaga_hp": df["horsepower"],
    "berat_kg": df["weight"] * 0.45359,           # pon -> kg
    "akselerasi_detik": df["acceleration"],       # detik untuk 0-60 mph
    "tahun": df["model_year"] + 1900,
    "asal": df["origin"],
    "km_per_liter": df["mpg"] * 0.425144,         # mil per galon -> km per liter
})
FITUR = ["silinder", "mesin_cc", "tenaga_hp", "berat_kg", "akselerasi_detik", "tahun"]
X, y = data[FITUR], data["km_per_liter"]

# --- 3. Membagi data, melatih dua model, lalu membandingkan ---
X_latih, X_uji, y_latih, y_uji = train_test_split(X, y, test_size=0.25, random_state=42)
calon = {
    "Regresi Linear": LinearRegression(),
    "Random Forest": RandomForestRegressor(n_estimators=300, min_samples_leaf=2, random_state=42),
}
hasil = {}
for nama, model in calon.items():
    model.fit(X_latih, y_latih)
    hasil[nama] = {
        "r2_latih": round(model.score(X_latih, y_latih), 3),
        "r2_uji": round(model.score(X_uji, y_uji), 3),
        "mae_uji": round(mean_absolute_error(y_uji, model.predict(X_uji)), 2),
    }
    print(nama, hasil[nama])

# --- 4. Model akhir: Random Forest dilatih ulang dengan seluruh data ---
model_akhir = RandomForestRegressor(n_estimators=300, min_samples_leaf=2, random_state=42)
model_akhir.fit(X, y)
joblib.dump(model_akhir, FOLDER_MODEL / "model_bbm.joblib")

# --- 5. Ringkasan untuk halaman web (rentang input, grafik, kategori) ---
batas_boros, batas_irit = y.quantile([1 / 3, 2 / 3]).round(1)
sampel = data.sample(120, random_state=7)
ringkasan = {
    "jumlah_data": int(len(data)),
    "fitur": FITUR,
    "rentang": {f: [round(float(X[f].min()), 1), round(float(X[f].max()), 1)] for f in FITUR},
    "rata_rata": {f: round(float(X[f].mean()), 1) for f in FITUR},
    "metrik": hasil,
    "pentingnya_fitur": {f: round(float(v), 3) for f, v in zip(FITUR, model_akhir.feature_importances_)},
    "kategori": {"boros_di_bawah": float(batas_boros), "irit_di_atas": float(batas_irit)},
    "sebaran": {"berat_kg": sampel["berat_kg"].round(0).tolist(),
                "km_per_liter": sampel["km_per_liter"].round(2).tolist()},
    "per_silinder": data.groupby("silinder")["km_per_liter"].mean().round(2).to_dict(),
    "per_asal": data.groupby("asal")["km_per_liter"].mean().round(2).to_dict(),
    "per_tahun": data.groupby("tahun")["km_per_liter"].mean().round(2).to_dict(),
}
(FOLDER_MODEL / "ringkasan.json").write_text(json.dumps(ringkasan, indent=2, ensure_ascii=False), encoding="utf-8")
print("Selesai. Model dan ringkasan tersimpan di", FOLDER_MODEL)