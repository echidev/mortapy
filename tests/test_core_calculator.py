# tests/test_core_calculator.py
import pytest
from mortapy.tables.base import MortalityTable
from mortapy.core_calculator import ActuarialCalculator
import os
import math
from typing import Callable, Literal, Optional, List # Impor yang diperlukan

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
        if not os.path.exists(TEST_TABLE_PATH_DEFAULT):
            TEST_TABLE_PATH_DEFAULT = "mortapy/tables/tabel_mortalita_penduduk_indonesia_2023.csv"
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
    assert calc_basic.survival_probability_from_table(age=30, n_years=0, gender='pria', table=default_table) == 1.0
    p1 = calc_basic.survival_probability_from_table(age=30, n_years=1, gender='pria', table=default_table)
    p2 = calc_basic.survival_probability_from_table(age=30, n_years=2, gender='pria', table=default_table)
    assert p2 < p1 if p1 > 0 else p2 == p1
    assert 0 <= p1 <= 1.0
    assert calc_basic.survival_probability_from_table(age=default_table.max_age + 1, n_years=1, gender='pria', table=default_table) == 0.0

def test_death_probability_from_table_core(calc_basic: ActuarialCalculator, default_table: MortalityTable):
    age, n, gender = 30, 2, 'pria'
    p_val = calc_basic.survival_probability_from_table(age, n, gender, default_table)
    q_val = calc_basic.death_probability_from_table(age, n, gender, default_table)
    assert q_val == pytest.approx(1.0 - p_val)

def test_deferred_death_probability_from_table_core(calc_basic: ActuarialCalculator, default_table: MortalityTable):
    age, t, u, gender = 30, 2, 3, 'pria'
    t_px = calc_basic.survival_probability_from_table(age, t, gender, default_table)
    u_q_xt = calc_basic.death_probability_from_table(age + t, u, gender, default_table)
    expected_val = t_px * u_q_xt
    actual_val = calc_basic.deferred_death_probability_from_table(age, t, u, gender, default_table)
    assert actual_val == pytest.approx(expected_val)

def test_force_of_mortality_from_table_core(calc_basic: ActuarialCalculator, default_table: MortalityTable):
    age, t_offset, gender = 35, 0.5, 'pria'
    mu_cfm = calc_basic.force_of_mortality_from_table(age, t_offset, gender, default_table, 'cfm')
    px_val = default_table.px(age, gender)
    expected_mu_cfm = -math.log(px_val) if px_val > 0 else float('inf')
    assert mu_cfm == pytest.approx(expected_mu_cfm)
    mu_udd = calc_basic.force_of_mortality_from_table(age, t_offset, gender, default_table, 'udd')
    qx_val = default_table.qx(age, gender)
    expected_mu_udd = qx_val / (1.0 - t_offset * qx_val) if (1.0 - t_offset * qx_val) > 1e-12 else float('inf')
    assert mu_udd == pytest.approx(expected_mu_udd)

def test_pdf_death_from_table_core(calc_basic: ActuarialCalculator, default_table: MortalityTable):
    age, t_period, gender = 35, 0.5, 'pria'
    px_base = default_table.px(age, gender)
    tpx_value_frac = px_base ** t_period if px_base > 0 else 0.0 # Asumsi CFM untuk _s p_x
    if t_period == 0 : tpx_value_frac = 1.0
    
    mu_value = calc_basic.force_of_mortality_from_table(age, t_period, gender, default_table, 'cfm') 
    expected_pdf = tpx_value_frac * mu_value
    actual_pdf = calc_basic.pdf_death_from_table(age, t_period, gender, default_table, 'cfm')
    assert actual_pdf == pytest.approx(expected_pdf)

def test_ex_curtate_from_table_core(calc_basic: ActuarialCalculator, default_table: MortalityTable):
    """Tes ekspektasi curtate future lifetime dari tabel."""
    # Untuk e_x, suku bunga tidak relevan
    # e_109 (pria) = p_109 + p_109*p_110 (jika max_age 111)
    # e_109 = p_109 + _2p_109
    # e_x = sum_{k=1}^{omega-x} _k p_x
    ex_109_pria = calc_basic.ex_curtate_from_table(109, 'pria', default_table)
    p_109 = default_table.px(109, 'pria')
    p_110 = default_table.px(110, 'pria')
    # _1p_109 = p_109
    # _2p_109 = p_109 * p_110
    # max_age tabel 111, jadi omega-x = 111-109 = 2. Loop k=1,2
    expected_ex_109 = p_109 + (p_109 * p_110)
    assert ex_109_pria == pytest.approx(expected_ex_109)

    # Tes temporary e_{x:n|}
    ex_30_5_pria = calc_basic.ex_curtate_from_table(30, 'pria', default_table, n_temp=5)
    expected_ex_30_5 = 0
    for k in range(1, 5 + 1):
        expected_ex_30_5 += calc_basic.survival_probability_from_table(30, k, 'pria', default_table)
    assert ex_30_5_pria == pytest.approx(expected_ex_30_5)

def test_e_sq_curtate_from_table_core(calc_basic: ActuarialCalculator, default_table: MortalityTable):
    """Tes momen kedua curtate future lifetime dari tabel."""
    # E[K_x^2] = sum_{j=0}^{omega-x-1} (2j+1) * _{j+1}p_x
    # Untuk K_109 (pria), max_age = 111. omega-x-1 = 111-109-1 = 1. Jadi j=0 dan j=1.
    # j=0: (1) * _1p_109 = p_109
    # j=1: (3) * _2p_109 = 3 * p_109 * p_110
    e_sq_109_pria = calc_basic.e_sq_curtate_from_table(109, 'pria', default_table)
    p_109 = default_table.px(109, 'pria')
    p_110 = default_table.px(110, 'pria')
    _1p_109 = p_109
    _2p_109 = p_109 * p_110
    expected_e_sq_109 = (1 * _1p_109) + (3 * _2p_109)
    assert e_sq_109_pria == pytest.approx(expected_e_sq_109)

    # Tes temporary E[(K_{x:n|})^2]
    e_sq_30_2_pria = calc_basic.e_sq_curtate_from_table(30, 'pria', default_table, n_temp=2)
    # n_temp=2, jadi limit_j=2, loop j=0,1
    # j=0: (1) * _1p_30
    # j=1: (3) * _2p_30
    _1p_30 = calc_basic.survival_probability_from_table(30, 1, 'pria', default_table)
    _2p_30 = calc_basic.survival_probability_from_table(30, 2, 'pria', default_table)
    expected_e_sq_30_2 = (1 * _1p_30) + (3 * _2p_30)
    assert e_sq_30_2_pria == pytest.approx(expected_e_sq_30_2)


# === Tes untuk Metode Berbasis Asumsi ===
@pytest.fixture
def calc_assumption_core() -> ActuarialCalculator:
    return ActuarialCalculator(interest_rate=0.05)

def test_survival_probability_from_assumption_core(calc_assumption_core: ActuarialCalculator):
    qx_val = 0.01
    px_func_yearly = lambda age_input: 1.0 - qx_val
    omega = 120
    assert calc_assumption_core.survival_probability_from_assumption(30, 2.0, px_func_yearly, omega) == pytest.approx((1.0-qx_val)**2)
    expected_cfm = ((1.0-qx_val)**2) * ((1.0-qx_val)**0.5)
    assert calc_assumption_core.survival_probability_from_assumption(30, 2.5, px_func_yearly, omega, 'cfm') == pytest.approx(expected_cfm)
    expected_udd = ((1.0-qx_val)**2) * (1.0 - 0.5 * qx_val)
    assert calc_assumption_core.survival_probability_from_assumption(30, 2.5, px_func_yearly, omega, 'udd') == pytest.approx(expected_udd)

def test_death_probability_from_assumption_core(calc_assumption_core: ActuarialCalculator):
    px_func = lambda age_input: 0.98 
    omega = 110
    n = 2.5
    tpx = calc_assumption_core.survival_probability_from_assumption(30, n, px_func, omega)
    tqx = calc_assumption_core.death_probability_from_assumption(30, n, px_func, omega)
    assert tqx == pytest.approx(1.0 - tpx)

def test_deferred_death_probability_from_assumption_core(calc_assumption_core: ActuarialCalculator):
    px_yearly_func = lambda age_input: 0.95 
    omega = 100
    age, t, u = 40, 2.5, 3.5
    
    # Menggunakan formula pengurangan untuk verifikasi karena implementasi core juga begitu
    t_px = calc_assumption_core.survival_probability_from_assumption(age, t, px_yearly_func, omega)
    t_plus_u_px = calc_assumption_core.survival_probability_from_assumption(age, t + u, px_yearly_func, omega)
    expected_val = t_px - t_plus_u_px
    
    actual_val = calc_assumption_core.deferred_death_probability_from_assumption(age, t, u, px_yearly_func, omega)
    assert actual_val == pytest.approx(expected_val)

def test_ex_curtate_from_assumption_core(calc_assumption_core: ActuarialCalculator):
    """Tes ekspektasi curtate future lifetime dari asumsi."""
    px_val = 0.95
    px_func_yearly = lambda age_input: px_val
    omega = 100 # Cukup untuk contoh
    age = 98
    # e_98 = p_98 + _2p_98 = p_98 + p_98*p_99
    # limit_k = omega - age = 100 - 98 = 2. Loop k=1,2
    expected_ex = px_val + (px_val * px_val)
    assert calc_assumption_core.ex_curtate_from_assumption(age, px_func_yearly, omega) == pytest.approx(expected_ex)
    
    # Tes temporary
    # e_98:1| = p_98
    expected_ex_temp1 = px_val
    assert calc_assumption_core.ex_curtate_from_assumption(age, px_func_yearly, omega, n_temp=1) == pytest.approx(expected_ex_temp1)

def test_e_sq_curtate_from_assumption_core(calc_assumption_core: ActuarialCalculator):
    """Tes momen kedua curtate future lifetime dari asumsi."""
    px_val = 0.9
    px_func_yearly = lambda age_input: px_val
    omega = 50 # Cukup untuk contoh
    age = 48
    # E[K_48^2], omega-age = 2. limit_j = 2. Loop j=0,1
    # j=0: (1) * _1p_48 = p_48
    # j=1: (3) * _2p_48 = 3 * p_48 * p_49
    _1p_48 = px_val
    _2p_48 = px_val * px_val
    expected_e_sq = (1 * _1p_48) + (3 * _2p_48)
    assert calc_assumption_core.e_sq_curtate_from_assumption(age, px_func_yearly, omega) == pytest.approx(expected_e_sq)

    # Tes temporary E[K_{48:1|}^2]
    # n_temp=1, limit_j=1. Loop j=0
    # j=0: (1) * _1p_48
    expected_e_sq_temp1 = 1 * _1p_48
    assert calc_assumption_core.e_sq_curtate_from_assumption(age, px_func_yearly, omega, n_temp=1) == pytest.approx(expected_e_sq_temp1)

# Tes untuk nsp_whole_life_from_assumption dan pv_annuity_due_whole_life_from_assumption
# bisa tetap sama seperti versi sebelumnya.