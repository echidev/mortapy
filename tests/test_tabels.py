# tests/test_tables.py
import pytest
from mortapy.tables.base import MortalityTable
import os
import pandas as pd

# Menggunakan path yang lebih robust yang juga dipakai di api_tables.py
TEST_TABLE_PATH_DEFAULT = os.path.join("mortapy", "tables", "tabel_mortalita_penduduk_indonesia_2023.csv")
if not os.path.exists(TEST_TABLE_PATH_DEFAULT): # Fallback jika dijalankan dari folder tests
    TEST_TABLE_PATH_DEFAULT = os.path.join(os.path.dirname(__file__), '..', 'mortapy', 'tables', 'tabel_mortalita_penduduk_indonesia_2023.csv')


def test_tabel_berhasil_dimuat_default():
    """Memastikan objek MortalityTable bisa dibuat dari tabel default tanpa error."""
    try:
        table = MortalityTable(TEST_TABLE_PATH_DEFAULT)
        assert table is not None
        assert table.max_age == 111 # Sesuai data terakhir
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
    
    assert 0 <= qx_val <= 1 # qx bisa 0 atau 1 di batas
    assert 0 <= px_val <= 1 # px bisa 0 atau 1 di batas
    assert qx_val + px_val == pytest.approx(1.0)

def test_boundary_age_default():
    """Memastikan qx adalah 1 untuk usia di luar batas tabel default."""
    table = MortalityTable(TEST_TABLE_PATH_DEFAULT)
    assert table.qx(150, 'wanita') == 1.0
    assert table.qx(-1, 'pria') == 1.0

def test_gender_validation_on_table_default():
    """Tes validasi gender pada tabel default."""
    table = MortalityTable(TEST_TABLE_PATH_DEFAULT)
    with pytest.raises(ValueError, match="Parameter 'gender' harus 'pria' atau 'wanita' untuk tabel ini."):
        table.qx(30, "tidakada") # type: ignore
    with pytest.raises(ValueError, match="Parameter 'gender' harus 'pria' atau 'wanita' untuk tabel ini."):
        table.qx(30, None)


# Contoh tes untuk tabel unisex (jika Anda membuatnya)
# @pytest.fixture
# def unisex_table_path(tmp_path):
#     d = tmp_path / "data"
#     d.mkdir()
#     p = d / "unisex_table.csv"
#     content = "x,qx\n30,0.01\n31,0.015\n110,1.0"
#     p.write_text(content)
#     return str(p)

# def test_unisex_table_loading(unisex_table_path):
#     table = MortalityTable(unisex_table_path)
#     assert table.is_unisex_table is True
#     assert table.has_gender_columns is False
#     assert table.qx(30) == 0.01
#     assert table.qx(30, 'pria') == 0.01 # Gender diabaikan