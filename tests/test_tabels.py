# tests/test_tables.py
import pytest
from mortapy.tables.base import MortalityTable # Pastikan import dari lokasi yang benar
import os
import pandas as pd

# Path yang lebih robust untuk tabel default, dengan fallback
# Ini akan mencoba mencari dari struktur paket terlebih dahulu, lalu dari root proyek
try:
    # Mencoba path seolah-olah dijalankan dari root proyek (misal, saat 'pytest' dipanggil dari root)
    # Struktur: project_root/mortapy/tables/file.csv
    path_candidate_1 = os.path.join("mortapy", "tables", "tabel_mortalita_penduduk_indonesia_2023.csv")
    # Mencoba path relatif dari folder tests (jika struktur tests/ ada di luar paket mortapy utama)
    # Struktur: project_root/tests/../mortapy/tables/file.csv
    path_candidate_2 = os.path.join(os.path.dirname(__file__), '..', 'mortapy', 'tables', 'tabel_mortalita_penduduk_indonesia_2023.csv')
    
    if os.path.exists(path_candidate_1):
        TEST_TABLE_PATH_DEFAULT = path_candidate_1
    elif os.path.exists(path_candidate_2):
        TEST_TABLE_PATH_DEFAULT = path_candidate_2
    else:
        # Fallback jika tidak ditemukan, ini akan error jika tabel tidak ada
        TEST_TABLE_PATH_DEFAULT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mortapy', 'tables', 'tabel_mortalita_penduduk_indonesia_2023.csv')

except Exception: # Fallback paling akhir jika ada masalah path dinamis
    TEST_TABLE_PATH_DEFAULT = "mortapy/tables/tabel_mortalita_penduduk_indonesia_2023.csv"


def test_tabel_berhasil_dimuat_default():
    """Memastikan objek MortalityTable bisa dibuat dari tabel default tanpa error."""
    try:
        table = MortalityTable(TEST_TABLE_PATH_DEFAULT)
        assert table is not None
        assert table.max_age == 111 
        assert table.has_gender_columns is True
        assert table.is_unisex_table is False
    except Exception as e:
        pytest.fail(f"Gagal memuat tabel default: {e}\nPath yang diuji: {TEST_TABLE_PATH_DEFAULT}")

def test_qx_dan_px_valid_default():
    """Memastikan nilai qx dan px logis dari tabel default."""
    table = MortalityTable(TEST_TABLE_PATH_DEFAULT)
    age = 35
    gender = 'pria'
    
    qx_val = table.qx(age, gender)
    px_val = table.px(age, gender)
    
    assert 0 <= qx_val <= 1 
    assert 0 <= px_val <= 1 
    assert qx_val + px_val == pytest.approx(1.0)

def test_boundary_age_default():
    """Memastikan qx adalah 1 untuk usia di luar batas tabel default."""
    table = MortalityTable(TEST_TABLE_PATH_DEFAULT)
    assert table.qx(150, 'wanita') == 1.0
    assert table.qx(-1, 'pria') == 1.0

def test_gender_validation_on_table_default():
    """Tes validasi gender pada tabel default."""
    table = MortalityTable(TEST_TABLE_PATH_DEFAULT)
    with pytest.raises(ValueError, match="Parameter 'gender' harus 'pria' atau 'wanita' untuk tabel berbasis gender ini."):
        table.qx(30, "tidakada") # type: ignore
    with pytest.raises(ValueError, match="Parameter 'gender' harus 'pria' atau 'wanita' untuk tabel berbasis gender ini."):
        table.qx(30, None)

@pytest.fixture
def unisex_table_path(tmp_path):
    """Membuat file CSV tabel unisex sementara untuk testing."""
    d = tmp_path / "data"
    d.mkdir()
    p = d / "unisex_table.csv"
    content = "x,qx\n30,0.01\n31,0.015\n110,1.0"
    p.write_text(content)
    return str(p)

def test_unisex_table_loading_and_access(unisex_table_path):
    """Tes memuat dan mengakses tabel unisex."""
    table = MortalityTable(unisex_table_path)
    assert table.is_unisex_table is True
    assert table.has_gender_columns is False
    assert table.max_age == 110
    assert table.qx(30) == 0.01
    # Gender seharusnya diabaikan untuk tabel unisex oleh metode qx di MortalityTable
    assert table.qx(30, 'pria') == 0.01 
    assert table.px(31) == pytest.approx(1.0 - 0.015)