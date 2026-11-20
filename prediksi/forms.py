from django import forms

from .layanan import muat_ringkasan


def _ribuan(angka):
    """1114.3 -> '1.114' (titik sebagai pemisah ribuan)."""
    return f"{angka:,.0f}".replace(",", ".")


class FormMobil(forms.Form):
    silinder = forms.TypedChoiceField(
        label="Jumlah silinder",
        choices=[(n, f"{n} silinder") for n in (3, 4, 5, 6, 8)],
        coerce=int, initial=4,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    mesin_cc = forms.IntegerField(
        label="Kapasitas mesin (cc)", min_value=500, max_value=8000, initial=1600,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": 50}),
    )
    tenaga_hp = forms.IntegerField(
        label="Tenaga (hp)", min_value=30, max_value=400, initial=90,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    berat_kg = forms.IntegerField(
        label="Berat kendaraan (kg)", min_value=500, max_value=3500, initial=1000,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": 10}),
    )
    akselerasi_detik = forms.FloatField(
        label="Akselerasi 0-60 mph (detik)", min_value=5, max_value=30, initial=15,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": 0.1}),
    )
    tahun = forms.IntegerField(
        label="Tahun pembuatan", min_value=1960, max_value=2030, initial=1978,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    # bukan masukan model, hanya untuk menghitung biaya per 100 km
    harga_bbm = forms.IntegerField(
        label="Harga BBM per liter (Rp)", min_value=1000, max_value=50000, initial=10000,
        help_text="Bisa diubah sesuai harga BBM yang dipakai.",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": 500}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        rentang = muat_ringkasan()["rentang"]
        for nama, (kecil, besar) in rentang.items():
            if nama == "silinder" or nama not in self.fields:
                continue
            if nama == "tahun":                      # tahun tidak diberi pemisah ribuan
                teks = f"{int(kecil)} sampai {int(besar)}"
            else:
                teks = f"{_ribuan(kecil)} sampai {_ribuan(besar)}"
            self.fields[nama].help_text = "Rentang data latih: " + teks