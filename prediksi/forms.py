from django import forms

from .layanan import daftar_merek, daftar_model, daftar_tahun

KELAS = ["Mobil kecil", "Mobil kompak", "Sedan menengah", "Sedan besar", "Station wagon", "SUV kecil",
         "SUV besar", "Pickup", "Van / MPV", "Mobil 2 kursi", "Lainnya"]
YA_TIDAK = [("Tidak", "Tidak"), ("Ya", "Ya")]


def _pilihan(daftar):
    return [(x, x) for x in daftar]


class FormHitung(forms.Form):
    merek = forms.ChoiceField(label="Merek", widget=forms.Select(attrs={"class": "form-select"}))
    model = forms.ChoiceField(label="Model", widget=forms.Select(attrs={"class": "form-select"}))
    tahun = forms.TypedChoiceField(label="Tahun", coerce=int, widget=forms.Select(attrs={"class": "form-select"}))

    kelas = forms.ChoiceField(
        label="Jenis mobil", choices=_pilihan(KELAS), initial="Mobil kompak",
        widget=forms.Select(attrs={"class": "form-select"}))
    mesin_liter = forms.FloatField(
        label="Ukuran mesin (liter)", min_value=0.6, max_value=8.5, initial=1.6,
        help_text="Mesin 1.500 cc sama dengan 1,5 liter.",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": 0.1}))
    silinder = forms.TypedChoiceField(
        label="Jumlah silinder", coerce=int, initial=4,
        choices=[(n, f"{n} silinder") for n in (2, 3, 4, 5, 6, 8, 10, 12, 16)],
        help_text="Mobil kecil biasanya 3 atau 4 silinder.",
        widget=forms.Select(attrs={"class": "form-select"}))
    transmisi = forms.ChoiceField(
        label="Transmisi", choices=_pilihan(["Otomatis", "Manual"]),
        widget=forms.Select(attrs={"class": "form-select"}))
    penggerak = forms.ChoiceField(
        label="Penggerak roda", choices=_pilihan(["Roda depan", "Roda belakang", "4x4 / AWD", "Tidak diketahui"]),
        widget=forms.Select(attrs={"class": "form-select"}))
    turbo = forms.ChoiceField(label="Turbo", choices=YA_TIDAK, widget=forms.Select(attrs={"class": "form-select"}))
    hybrid = forms.ChoiceField(label="Hybrid", choices=YA_TIDAK, widget=forms.Select(attrs={"class": "form-select"}))
    diesel = forms.ChoiceField(label="Mesin diesel", choices=YA_TIDAK, widget=forms.Select(attrs={"class": "form-select"}))

    jarak_bulan = forms.IntegerField(
        label="Jarak tempuh per bulan (km)", min_value=50, max_value=20000, initial=1000,
        help_text="Perkiraan saja. Contoh: 30 km per hari sekitar 900 km per bulan.",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": 50}))
    harga_bbm = forms.IntegerField(
        label="Harga BBM per liter (Rp)", min_value=1000, max_value=50000, initial=10000,
        help_text="Isi sesuai harga BBM yang kamu pakai.",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": 100}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["merek"].choices = [("", "Pilih merek")] + _pilihan(daftar_merek())
        self.fields["model"].choices = [("", "Pilih merek dulu")]
        self.fields["tahun"].choices = [("", "Pilih model dulu")]
        # setelah formulir dikirim: isi menu model dan tahun sesuai pilihan sebelumnya
        if self.is_bound:
            merek = self.data.get("merek", "")
            model = self.data.get("model", "")
            if merek in daftar_merek():
                self.fields["model"].choices = [("", "Pilih model")] + _pilihan(daftar_model(merek))
                if model in daftar_model(merek):
                    self.fields["tahun"].choices = [("", "Pilih tahun")] + [(t, t) for t in daftar_tahun(merek, model)]

    def clean(self):
        data = super().clean()
        if data.get("merek") and data.get("model") and data.get("tahun"):
            if data["tahun"] not in daftar_tahun(data["merek"], data["model"]):
                self.add_error("tahun", "Tahun ini tidak ada untuk model tersebut.")
        return data