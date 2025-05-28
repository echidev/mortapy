# tests/test_core_calculator.py
import pytest
from mortapy.tables.base import MortalityTable
from mortapy.core_calculator import ActuarialCalculator
import os
import math
from typing import Callable, Literal, Optional # Impor yang diperlukan

# (Logika path TEST_TABLE_PATH_DEFAULT tetap sama)
try:
    path_candidate_1 = os.path.join("mortapy", "tables", "tabel_mortalita_penduduk_indonesia_2023.csv")
    path_candidate_2 = os.path.join(os.path.dirname(__file__), '..', 'mortapy', 'tables', 'tabel_mortalita_penduduk_indonesia_2023.csv')
    if os.path.exists(path_candidate_1):
        TEST_TABLE_PATH_DEFAULT = path_candidate_1
    elif os.path.exists(path_candidate_2):
        TEST_TABLE_PATH_DEFAULT = path_candidate_2
    else:
        TEST_TABLE_PATH_DEFAULT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mortapy', 'tables', 'tabel_mortalita_penduduk_indonesia_2023.csv')
except Exception:
    TEST_TABLE_PATH_DEFAULT = "mortapy/tables/tabel_mortalita_penduduk_indonesia_2023.csv"

@pytest.fixture
def default_table() -> MortalityTable:
    """Fixture untuk memuat tabel mortalita default."""
    return MortalityTable(TEST_TABLE_PATH_DEFAULT)

@pytest.fixture
def calc_basic() -> ActuarialCalculator:
    """Fixture untuk kalkulator dasar hanya dengan suku bunga."""
    return ActuarialCalculator(interest_rate=0.05)

# === Tes untuk Metode Berbasis Tabel ===
def test_survival_probability_from_table_core(calc_basic: ActuarialCalculator, default_table: MortalityTable):
    """Tes _n p_x dengan tabel dari core."""
    assert calc_basic.survival_probability_from_table(age=30, n_years=0, gender='pria', table=default_table) == 1.0
    p1 = calc_basic.survival_probability_from_table(age=30, n_years=1, gender='pria', table=default_table)
    p2 = calc_basic.survival_probability_from_table(age=30, n_years=2, gender='pria', table=default_table)
    assert p2 < p1 if p1 > 0 else p2 == p1
    assert 0 <= p1 <= 1.0
    assert calc_basic.survival_probability_from_table(age=default_table.max_age + 1, n_years=1, gender='pria', table=default_table) == 0.0

def test_death_probability_from_table_core(calc_basic: ActuarialCalculator, default_table: MortalityTable):
    """Tes _n q_x dengan tabel dari core."""
    age, n, gender = 30, 2, 'pria'
    p_val = calc_basic.survival_probability_from_table(age, n, gender, default_table)
    q_val = calc_basic.death_probability_from_table(age, n, gender, default_table)
    assert q_val == pytest.approx(1.0 - p_val)

def test_deferred_death_probability_from_table_core(calc_basic: ActuarialCalculator, default_table: MortalityTable):
    """Tes _{t|u}q_x dengan tabel dari core menggunakan formula perkalian."""
    age, t, u, gender = 30, 2, 3, 'pria'
    t_px = calc_basic.survival_probability_from_table(age, t, gender, default_table)
    u_q_xt = calc_basic.death_probability_from_table(age + t, u, gender, default_table)
    expected_val = t_px * u_q_xt
    actual_val = calc_basic.deferred_death_probability_from_table(age, t, u, gender, default_table)
    assert actual_val == pytest.approx(expected_val)

def test_force_of_mortality_from_table_core(calc_basic: ActuarialCalculator, default_table: MortalityTable):
    """Tes mu_{x+s} dengan tabel dari core."""
    age, t_offset, gender = 35, 0.5, 'pria'
    # CFM
    mu_cfm = calc_basic.force_of_mortality_from_table(age, t_offset, gender, default_table, 'cfm')
    px_val = default_table.px(age, gender)
    expected_mu_cfm = -math.log(px_val) if px_val > 0 else float('inf')
    assert mu_cfm == pytest.approx(expected_mu_cfm)
    # UDD
    mu_udd = calc_basic.force_of_mortality_from_table(age, t_offset, gender, default_table, 'udd')
    qx_val = default_table.qx(age, gender)
    expected_mu_udd = qx_val / (1.0 - t_offset * qx_val) if (1.0 - t_offset * qx_val) > 1e-12 else float('inf')
    assert mu_udd == pytest.approx(expected_mu_udd)

def test_pdf_death_from_table_core(calc_basic: ActuarialCalculator, default_table: MortalityTable):
    """Tes PDF kematian _t p_x * mu_{x+t} dengan tabel dari core."""
    age, t_period, gender = 35, 0.5, 'pria'
    
    # Hitung tpx fraksional (misal CFM)
    px_base = default_table.px(age, gender)
    tpx_value_frac = px_base ** t_period if px_base > 0 else 0.0
    if t_period == 0: tpx_value_frac = 1.0
    
    mu_value = calc_basic.force_of_mortality_from_table(age, t_period, gender, default_table, 'cfm') # t_period di sini adalah t_offset
    
    expected_pdf = tpx_value_frac * mu_value
    actual_pdf = calc_basic.pdf_death_from_table(age, t_period, gender, default_table, 'cfm')
    assert actual_pdf == pytest.approx(expected_pdf)

# === Tes untuk Metode Berbasis Asumsi ===
def test_survival_probability_from_assumption_core():
    """Tes _t p_x dari asumsi (termasuk fraksional) di core."""
    calc = ActuarialCalculator(interest_rate=0.05)
    qx_val = 0.01
    px_func_yearly = lambda age_input: 1.0 - qx_val
    omega = 120
    
    # Periode bulat
    assert calc.survival_probability_from_assumption(30, 2.0, px_func_yearly, omega) == pytest.approx((1.0-qx_val)**2)
    # Periode non-bulat (default CFM untuk fraksional)
    expected_cfm = ((1.0-qx_val)**2) * ((1.0-qx_val)**0.5)
    assert calc.survival_probability_from_assumption(30, 2.5, px_func_yearly, omega, 'cfm') == pytest.approx(expected_cfm)
    # Periode non-bulat (UDD untuk fraksional)
    expected_udd = ((1.0-qx_val)**2) * (1.0 - 0.5 * qx_val)
    assert calc.survival_probability_from_assumption(30, 2.5, px_func_yearly, omega, 'udd') == pytest.approx(expected_udd)

def test_death_probability_from_assumption_core():
    """Tes _t q_x dari asumsi di core."""
    calc = ActuarialCalculator(interest_rate=0.05)
    px_func = lambda age_input: 0.98 # p_x = 0.98, q_x = 0.02
    omega = 110
    n = 2.5
    tpx = calc.survival_probability_from_assumption(30, n, px_func, omega)
    tqx = calc.death_probability_from_assumption(30, n, px_func, omega)
    assert tqx == pytest.approx(1.0 - tpx)

def test_deferred_death_probability_from_assumption_core():
    """Tes _{t|u}q_x dari asumsi di core (formula perkalian)."""
    calc = ActuarialCalculator(interest_rate=0.05)
    px_yearly_func = lambda age_input: 0.95 # p_x = 0.95
    omega = 100
    age, t, u = 40, 2.5, 3.5

    # _t p_x
    t_px = calc.survival_probability_from_assumption(age, t, px_yearly_func, omega)
    # _u q_{x+t} = 1 - _u p_{x+t}
    # Untuk _u p_{x+t}, usia awalnya age+t, periode u
    # Metode core kita butuh px_yearly_func dan age bulat.
    # Ini memerlukan penyesuaian jika ingin menghitung _u q_{x+t} dengan usia awal non-bulat
    # di level core. Untuk sekarang, kita gunakan formula pengurangan di tes untuk verifikasi.
    
    # Verifikasi dengan _t p_x - _{t+u} p_x
    t_plus_u_px = calc.survival_probability_from_assumption(age, t + u, px_yearly_func, omega)
    expected_deferred_qx = t_px - t_plus_u_px
    
    # Pemanggilan metode yang sudah diubah (yang menggunakan formula pengurangan juga di core)
    actual_deferred_qx = calc.deferred_death_probability_from_assumption(age, t, u, px_yearly_func, omega)
    assert actual_deferred_qx == pytest.approx(expected_deferred_qx)


# Tes untuk nsp_whole_life_from_assumption dan pv_annuity_due_whole_life_from_assumption
# bisa tetap sama seperti versi sebelumnya, memastikan mereka memanggil survival_probability_from_assumption
# dengan periode integer (float(k)).