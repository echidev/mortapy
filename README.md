
MortaPy
=======

MortaPy adalah library Python yang ringan dan intuitif untuk kalkulasi aktuaria dasar, dengan fokus pada penggunaan Tabel Mortalita Indonesia dan berbagai asumsi distribusi mortalita.

Proyek ini bertujuan untuk menyediakan alat bantu yang andal dan fleksibel bagi para aktuaris, mahasiswa, peneliti, dan praktisi keuangan di Indonesia untuk melakukan perhitungan fundamental terkait asuransi jiwa dan anuitas. MortaPy dirancang agar mudah digunakan, dengan API yang jelas dan output yang informatif, termasuk representasi formula LaTeX untuk kemudahan analisis di lingkungan seperti Jupyter Notebook.

Daftar Isi
----------
- Fitur Utama
- Instalasi
- Contoh Penggunaan Cepat
- Perhitungan Berbasis Tabel Mortalita
- Perhitungan Berbasis Asumsi Distribusi
- Operasi Aritmatika pada Hasil
- Struktur Proyek
- Pengembangan & Kontribusi
- Lisensi

Fitur Utama
-----------

### Manajemen Tabel Mortalita:
- Memuat Tabel Mortalita Indonesia (TMI) default yang disertakan.
- Memungkinkan pengguna memuat tabel mortalita kustom mereka sendiri (format CSV).
- Penanganan otomatis untuk tabel dengan atau tanpa pembedaan gender.

### Kalkulasi Aktuaria Berbasis Tabel:
- Menghitung probabilitas hidup dan mati (px, qx, npx) berdasarkan data tabel.
- Menghitung Premi Tunggal Bersih (NSP) untuk produk asuransi jiwa seumur hidup (Ax).
- Menghitung Nilai Sekarang (PV) untuk produk anuitas jiwa seumur hidup awal tahun (äx).
- (Pengembangan selanjutnya: asuransi berjangka, dwiguna, anuitas berjangka, interpolasi usia non-bulat UDD/CFM).

### Kalkulasi Aktuaria Berbasis Asumsi Distribusi Murni:
- Mendukung perhitungan untuk qx konstan, px konstan, Hukum De Moivre (ω), dan Constant Force of Mortality (μ konstan).
- Menghitung probabilitas hidup, NSP, dan PV anuitas tanpa memerlukan tabel eksternal.
- Mampu menangani periode waktu non-bulat (fraksional) untuk probabilitas hidup di bawah asumsi kontinu (De Moivre, CFM).
- (Pengembangan selanjutnya: Gompertz, Makeham, Weibull, Beta Distribution).

### Output Hasil yang Informatif:
- Hasil perhitungan disajikan sebagai objek ActuarialResult yang menampilkan nilai numerik dan representasi simbol LaTeX.
- Mendukung operasi aritmatika dasar (+, -) antar objek ActuarialResult atau dengan angka.

Instalasi
---------

### Opsi 1: Instal dari GitHub (untuk pengguna)
```bash
pip install git+https://github.com/echidev/mortapy.git
```

### Opsi 2: Instal untuk Pengembangan Lokal (untuk kontributor)
```bash
git clone https://github.com/echidev/mortapy.git
cd mortapy

# Buat dan aktifkan virtual environment (sangat direkomendasikan)
python -m venv venv
# Windows: venv\Scripts\activate
# MacOS/Linux: source venv/bin/activate

# Instal dependensi proyek
pip install -r requirements.txt

# Instal MortaPy dalam mode editable
pip install -e .
```

Contoh Penggunaan Cepat
------------------------
Contoh skrip Python / Jupyter Notebook:
```python
import mortapy as mp

usia = 35
periode_hidup = 5
suku_bunga = 0.05

# 1. Perhitungan Tabel Mortalita
nsp_tabel_pria = mp.nsp_wl_table(age=usia, interest_rate=suku_bunga, gender='pria')
nsp_tabel_pria.show()

pv_ann_tabel_wanita = mp.pv_annuity_due_wl_table(age=60, interest_rate=suku_bunga, gender='wanita')
pv_ann_tabel_wanita.show()

prob_hidup_tabel = mp.survival_prob_table(age=usia, n_years=periode_hidup, interest_rate=suku_bunga, gender='pria')
prob_hidup_tabel.show()

# 2. Asumsi Distribusi
nsp_asumsi_dm = mp.nsp_wl_assumption(age=usia, interest_rate=suku_bunga, assumption_type='de_moivre', param1=100)
nsp_asumsi_dm.show()

prob_asumsi_cfm = mp.survival_prob_assumption(age=usia, period=2.5, interest_rate=suku_bunga, assumption_type='constant_mu_cfm', param1=0.02)
prob_asumsi_cfm.show()

pv_ann_asumsi_qx = mp.pv_annuity_due_wl_assumption(age=usia, interest_rate=suku_bunga, assumption_type='constant_qx', param1=0.01)
pv_ann_asumsi_qx.show()

# 3. Operasi Aritmatika
total_nsp_gabungan = nsp_tabel_pria + nsp_asumsi_dm
total_nsp_gabungan.show()

pv_ann_dikurangi = pv_ann_tabel_wanita - 0.5
pv_ann_dikurangi.show()
```

Struktur Proyek
----------------

```
mortapy/
├── .gitignore
├── README.md
├── requirements.txt
├── setup.py
├── examples/
│   └── contoh_penggunaan_lengkap.ipynb
├── mortapy/
│   ├── __init__.py
│   ├── api_tables.py
│   ├── api_assumptions.py
│   ├── core_calculator.py
│   ├── result.py
│   └── tables/
│       ├── __init__.py
│       ├── base.py
│       └── tabel_mortalita_penduduk_indonesia_2023.csv
└── tests/
    ├── test_api_tables.py
    ├── test_api_assumptions.py
    ├── test_core_calculator.py
    ├── test_result.py
    └── test_tables.py
```

Pengembangan & Kontribusi
--------------------------

### Menjalankan Tes
```bash
pytest
```

### Alur Kerja Kontribusi
1. Fork repositori `echidev/mortapy`
2. Buat branch baru (`git checkout -b fitur-anda`)
3. Lakukan perubahan & tambahkan tes
4. Jalankan `pytest` untuk memastikan semua tes lolos
5. Commit dan push ke branch Anda
6. Buat Pull Request ke branch `main`

Jika memiliki pertanyaan, silakan buat Issue di GitHub.

Lisensi
-------

Proyek ini menggunakan Lisensi MIT. Lihat file `LICENSE` untuk informasi lebih lanjut.
