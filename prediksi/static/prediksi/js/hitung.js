// Menu bertingkat: merek -> model -> tahun -> varian. Data diminta ke server (Django) lewat fetch.
const formulir = document.getElementById("formHitung");
const merek = document.getElementById("id_merek");
const model = document.getElementById("id_model");
const tahun = document.getElementById("id_tahun");
const varian = document.getElementById("varian");

// kolom spesifikasi yang diisi otomatis dari varian: nama kolom Django -> kunci pada data varian
const KOLOM = {
    id_kelas: "kelas", id_mesin_liter: "mesin_liter", id_silinder: "silinder", id_transmisi: "transmisi",
    id_penggerak: "penggerak", id_turbo: "turbo", id_hybrid: "hybrid", id_diesel: "diesel",
};
let daftarVarian = [];

async function ambil(url, parameter) {
    const jawaban = await fetch(url + "?" + new URLSearchParams(parameter));
    return (await jawaban.json()).daftar;
}

function isiMenu(menu, daftar, teksAwal) {
    menu.innerHTML = "";
    menu.add(new Option(teksAwal, ""));
    daftar.forEach(x => menu.add(new Option(x, x)));
}

function isiSpesifikasi(v) {
    for (const [id, kunci] of Object.entries(KOLOM)) {
        document.getElementById(id).value = v[kunci];
    }
}

function cocokDenganFormulir(v) {
    return Object.entries(KOLOM).every(([id, kunci]) => String(document.getElementById(id).value) === String(v[kunci]));
}

async function muatVarian(pilihOtomatis) {
    daftarVarian = [];
    if (!merek.value || !model.value || !tahun.value) {
        varian.innerHTML = "<option>Pilih tahun dulu</option>";
        varian.disabled = true;
        return;
    }
    daftarVarian = await ambil(formulir.dataset.urlVarian, { merek: merek.value, model: model.value, tahun: tahun.value });
    varian.innerHTML = "";
    daftarVarian.forEach((v, i) => varian.add(new Option(v.label, i)));
    varian.disabled = false;
    if (pilihOtomatis) {                       // setelah memilih tahun: langsung isi dengan varian pertama
        varian.value = 0;
        isiSpesifikasi(daftarVarian[0]);
    } else {                                   // setelah formulir dikirim: tampilkan varian yang cocok dengan isian
        const i = daftarVarian.findIndex(cocokDenganFormulir);
        if (i >= 0) varian.value = i;
        else varian.add(new Option("Spesifikasi diubah sendiri", "-1"), 0), (varian.value = "-1");
    }
}

merek.addEventListener("change", async () => {
    isiMenu(tahun, [], "Pilih model dulu");
    if (!merek.value) { isiMenu(model, [], "Pilih merek dulu"); return muatVarian(true); }
    isiMenu(model, await ambil(formulir.dataset.urlModel, { merek: merek.value }), "Pilih model");
    muatVarian(true);
});

model.addEventListener("change", async () => {
    if (!model.value) { isiMenu(tahun, [], "Pilih model dulu"); return muatVarian(true); }
    isiMenu(tahun, await ambil(formulir.dataset.urlTahun, { merek: merek.value, model: model.value }), "Pilih tahun");
    muatVarian(true);
});

tahun.addEventListener("change", () => muatVarian(true));

varian.addEventListener("change", () => {
    const v = daftarVarian[Number(varian.value)];
    if (v) isiSpesifikasi(v);
});

// halaman dibuka kembali setelah klik "Hitung": daftar varian dimuat ulang
if (merek.value && model.value && tahun.value) muatVarian(false);