# tests/test_api_tables.py
import pytest
from mortapy import (
    nsp_wl_table,
    pv_annuity_due_wl_table,
    survival_prob_table,
    load_default_table
)
from mortapy.result import ActuarialResult
# from mortapy.tables.base import MortalityTable # Tidak perlu jika hanya menguji API
import os

# Path ke tabel tes (jika berbeda dari default atau untuk tabel kustom)
# Untuk saat ini kita akan gunakan tabel default yang dimuat oleh fungsi API
# TEST_TABLE_PATH = os.path.join(os.path.dirname(__file__), '..', 'mortapy', 'tables', 'tabel_mortalita_penduduk_indonesia_2023.csv')

def test_nsp_wl_table_default():
    """Tes NSP Whole Life dengan tabel default."""
    result = nsp_wl_table(age=35, interest_rate=0.05, gender='pria')
    assert isinstance(result, ActuarialResult)
    assert result.value > 0
    assert "A_{35; \\text{pria}}" in result.formula_latex # Periksa formula LaTeX dasar
    assert "NSP Asuransi Jiwa Seumur Hidup (Tabel), Usia 35, Gender Pria" in result.description

def test_pv_annuity_due_wl_table_default():
    """Tes PV Anuitas Whole Life Due dengan tabel default."""
    result = pv_annuity_due_wl_table(age=60, interest_rate=0.06, gender='wanita')
    assert isinstance(result, ActuarialResult)
    assert result.value > 0
    assert "\\ddot{a}_{60; \\text{wanita}}" in result.formula_latex
    assert "PV Anuitas Jiwa Seumur Hidup Awal Tahun (Tabel), Usia 60, Gender Wanita" in result.description

def test_survival_prob_table_default():
    """Tes Probabilitas Hidup dengan tabel default."""
    result = survival_prob_table(age=30, n_years=5, interest_rate=0.05, gender='pria')
    assert isinstance(result, ActuarialResult)
    assert 0 < result.value <= 1.0
    assert "{}_{5}p_{30; \\text{pria}}" in result.formula_latex
    assert "Probabilitas Hidup 5 Tahun (Tabel), Usia 30, Gender Pria" in result.description

def test_table_gender_validation():
    """Tes validasi gender saat menggunakan tabel."""
    # Escape karakter khusus regex seperti '(' dan ')'
    expected_error_message = r"Parameter 'gender' \('pria' atau 'wanita'\) wajib untuk tabel ini\."
    # Alternatif lain, menggunakan re.escape():
    # import re
    # expected_error_message = re.escape("Parameter 'gender' ('pria' atau 'wanita') wajib untuk tabel ini.")
    
    with pytest.raises(ValueError, match=expected_error_message):
        nsp_wl_table(age=35, interest_rate=0.05, gender="tidakvalid") # type: ignore

# TODO: Tambahkan tes untuk penggunaan mortality_table kustom