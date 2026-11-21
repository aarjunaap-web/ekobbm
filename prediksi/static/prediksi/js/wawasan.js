// Membaca data dari Django (json_script), menggambar grafik dengan Chart.js, lalu meminta ringkasan dari server.
const data = JSON.parse(document.getElementById("data-grafik").textContent);

const HIJAU = "#0f766e", KUNING = "#f59e0b", MERAH = "#dc2626", ABU = "#6b7280";

Chart.defaults.font.family = "'Plus Jakarta Sans', system-ui, sans-serif";
Chart.defaults.color = ABU;
Chart.defaults.maintainAspectRatio = false;

// warna mengikuti kategori yang sama dengan halaman Hitung: boros / sedang / irit
function warna(nilai) {
    if (nilai >= data.batas.irit) return "#16a34a";
    if (nilai < data.batas.boros) return MERAH;
    return KUNING;
}

const sumbuKml = { title: { display: true, text: "km per liter" }, beginAtZero: true };
const tanpaLegenda = { legend: { display: false } };

// 1. ukuran mesin vs km/L
new Chart(document.getElementById("gSebaran"), {
    type: "scatter",
    data: { datasets: [{ data: data.sebaran, backgroundColor: data.sebaran.map(t => warna(t.y) + "b3"), pointRadius: 4 }] },
    options: {
        plugins: { ...tanpaLegenda, tooltip: { callbacks: { label: c => `${String(c.parsed.x).replace(".", ",")} liter, ${c.parsed.y.toFixed(1).replace(".", ",")} km/L` } } },
        scales: { x: { title: { display: true, text: "Ukuran mesin (liter)" } }, y: sumbuKml },
    },
});

// 2. per jumlah silinder
new Chart(document.getElementById("gSilinder"), {
    type: "bar",
    data: { labels: data.silinder.label, datasets: [{ data: data.silinder.nilai, backgroundColor: data.silinder.nilai.map(warna), borderRadius: 8 }] },
    options: { plugins: tanpaLegenda, scales: { y: sumbuKml } },
});

// 3. per tahun
new Chart(document.getElementById("gTahun"), {
    type: "line",
    data: {
        labels: data.tahun.label,
        datasets: [{ data: data.tahun.nilai, borderColor: HIJAU, backgroundColor: "rgba(15,118,110,.12)", fill: true, tension: .3, pointRadius: 3, pointBackgroundColor: HIJAU }],
    },
    options: { plugins: tanpaLegenda, scales: { x: { ticks: { maxTicksLimit: 8 } }, y: sumbuKml } },
});

// batang mendatar: semua label tetap tampil
function batangMendatar(id, label, nilai, warnaBatang, judulSumbu) {
    new Chart(document.getElementById(id), {
        type: "bar",
        data: { labels: label, datasets: [{ data: nilai, backgroundColor: warnaBatang, borderRadius: 6 }] },
        options: {
            indexAxis: "y",
            plugins: tanpaLegenda,
            scales: { x: { title: { display: true, text: judulSumbu }, beginAtZero: true }, y: { ticks: { autoSkip: false } } },
        },
    });
}
batangMendatar("gKelas", data.kelas.label, data.kelas.nilai, data.kelas.nilai.map(warna), "km per liter");
batangMendatar("gMerek", data.merek.label, data.merek.nilai, data.merek.nilai.map(warna), "km per liter");
batangMendatar("gFaktor", data.faktor.label, data.faktor.nilai, HIJAU, "Pengaruh (%)");

// penjelasan tiap grafik: diminta ke server (yang menghubungi Groq), lalu dimasukkan ke kotak "Artinya"
const wadah = document.getElementById("penjelasan");
const lencana = document.getElementById("sumberPenjelasan");

fetch(wadah.dataset.url)
    .then(r => r.json())
    .then(hasil => {
        document.querySelectorAll(".artinya").forEach(kotak => {
            const teks = hasil.teks[kotak.dataset.kunci];
            if (teks) kotak.querySelector(".artinya-isi").textContent = teks;   // textContent: aman dari HTML
        });
        lencana.textContent = hasil.sumber === "ai" ? "Penjelasan ditulis oleh AI (Llama via Groq)" : "Penjelasan otomatis dari data";
        lencana.classList.remove("d-none");
    })
    .catch(() => {
        document.querySelectorAll(".artinya-isi").forEach(k => { k.textContent = "Penjelasan belum bisa ditampilkan."; });
    });