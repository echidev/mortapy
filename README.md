# MortaPy

[![PyPI version](https://badge.fury.io/py/mortapy.svg)](https://badge.fury.io/py/mortapy)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/<username-github-anda>/mortapy)

Sebuah library Python yang ringan dan intuitif untuk kalkulasi aktuaria dasar, dengan fokus pada penggunaan dan analisis Tabel Mortalita Indonesia.

Proyek ini bertujuan untuk menyediakan alat bantu yang andal bagi para aktuaris, mahasiswa, dan praktisi keuangan di Indonesia untuk melakukan perhitungan fundamental asuransi jiwa dan anuitas.

***

## Fitur Utama

- **Manajemen Tabel Mortalita**: Memuat tabel mortalita standar Indonesia (berbasis `qx`) atau tabel kustom Anda sendiri.
- **Kalkulasi Aktuaria Dasar**: Menghitung probabilitas hidup dan mati ($p_x$, $q_x$, $_np_x$).
- **Asuransi Jiwa**: Menghitung Premi Tunggal Bersih (NSP) untuk produk asuransi jiwa seumur hidup (*whole life*).
- **Anuitas Jiwa**: Menghitung Nilai Sekarang (PV) untuk produk anuitas jiwa seumur hidup awal tahun (*annuity due*).
- **Pengembangan Selanjutnya**: Dukungan untuk asuransi berjangka, dwiguna, dan anuitas yang lebih kompleks sedang dalam pengembangan.

***

## Instalasi

Pastikan Anda memiliki Python 3.8 atau yang lebih baru.

#### Opsi 1: Instal dari GitHub (untuk pengguna)

Anda bisa menginstal versi pengembangan terbaru langsung dari repositori ini menggunakan `pip`:
```bash
pip install git+[https://github.com/](https://github.com/)<username-github-anda>/mortapy.git