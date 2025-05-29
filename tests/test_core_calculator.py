# tests/test_core_calculator.py
import pytest
from mortapy.tables.base import MortalityTable
from mortapy.core_calculator import ActuarialCalculator
import os
import math
from typing import Callable, Literal, Optional, List 

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
    mu_cfm = calc_basic.force_of_mortality_from_table(age, t_offset, gender, default_table, 'cfm')
    px_val = default_table.px(age, gender)
    expected_mu_cfm = -math.log(px_val) if px_val > 0 else float('inf')
    assert mu_cfm == pytest.approx(expected_mu_cfm)
    mu_udd = calc_basic.force_of_mortality_from_table(age, t_offset, gender, default_table, 'udd')
    qx_val = default_table.qx(age, gender)
    expected_mu_udd = qx_val / (1.0 - t_offset * qx_val) if (1.0 - t_offset * qx_val) > 1e-12 else float('inf')
    assert mu_udd == pytest.approx(expected_mu_udd)

def test_pdf_death_from_table_core(calc_basic: ActuarialCalculator, default_table: MortalityTable):
    """Tes PDF kematian _t p_x * mu_{x+t} dengan tabel dari core."""
    age, t_period, gender = 35, 0.5, 'pria'
    
    integer_part_t = int(t_period)
    fractional_part_t = t_period - integer_part_t
    tpx_integer_part = calc_basic.survival_probability_from_table(age, integer_part_t, gender, default_table)
    tpx_value_frac = tpx_integer_part
    if fractional_part_t > 0 and tpx_integer_part > 0:
        age_after_integer = age + integer_part_t
        if age_after_integer <= default_table.max_age :
            px_base_frac = default_table.px(age_after_integer, gender) # p_x tahunan
            tpx_value_frac *= (px_base_frac ** fractional_part_t) # Asumsi CFM untuk fraksional
    elif tpx_integer_part == 0.0 and fractional_part_t > 0:
        tpx_value_frac = 0.0
    
    mu_value = calc_basic.force_of_mortality_from_table(age + integer_part_t, fractional_part_t, gender, default_table, 'cfm') 
    expected_pdf = tpx_value_frac * mu_value
    actual_pdf = calc_basic.pdf_death_from_table(age, t_period, gender, default_table, 'cfm')
    assert actual_pdf == pytest.approx(expected_pdf)

def test_ex_curtate_from_table_core(calc_basic: ActuarialCalculator, default_table: MortalityTable):
    """Tes ekspektasi curtate future lifetime dari tabel."""
    ex_109_pria = calc_basic.ex_curtate_from_table(109, 'pria', default_table)
    p_109 = default_table.px(109, 'pria')
    p_110 = default_table.px(110, 'pria')
    expected_ex_109 = p_109 + (p_109 * p_110)
    assert ex_109_pria == pytest.approx(expected_ex_109)
    ex_30_5_pria = calc_basic.ex_curtate_from_table(30, 'pria', default_table, n_temp=5)
    expected_ex_30_5 = sum(calc_basic.survival_probability_from_table(30, k, 'pria', default_table) for k in range(1, 5 + 1))
    assert ex_30_5_pria == pytest.approx(expected_ex_30_5)

def test_e_sq_curtate_from_table_core(calc_basic: ActuarialCalculator, default_table: MortalityTable):
    """Tes momen kedua curtate future lifetime dari tabel."""
    e_sq_109_pria = calc_basic.e_sq_curtate_from_table(109, 'pria', default_table)
    p_109 = default_table.px(109, 'pria')
    p_110 = default_table.px(110, 'pria')
    _1p_109 = p_109; _2p_109 = p_109 * p_110
    expected_e_sq_109 = (1 * _1p_109) + (3 * _2p_109)
    assert e_sq_109_pria == pytest.approx(expected_e_sq_109)
    e_sq_30_2_pria = calc_basic.e_sq_curtate_from_table(30, 'pria', default_table, n_temp=2)
    _1p_30 = calc_basic.survival_probability_from_table(30, 1, 'pria', default_table)
    _2p_30 = calc_basic.survival_probability_from_table(30, 2, 'pria', default_table)
    expected_e_sq_30_2 = (1 * _1p_30) + (3 * _2p_30)
    assert e_sq_30_2_pria == pytest.approx(expected_e_sq_30_2)

def test_ex_complete_from_table_core(calc_basic: ActuarialCalculator, default_table: MortalityTable):
    """Tes ekspektasi complete future lifetime dari tabel (aproksimasi UDD)."""
    age = 98
    ex_curtate = calc_basic.ex_curtate_from_table(age, 'pria', default_table)
    expected_ex_complete_udd = ex_curtate + 0.5
    assert calc_basic.ex_complete_from_table(age, 'pria', default_table, assumption_fractional='udd') == pytest.approx(expected_ex_complete_udd)
    
    n_temp = 2
    ex_curtate_temp = calc_basic.ex_curtate_from_table(age, 'pria', default_table, n_temp=n_temp)
    # Formula e_circ_{x:n|} = sum_{k=0}^{n-1} _k p_x (1 - 0.5 * q_{x+k})
    expected_ex_complete_temp_udd_sum = 0
    for k_loop in range(n_temp):
        k_px_val = calc_basic.survival_probability_from_table(age, k_loop, 'pria', default_table)
        qx_val_at_xk = default_table.qx(age + k_loop, 'pria')
        expected_ex_complete_temp_udd_sum += k_px_val * (1 - 0.5 * qx_val_at_xk)
    assert calc_basic.ex_complete_from_table(age, 'pria', default_table, n_temp=n_temp, assumption_fractional='udd') == pytest.approx(expected_ex_complete_temp_udd_sum, abs=1e-1)

def test_e_sq_complete_from_table_core(calc_basic: ActuarialCalculator, default_table: MortalityTable):
    """Tes momen kedua complete future lifetime dari tabel (aproksimasi UDD)."""
    age = 90 
    ex_curtate = calc_basic.ex_curtate_from_table(age, 'pria', default_table)
    e_sq_curtate = calc_basic.e_sq_curtate_from_table(age, 'pria', default_table)
    expected_e_sq_complete_udd = e_sq_curtate + ex_curtate + (1.0/3.0)
    assert calc_basic.e_sq_complete_from_table(age, 'pria', default_table, assumption_fractional='udd') == pytest.approx(expected_e_sq_complete_udd, abs=1e-1)


# === Tes Metode Berbasis Asumsi ===
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
    t_px = calc_assumption_core.survival_probability_from_assumption(age, t, px_yearly_func, omega)
    t_plus_u_px = calc_assumption_core.survival_probability_from_assumption(age, t + u, px_yearly_func, omega)
    expected_val = t_px - t_plus_u_px # Menggunakan formula pengurangan
    
    actual_val = calc_assumption_core.deferred_death_probability_from_assumption(age, t, u, px_yearly_func, omega)
    assert actual_val == pytest.approx(expected_val)

def test_ex_curtate_from_assumption_core(calc_assumption_core: ActuarialCalculator):
    px_val = 0.95
    px_func_yearly = lambda age_input: px_val
    omega = 100 
    age = 98
    expected_ex = px_val + (px_val * px_val)
    assert calc_assumption_core.ex_curtate_from_assumption(age, px_func_yearly, omega) == pytest.approx(expected_ex)
    expected_ex_temp1 = px_val
    assert calc_assumption_core.ex_curtate_from_assumption(age, px_func_yearly, omega, n_temp=1) == pytest.approx(expected_ex_temp1)

def test_e_sq_curtate_from_assumption_core(calc_assumption_core: ActuarialCalculator):
    px_val = 0.9
    px_func_yearly = lambda age_input: px_val
    omega = 50 
    age = 48
    _1p_48 = px_val
    _2p_48 = px_val * px_val
    expected_e_sq = (1 * _1p_48) + (3 * _2p_48)
    assert calc_assumption_core.e_sq_curtate_from_assumption(age, px_func_yearly, omega) == pytest.approx(expected_e_sq)
    expected_e_sq_temp1 = 1 * _1p_48
    assert calc_assumption_core.e_sq_curtate_from_assumption(age, px_func_yearly, omega, n_temp=1) == pytest.approx(expected_e_sq_temp1)

def test_ex_complete_from_assumption_core(calc_assumption_core: ActuarialCalculator):
    qx_val = 0.02
    px_func = lambda age: 1.0 - qx_val
    qx_func_for_udd = lambda age: qx_val 
    omega = 110
    ex_curtate = calc_assumption_core.ex_curtate_from_assumption(30, px_func, omega)
    expected_ex_complete = ex_curtate + 0.5
    assert calc_assumption_core.ex_complete_from_assumption(30, px_func, qx_func_for_udd, omega, assumption_fractional='udd') == pytest.approx(expected_ex_complete)

def test_e_sq_complete_from_assumption_core(calc_assumption_core: ActuarialCalculator):
    qx_val = 0.02
    px_func = lambda age: 1.0 - qx_val
    qx_func_for_udd = lambda age: qx_val
    omega = 110
    ex_curtate = calc_assumption_core.ex_curtate_from_assumption(30, px_func, omega)
    e_sq_curtate = calc_assumption_core.e_sq_curtate_from_assumption(30, px_func, omega)
    expected_e_sq_complete = e_sq_curtate + ex_curtate + (1.0/3.0)
    assert calc_assumption_core.e_sq_complete_from_assumption(30, px_func, qx_func_for_udd, omega, assumption_fractional='udd') == pytest.approx(expected_e_sq_complete)