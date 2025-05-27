# tests/test_fractional.py

import pytest
from mortapy.tables.base import MortalityTable # Ini masih dibutuhkan untuk fixture
from mortapy.core import ActuarialCalculator
import os

TEST_TABLE_PATH = os.path.join(os.path.dirname(__file__), '..', 'mortapy', 'tables', 'tabel_mortalita_penduduk_indonesia_2023.csv')

@pytest.fixture
def calc():
    """Fixture untuk membuat objek kalkulator yang bisa dipakai ulang."""
    table = MortalityTable(TEST_TABLE_PATH)
    # Cara inisialisasi ActuarialCalculator ini sudah benar berdasarkan respons sebelumnya
    return ActuarialCalculator(interest_rate=0.05, mortality_table=table)

def test_p_frac_udd(calc):
    """Menguji perhitungan UDD untuk kasus sederhana."""
    age = 40
    # Probabilitas hidup 0.5 tahun di bawah UDD adalah 1 - 0.5 * q_40
    
    # ===== PERUBAHAN DI SINI =====
    # Semula: qx_40 = calc.table.qx(age, 'pria')
    # Menjadi:
    qx_40 = calc._get_qx(age, 'pria') 
    # ============================
    
    expected_p_frac = 1 - 0.5 * qx_40
    
    assert calc.p_frac(age, 0.5, 'pria', 'udd') == pytest.approx(expected_p_frac)
    
    # Memastikan hasil untuk 1 tahun penuh sama dengan metode integer
    assert calc.p_frac(age, 1.0, 'pria', 'udd') == pytest.approx(calc.p(age, 1, 'pria'))

def test_p_frac_cfm(calc):
    """Menguji perhitungan CFM untuk kasus sederhana."""
    age = 40
    # Probabilitas hidup 0.5 tahun di bawah CFM adalah (p_40)^0.5

    # ===== PERUBAHAN DI SINI =====
    # Semula: px_40 = calc.table.px(age, 'pria')
    # Menjadi:
    px_40 = calc._get_px(age, 'pria')
    # ============================
    
    expected_p_frac = px_40 ** 0.5
    
    assert calc.p_frac(age, 0.5, 'pria', 'cfm') == pytest.approx(expected_p_frac)

    # Memastikan hasil untuk 1 tahun penuh sama dengan metode integer
    assert calc.p_frac(age, 1.0, 'pria', 'cfm') == pytest.approx(calc.p(age, 1, 'pria'))

def test_p_frac_values_are_correct(calc): # Sebelumnya bernama test_udd_vs_cfm_high_mortality
    """
    Memverifikasi hasil perhitungan UDD dan CFM dengan nilai yang sudah
    dihitung secara manual (regression test).
    """
    age = 85
    period = 0.5
    gender = 'wanita'
    
    # Berdasarkan tabel (data asli): q_85_wanita = 0.046397
    # Maka p_85_wanita = 1 - 0.046397 = 0.953603
    
    # Nilai yang diharapkan berdasarkan perhitungan manual
    # Untuk qx_85_wanita = 0.046397 (digunakan oleh _get_qx di bawah)
    expected_udd = 1 - (period * 0.046397) # 1 - t*q_x
    # Untuk px_85_wanita = 0.953603 (digunakan oleh _get_px di bawah)
    expected_cfm = (0.953603) ** period    # (p_x)^t
    
    # Panggil fungsi dari kode Anda
    p_udd_actual = calc.p_frac(age, period, gender, 'udd')
    p_cfm_actual = calc.p_frac(age, period, gender, 'cfm')
    
    # Lakukan assert terhadap nilai yang benar
    assert p_udd_actual == pytest.approx(expected_udd)
    assert p_cfm_actual == pytest.approx(expected_cfm)
    
    # Kita juga bisa pastikan bahwa untuk data ini, UDD > CFM
    # (Berdasarkan perhitungan manual sebelumnya untuk data ini)
    assert p_udd_actual > p_cfm_actual