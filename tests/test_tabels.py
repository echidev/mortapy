# tests/test_tables.py
import pytest
from mortapy.tables.base import MortalityTable
import os
import pandas as pd
from typing import Literal, Optional, Any

# Logika path untuk TEST_TABLE_PATH_DEFAULT
try:
    path_candidate_1 = os.path.join("mortapy", "tables", "tabel_mortalita_penduduk_indonesia_2023.csv")
    path_candidate_2 = os.path.join(os.path.dirname(__file__), '..', 'mortapy', 'tables', 'tabel_mortalita_penduduk_indonesia_2023.csv')
    if os.path.exists(path_candidate_1):
        TEST_TABLE_PATH_DEFAULT = path_candidate_1
    elif os.path.exists(path_candidate_2):
        TEST_TABLE_PATH_DEFAULT = path_candidate_2
    else:
        TEST_TABLE_PATH_DEFAULT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mortapy', 'tables', 'tabel_mortalita_penduduk_indonesia_2023.csv')
        if not os.path.exists(TEST_TABLE_PATH_DEFAULT):
            TEST_TABLE_PATH_DEFAULT = "mortapy/tables/tabel_mortalita_penduduk_indonesia_2023.csv"
except Exception:
    TEST_TABLE_PATH_DEFAULT = "mortapy/tables/tabel_mortalita_penduduk_indonesia_2023.csv"


def test_tabel_berhasil_dimuat_default():
    """Memastikan objek MortalityTable bisa dibuat dari tabel default tanpa error."""
    try:
        table = MortalityTable(TEST_TABLE_PATH_DEFAULT)
        assert table is not None
        assert table.max_age_ultimate == 111
        assert table.has_gender_columns_ultimate is True
        assert table.is_unisex_ultimate is False
        assert table.is_select_and_ultimate is False # Default table bukan select
    except Exception as e:
        pytest.fail(f"Gagal memuat tabel default: {e}\nPath yang diuji: {TEST_TABLE_PATH_DEFAULT}")

def test_qx_dan_px_valid_default():
    """Memastikan nilai qx dan px logis dari tabel default (ultima)."""
    table = MortalityTable(TEST_TABLE_PATH_DEFAULT)
    age = 35
    gender: Literal["pria", "wanita"] = 'pria'
    
    qx_val = table.get_qx(age, gender) # Menggunakan get_qx
    px_val = table.get_px(age, gender) # Menggunakan get_px
    
    assert 0 <= qx_val <= 1
    assert 0 <= px_val <= 1
    assert qx_val + px_val == pytest.approx(1.0)

def test_boundary_age_default():
    """Memastikan qx adalah 1 untuk usia di luar batas tabel default (ultima)."""
    table = MortalityTable(TEST_TABLE_PATH_DEFAULT)
    assert table.get_qx(150, 'wanita') == 1.0
    assert table.get_qx(-1, 'pria') == 1.0

def test_gender_validation_on_table_default():
    """Tes validasi gender pada tabel default (ultima)."""
    table = MortalityTable(TEST_TABLE_PATH_DEFAULT)
    with pytest.raises(ValueError, match="Parameter 'gender' harus 'pria' atau 'wanita'"):
        table.get_qx(30, "tidakada") # type: ignore
    with pytest.raises(ValueError, match="Parameter 'gender' harus 'pria' atau 'wanita'"):
        table.get_qx(30, None) # Karena tabel default TMI adalah gender-specific

@pytest.fixture
def unisex_ultimate_table_path(tmp_path):
    """Membuat file CSV tabel ultima unisex sementara."""
    d = tmp_path / "data_tables"
    d.mkdir(exist_ok=True)
    p = d / "unisex_ultimate_table.csv"
    content = "x,qx\n60,0.01\n61,0.015\n62,1.0"
    p.write_text(content)
    return str(p)

@pytest.fixture
def select_table_gendered_path(tmp_path):
    """Membuat file CSV tabel seleksi berbasis gender sementara."""
    d = tmp_path / "data_tables"
    d.mkdir(exist_ok=True)
    p = d / "select_gendered_table.csv"
    content = (
        "age_select,d0_pria,d0_wanita,d1_pria,d1_wanita\n"
        "60,0.005,0.004,0.006,0.0045\n"
        "61,0.007,0.005,0.008,0.0055\n"
    )
    p.write_text(content)
    return str(p)

def test_select_and_ultimate_table_loading(select_table_gendered_path, unisex_ultimate_table_path):
    """Tes memuat tabel seleksi dan ultima."""
    table = MortalityTable(
        ultimate_file_path=unisex_ultimate_table_path,
        select_file_path=select_table_gendered_path,
        select_duration=2 # Periode seleksi 2 tahun (d0, d1)
    )
    assert table.is_select_and_ultimate is True
    assert table.select_duration == 2
    assert table.select_table is not None
    assert table.ultimate_table is not None
    assert table.has_gender_columns_select is True # Karena ada _pria/_wanita di nama kolom
    assert table.is_unisex_ultimate is True

    # Akses data seleksi
    # q_[60] pria
    assert table.get_qx(attained_age=60, gender='pria', age_at_selection=60, duration_since_selection=0) == 0.005
    # q_[60]+1 pria
    assert table.get_qx(attained_age=61, gender='pria', age_at_selection=60, duration_since_selection=1) == 0.006
    # q_[60]+1 wanita
    assert table.get_qx(attained_age=61, gender='wanita', age_at_selection=60, duration_since_selection=1) == 0.0045

    # Akses data ultima (setelah periode seleksi)
    # q_[60]+2 pria (seharusnya q_62 dari tabel ultima unisex)
    assert table.get_qx(attained_age=62, gender='pria', age_at_selection=60, duration_since_selection=2) == 1.0 
    # q_61 (langsung dari ultima)
    assert table.get_qx(attained_age=61, gender='pria') == 0.015 # Dari unisex_ultimate_table

def test_select_table_fallback_to_ultimate(select_table_gendered_path, unisex_ultimate_table_path):
    """Tes fallback ke tabel ultima jika data seleksi tidak ada atau di luar periode."""
    table = MortalityTable(
        ultimate_file_path=unisex_ultimate_table_path,
        select_file_path=select_table_gendered_path,
        select_duration=2
    )
    # Durasi > select_duration
    assert table.get_qx(attained_age=62, gender='pria', age_at_selection=60, duration_since_selection=2) == 1.0 # q_62 dari ultima
    
    # Usia seleksi tidak ada di tabel seleksi
    assert table.get_qx(attained_age=65, gender='pria', age_at_selection=65, duration_since_selection=0) == 1.0 # q_65 dari ultima (karena tidak ada di dummy)

    # Tidak ada parameter seleksi yang diberikan
    assert table.get_qx(attained_age=60, gender='pria') == 0.01 # q_60 dari ultima