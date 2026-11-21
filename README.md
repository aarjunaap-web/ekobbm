# EkoBBM

Website untuk mengecek seberapa irit sebuah mobil dan berapa biaya BBM-nya. Pengunjung memilih merek, model, dan tahun; website memperkirakan konsumsi dalam km per liter (km/L), membandingkannya dengan ribuan mobil lain, dan menghitung biaya bulanan.

Website: https://ekobbm.vercel.app

Proyek individu mata kuliah Sistem Cerdas, Politeknik Negeri Madiun.
Pembuat: Arjuna Anggara Putra (NIM 253307052).

## Fitur

| Halaman | Isi |
|---|---|
| Hitung | Prediksi km/L oleh model *machine learning*, peringkat Irit / Sedang / Boros, kisaran wajar, dan biaya BBM per bulan |
| Wawasan | Enam grafik (Chart.js), masing-masing dengan cara membaca dan penjelasan dari AI (Groq) |
| Data | Tabel 25.920 varian mobil yang bisa dicari, difilter, diurutkan, dan dibagi per halaman |
| Tentang | Sumber data, cara hitung, akurasi model, dan batasan |

Tiga syarat tugas dipenuhi sebagai berikut:
1. **Model ML:** Gradient Boosting memprediksi km/L (halaman Hitung).
2. **Grafik:** enam grafik di halaman Wawasan.
3. **LLM:** Groq (Llama) menjelaskan tiap grafik. Bila Groq tidak tersedia, dipakai penjelasan otomatis dari data dan lencana di halaman menyebutkannya.

## Data

- Sumber: EPA (Environmental Protection Agency) dan DOE (Department of Energy) Amerika Serikat, berkas `vehicles.csv` dari https://fueleconomy.gov/feg/download.shtml
- Berkas mentah tidak disertakan di repositori (lihat `.gitignore`). Unduh sendiri dan taruh di `data/vehicles.csv` bila ingin melatih ulang model.
- Pembersihan: hanya bensin, diesel, dan hybrid biasa; tahun 2000 ke atas; baris ganda dibuang; merek dengan kurang dari 100 baris dibuang; satuan mil per galon diubah ke km per liter (dikali 0,425144).
- Hasil: 25.920 varian, 42 merek, 792 model, tahun 2000 sampai 2027.

## Model

Variabel masukan: merek, model, jenis mobil, transmisi, penggerak roda, turbo, hybrid, diesel, tahun, jumlah silinder, ukuran mesin. Target: km/L (dilatih dalam skala logaritma).

Data dibagi 80% untuk belajar dan 20% untuk menguji.

| Model | R² | Rata-rata meleset | 80% tebakan meleset kurang dari |
|---|---|---|---|
| Regresi linear (Ridge), pembanding | 0,902 | 0,55 km/L (5,8%) | 9,3% |
| Gradient Boosting (dipakai) | 0,965 | 0,34 km/L (3,6%) | 5,7% |

Model akhir dilatih ulang dengan seluruh data lalu disimpan ke `prediksi/ml/model_efisiensi.joblib`.

## Struktur proyek

```
website_bbm/
├── latih_model.py          # membaca data, melatih model, menyimpan hasil ke prediksi/ml/
├── manage.py
├── pyproject.toml          # daftar paket dengan versi tetap (dibaca Vercel)
├── config/settings.py      # pengaturan Django (aman untuk lokal dan Vercel)
└── prediksi/
    ├── views.py            # beranda, hitung, wawasan, data, tentang, dan endpoint JSON
    ├── forms.py            # formulir Hitung dan validasinya
    ├── layanan.py          # memuat model, ringkasan, dan katalog (di-cache)
    ├── penjelas.py         # penjelasan grafik oleh Groq + cadangan otomatis
    ├── urls.py
    ├── ml/                 # model_efisiensi.joblib, katalog.json, ringkasan.json
    ├── templates/prediksi/ # halaman HTML
    └── static/prediksi/    # css dan javascript
```

## Menjalankan di komputer sendiri

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install django scikit-learn pandas numpy scipy joblib
python manage.py runserver
```

Buka http://127.0.0.1:8000/

Agar penjelasan grafik ditulis AI, isi kunci Groq di terminal (jangan di dalam kode):

```powershell
$env:GROQ_API_KEY="isi-kunci-kamu"
```

Tanpa kunci, situs tetap berjalan dengan penjelasan otomatis.

Melatih ulang model (perlu `data/vehicles.csv`):

```powershell
python latih_model.py
```

## Deploy

Repositori terhubung ke Vercel. Push ke `main` memasang versi baru ke alamat utama; cabang lain mendapat tautan pratinjau. Environment Variables di Vercel: `GROQ_API_KEY` dan `SECRET_KEY`.

## Batasan

- Data berasal dari mobil yang dijual di Amerika Serikat; banyak mobil khas Indonesia tidak ada.
- Angka hasil uji standar EPA, bukan kondisi jalan sebenarnya.
- Mengubah spesifikasi menghasilkan simulasi, bukan angka uji.
- Penjelasan AI bisa keliru menyusun kalimat; grafik tetap menjadi acuan.

## Teknologi

Python, Django, pandas, scikit-learn, Chart.js, Bootstrap, Groq (Llama), Vercel.

## Kredit

Data konsumsi BBM: U.S. Environmental Protection Agency dan U.S. Department of Energy (fueleconomy.gov).
