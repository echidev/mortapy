# setup.py

from setuptools import setup, find_packages

# Ini adalah praktik yang baik untuk membaca deskripsi panjang dari file README.md
# agar tampilannya bagus saat diunggah ke PyPI.
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    # 1. Informasi Dasar Proyek
    # Nama ini akan digunakan saat 'pip install mortapy'
    name="mortapy",
    version="0.1.0",

    # 2. Informasi Pembuat
    author="Muhammad Wildan Maulana",
    author_email="imwildanm@gmail.com",

    # 3. Deskripsi
    # Deskripsi singkat yang muncul di hasil pencarian PyPI
    description="Library aktuaria untuk analisis tabel mortalita Indonesia.",
    # Deskripsi panjang yang diambil dari README.md
    long_description=long_description,
    long_description_content_type="text/markdown",

    # 4. Tautan (URL)
    # Tautan utama ke repositori GitHub Anda
    url="https://github.com/echidev/mortapy",
    project_urls={
        "Bug Tracker": "https://github.com/echidev/mortapy/issues",
    },

    # 5. Konfigurasi Paket (Sangat Penting)
    # Secara otomatis menemukan semua paket Python di dalam proyek ini.
    # Ia akan menemukan folder 'mortapy' yang berisi '__init__.py'.
    packages=find_packages(),

    # 6. Metadata Tambahan (Klasifikasi)
    # Ini membantu orang menemukan paket Anda di PyPI.
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Scientific/Engineering :: Mathematics",
    ],

    # 7. Dependensi (Sangat Penting)
    # Daftar library lain yang dibutuhkan oleh 'mortapy' agar bisa berjalan.
    install_requires=[
        "pandas>=1.0.0",
    ],

    # 8. Versi Python yang Dibutuhkan
    # Mencegah instalasi pada versi Python yang tidak kompatibel.
    python_requires=">=3.8",
)