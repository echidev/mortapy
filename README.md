MortaPyMortaPy adalah library Python yang ringan dan intuitif untuk kalkulasi aktuaria dasar, dengan fokus pada penggunaan Tabel Mortalita Indonesia dan berbagai asumsi distribusi mortalita.Proyek ini bertujuan untuk menyediakan alat bantu yang andal dan fleksibel bagi para aktuaris, mahasiswa, peneliti, dan praktisi keuangan di Indonesia untuk melakukan perhitungan fundamental terkait asuransi jiwa dan anuitas. MortaPy dirancang agar mudah digunakan, dengan API yang jelas dan output yang informatif, termasuk representasi formula LaTeX untuk kemudahan analisis di lingkungan seperti Jupyter Notebook.Daftar IsiFitur UtamaInstalasiContoh Penggunaan CepatPerhitungan Berbasis Tabel MortalitaPerhitungan Berbasis Asumsi DistribusiOperasi Aritmatika pada HasilStruktur ProyekPengembangan & KontribusiLisensiFitur UtamaManajemen Tabel Mortalita:Memuat Tabel Mortalita Indonesia (TMI) default yang disertakan.Memungkinkan pengguna memuat tabel mortalita kustom mereka sendiri (format CSV).Penanganan otomatis untuk tabel dengan atau tanpa pembedaan gender.Kalkulasi Aktuaria Berbasis Tabel:Menghitung probabilitas hidup dan mati (px​,qx​,n​px​) berdasarkan data tabel.Menghitung Premi Tunggal Bersih (NSP) untuk produk asuransi jiwa seumur hidup (Ax​).Menghitung Nilai Sekarang (PV) untuk produk anuitas jiwa seumur hidup awal tahun (a¨x​).(Pengembangan selanjutnya: asuransi berjangka, dwiguna, anuitas berjangka, interpolasi usia non-bulat UDD/CFM).Kalkulasi Aktuaria Berbasis Asumsi Distribusi Murni:Mendukung perhitungan untuk qx​ konstan, px​ konstan, Hukum De Moivre (ω), dan Constant Force of Mortality (μ konstan).Menghitung probabilitas hidup, NSP, dan PV anuitas tanpa memerlukan tabel eksternal.Mampu menangani periode waktu non-bulat (fraksional) untuk probabilitas hidup di bawah asumsi kontinu (De Moivre, CFM).(Pengembangan selanjutnya: Gompertz, Makeham, Weibull, Beta Distribution).Output Hasil yang Informatif:Hasil perhitungan disajikan sebagai objek ActuarialResult yang menampilkan nilai numerik dan representasi simbol LaTeX dari formula yang digunakan (ideal untuk Jupyter Notebook).Mendukung operasi aritmatika dasar (+, -) antar objek ActuarialResult atau dengan angka.InstalasiPastikan Anda memiliki Python 3.8 atau yang lebih baru terinstal di sistem Anda.Opsi 1: Instal dari GitHub (untuk pengguna)Anda bisa menginstal versi pengembangan terbaru langsung dari repositori GitHub ini menggunakan pip:pip install git+[https://github.com/echidev/mortapy.git](https://github.com/echidev/mortapy.git)
Opsi 2: Instal untuk Pengembangan Lokal (untuk kontributor)Jika Anda ingin berkontribusi pada proyek ini atau melakukan modifikasi lokal:# 1. Clone repositori ini ke komputer lokal Anda
git clone [https://github.com/echidev/mortapy.git](https://github.com/echidev/mortapy.git)
cd mortapy

# 2. Buat dan aktifkan virtual environment (sangat direkomendasikan)
python -m venv venv
# Untuk Windows:
# venv\Scripts\activate
# Untuk MacOS/Linux:
# source venv/bin/activate

# 3. Instal dependensi yang dibutuhkan proyek
pip install -r requirements.txt

# 4. Instal library mortapy dalam mode editable
pip install -e .
Mode editable (-e) berarti perubahan yang Anda buat pada kode sumber akan langsung terlihat saat Anda mengimpor library, tanpa perlu instal ulang.Contoh Penggunaan CepatBerikut adalah beberapa contoh bagaimana menggunakan MortaPy di skrip Python atau Jupyter Notebook.import mortapy as mp

# --- Parameter Dasar untuk Contoh ---
usia = 35
periode_hidup = 5 # tahun
suku_bunga = 0.05 # 5%

print("="*60)
print("CONTOH PENGGUNAAN MORTAPY")
print("="*60)

# === 1. Perhitungan Berbasis Tabel Mortalita Default (TMI) ===
print("\n--- 1. BERBASIS TABEL MORTALITA DEFAULT ---")

# a. NSP Asuransi Jiwa Seumur Hidup untuk Pria
print(f"\nMenghitung NSP A_{{{usia}}} untuk Pria (Tabel Default):")
nsp_tabel_pria = mp.nsp_wl_table(
    age=usia,
    interest_rate=suku_bunga,
    gender='pria'
)
nsp_tabel_pria.show() # Di Jupyter, ini akan render LaTeX. Di terminal, print deskripsi.

# b. PV Anuitas Jiwa Seumur Hidup Awal Tahun untuk Wanita
usia_anuitan = 60
print(f"\nMenghitung PV Anuitas ä_{{{usia_anuitan}}} untuk Wanita (Tabel Default):")
pv_ann_tabel_wanita = mp.pv_annuity_due_wl_table(
    age=usia_anuitan,
    interest_rate=suku_bunga,
    gender='wanita'
)
pv_ann_tabel_wanita.show()

# c. Probabilitas Hidup
print(f"\nMenghitung Probabilitas Hidup _{{{periode_hidup}}}p_{{{usia}}} untuk Pria (Tabel Default):")
prob_hidup_tabel = mp.survival_prob_table(
    age=usia,
    n_years=periode_hidup,
    interest_rate=suku_bunga, # Diperlukan untuk konsistensi kalkulator
    gender='pria'
)
prob_hidup_tabel.show()


# === 2. Perhitungan Berbasis Asumsi Distribusi Murni ===
print("\n\n--- 2. BERBASIS ASUMSI DISTRIBUSI MURNI ---")

# a. Asumsi Hukum De Moivre dengan omega = 100
omega_dm = 100
print(f"\nMenghitung NSP A_{{{usia}}} (Asumsi De Moivre, ω={omega_dm}):")
nsp_asumsi_dm = mp.nsp_wl_assumption(
    age=usia,
    interest_rate=suku_bunga,
    assumption_type='de_moivre',
    param1=float(omega_dm) # param1 adalah omega
)
nsp_asumsi_dm.show()

# b. Asumsi Constant Force of Mortality (CFM) dengan mu = 0.02
mu_cfm = 0.02
periode_non_bulat = 2.5
print(f"\nMenghitung Probabilitas Hidup _{{{periode_non_bulat}}}p_{{{usia}}} (Asumsi CFM, μ={mu_cfm}):")
prob_asumsi_cfm = mp.survival_prob_assumption(
    age=usia,
    period=periode_non_bulat,
    interest_rate=suku_bunga,
    assumption_type='constant_mu_cfm',
    param1=mu_cfm # param1 adalah mu
)
prob_asumsi_cfm.show()

# c. Asumsi q_x konstan = 0.01
qx_konstan = 0.01
print(f"\nMenghitung PV Anuitas ä_{{{usia}}} (Asumsi q_x konstan = {qx_konstan}):")
pv_ann_asumsi_qx = mp.pv_annuity_due_wl_assumption(
    age=usia,
    interest_rate=suku_bunga,
    assumption_type='constant_qx',
    param1=qx_konstan # param1 adalah q_x
)
pv_ann_asumsi_qx.show()


# === 3. Operasi Aritmatika pada Hasil ===
# Hanya jalankan jika objek sebelumnya berhasil dibuat
if 'nsp_tabel_pria' in locals() and 'nsp_asumsi_dm' in locals() and 'pv_ann_tabel_wanita' in locals():
    print("\n\n--- 3. OPERASI ARITMATIKA PADA HASIL ---")
    print("\nMenjumlahkan NSP dari Tabel dengan NSP dari Asumsi De Moivre:")
    total_nsp_gabungan = nsp_tabel_pria + nsp_asumsi_dm
    total_nsp_gabungan.show()

    print("\nMengurangkan konstanta dari hasil PV Anuitas:")
    pv_ann_dikurangi = pv_ann_tabel_wanita - 0.5
    pv_ann_dikurangi.show()
Output yang Diharapkan di Jupyter Notebook (Contoh untuk satu kasus):Untuk nsp_tabel_pria.show():A_{35; \text{pria}} = \text{NILAI_NUMERIK}Deskripsi: NSP Asuransi Jiwa Seumur Hidup (Tabel), Usia 35, Gender PriaUntuk total_nsp_gabungan.show():(A_{35; \text{pria}} + A_{35}) = \text{HASIL_PENJUMLAHAN}Deskripsi: Operasi (NSP Asuransi Jiwa Seumur Hidup (Tabel), Usia 35, Gender Pria) + (NSP Whole Life (Asumsi: De Moivre (ω=100)), Usia 35)Struktur ProyekBerikut adalah gambaran umum struktur direktori proyek MortaPy:mortapy/
├── .gitignore
├── README.md
├── requirements.txt
├── setup.py
├── examples/                 # Contoh penggunaan library
│   ├── contoh_penggunaan_lengkap.ipynb # Atau .py yang sudah disesuaikan
├── mortapy/                  # Paket inti Python
│   ├── __init__.py           # Inisialisasi paket & ekspor publik
│   ├── api_tables.py         # API untuk perhitungan berbasis tabel
│   ├── api_assumptions.py    # API untuk perhitungan berbasis asumsi
│   ├── core_calculator.py    # Logika kalkulasi aktuaria inti
│   ├── result.py             # Kelas ActuarialResult untuk output
│   └── tables/               # Sub-paket manajemen tabel mortalita
│       ├── __init__.py
│       ├── base.py           # Kelas MortalityTable
│       └── tabel_mortalita_penduduk_indonesia_2023.csv # Data TMI
└── tests/                    # Tes otomatis
    ├── test_api_tables.py
    ├── test_api_assumptions.py
    ├── test_core_calculator.py
    ├── test_result.py
    └── test_tables.py
Pengembangan & KontribusiKontribusi untuk MortaPy sangat diharapkan! Baik itu berupa laporan bug, permintaan fitur, perbaikan kode, atau penambahan dokumentasi.Setup Lingkungan PengembanganSilakan ikuti langkah-langkah pada bagian Instalasi untuk Pengembangan Lokal.Menjalankan TesProyek ini menggunakan pytest untuk pengujian otomatis. Sangat penting untuk menjalankan semua tes dan memastikan semuanya berhasil sebelum membuat commit atau pull request.# Pastikan Anda berada di direktori root proyek
# dan virtual environment Anda aktif.
pytest
Alur Kerja KontribusiBuat fork dari repositori echidev/mortapy.Buat branch baru untuk fitur atau perbaikan Anda (git checkout -b nama-fitur-anda).Lakukan perubahan dan tambahkan tes yang relevan.Pastikan semua tes berhasil (pytest).Commit perubahan Anda dengan pesan yang jelas.Push ke branch Anda di fork Anda (git push origin nama-fitur-anda).Buat Pull Request dari branch Anda di fork Anda ke branch main di echidev/mortapy.Jika Anda memiliki pertanyaan atau ide, jangan ragu untuk membuat Issue di halaman GitHub Issues repositori ini.LisensiProyek MortaPy dilisensikan di bawah Lisensi MIT. Anda dapat melihat detail lengkapnya di file LICENSE dalam repositori ini.(Anda perlu membuat file LICENSE dan memasukkan teks Lisensi MIT ke dalamnya. Anda bisa mencari template Lisensi MIT dengan mudah secara online.)