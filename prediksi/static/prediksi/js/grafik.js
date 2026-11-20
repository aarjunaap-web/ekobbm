// Membaca data dari Django (json_script), lalu menggambar 4 grafik dengan Chart.js
const data = JSON.parse(document.getElementById("data-grafik").textContent);

const HIJAU = "#0f766e";
const AKSEN = "#f59e0b";
const MERAH = "#dc2626";
const ABU = "#6b7280";

Chart.defaults.font.family = "'Plus Jakarta Sans', system-ui, sans-serif";
Chart.defaults.color = ABU;
Chart.defaults.maintainAspectRatio = false;

// warna titik/batang mengikuti kategori: boros / sedang / irit
function warna(nilai) {
    if (nilai >= data.batas.irit_di_atas) return HIJAU;
    if (nilai < data.batas.boros_di_bawah) return MERAH;
    return AKSEN;
}

// 1. sebaran berat vs km/L
new Chart(document.getElementById("gSebaran"), {
    type: "scatter",
    data: {
        datasets: [{
            data: data.titik,
            backgroundColor: data.titik.map(t => warna(t.y) + "b3"),
            pointRadius: 4,
        }],
    },
    options: {
        plugins: {
            legend: { display: false },
            tooltip: { callbacks: { label: c => `${Math.round(c.parsed.x)} kg, ${c.parsed.y.toFixed(1)} km/L` } },
        },
        scales: {
            x: { title: { display: true, text: "Berat (kg)" } },
            y: { title: { display: true, text: "km/L" }, beginAtZero: true },
        },
    },
});

// 2. rata-rata per silinder
new Chart(document.getElementById("gSilinder"), {
    type: "bar",
    data: {
        labels: data.silinder.label,
        datasets: [{ data: data.silinder.nilai, backgroundColor: data.silinder.nilai.map(warna), borderRadius: 8 }],
    },
    options: {
        plugins: { legend: { display: false } },
        scales: { y: { title: { display: true, text: "km/L" }, beginAtZero: true } },
    },
});

// 3. tren per tahun
new Chart(document.getElementById("gTahun"), {
    type: "line",
    data: {
        labels: data.tahun.label,
        datasets: [{
            data: data.tahun.nilai, borderColor: HIJAU, backgroundColor: "rgba(15,118,110,.12)",
            fill: true, tension: .3, pointRadius: 4, pointBackgroundColor: HIJAU,
        }],
    },
    options: {
        plugins: { legend: { display: false } },
        scales: { y: { title: { display: true, text: "km/L" }, beginAtZero: true } },
    },
});

// 4. pentingnya fitur (batang mendatar)
new Chart(document.getElementById("gFitur"), {
    type: "bar",
    data: {
        labels: data.fitur.label,
        datasets: [{ data: data.fitur.nilai, backgroundColor: HIJAU, borderRadius: 8 }],
    },
    options: {
        indexAxis: "y",
        plugins: {
            legend: { display: false },
            tooltip: { callbacks: { label: c => c.parsed.x + "%" } },
        },
        scales: { x: { title: { display: true, text: "Pengaruh (%)" }, beginAtZero: true } },
    },
});

// 5. tombol penjelasan: minta teks ke server (yang menghubungi Groq), lalu tampilkan
const tombol = document.getElementById("tombolJelas");
const kotak = document.getElementById("hasilJelas");

tombol.addEventListener("click", async () => {
    tombol.disabled = true;
    kotak.textContent = "Sedang membuat penjelasan...";
    try {
        const jawaban = await fetch(tombol.dataset.url);
        const hasil = await jawaban.json();
        kotak.textContent = "";
        if (!hasil.berhasil) {
            kotak.textContent = hasil.teks;
        } else {
            const daftar = document.createElement("ul");
            hasil.teks.split("\n").filter(b => b.trim()).forEach(baris => {
                const li = document.createElement("li");
                li.textContent = baris.replace(/^[-*•]\s*/, "");  // textContent: aman dari HTML
                daftar.appendChild(li);
            });
            kotak.classList.remove("text-muted");
            kotak.appendChild(daftar);
        }
    } catch (e) {
        kotak.textContent = "Terjadi kesalahan saat menghubungi server.";
    }
    tombol.disabled = false;
});