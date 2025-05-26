import pytest
from mortapy.tables.base import MortalityTable
import os

# Tentukan path ke tabel tes. Asumsi folder tests sejajar dengan folder mortapy
# Ini adalah cara yang robust untuk menemukan file tersebut
TEST_TABLE_PATH = os.path.join(os.path.dirname(__file__), '..', 'mortapy', 'tables', 'tabel_mortalita_penduduk_indonesia_2023.csv')

def test_tabel_berhasil_dimuat():
    """Memastikan objek MortalityTable bisa dibuat tanpa error."""
    try:
        table = MortalityTable(TEST_TABLE_PATH)
        assert table is not None
        assert table.max_age == 111 
    except Exception as e:
        pytest.fail(f"Gagal memuat tabel: {e}")

def test_qx_dan_px_valid():
    """Memastikan nilai qx dan px logis dan penjumlahannya adalah 1."""
    table = MortalityTable(TEST_TABLE_PATH)
    
    # Tes untuk usia 35 tahun, pria
    age = 35
    gender = 'pria'
    
    qx_val = table.qx(age, gender)
    px_val = table.px(age, gender)
    
    # Nilai qx harus antara 0 dan 1
    assert 0 < qx_val < 1
    # Nilai px harus antara 0 dan 1
    assert 0 < px_val < 1
    # Penjumlahan qx dan px harus mendekati 1
    assert qx_val + px_val == pytest.approx(1.0)

def test_boundary_age():
    """Memastikan qx adalah 1 untuk usia di luar batas."""
    table = MortalityTable(TEST_TABLE_PATH)
    
    # Usia sangat tua
    assert table.qx(150, 'wanita') == 1.0
    # Usia negatif
    assert table.qx(-1, 'pria') == 1.0