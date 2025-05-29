# tests/test_core_calculator.py
import pytest
from mortapy.tables.base import MortalityTable
from mortapy.core_calculator import ActuarialCalculator
import os
import math
from typing import Callable, Literal, Optional, List

# Logika path untuk TEST_TABLE_PATH_DEFAULT
try:
    # Mencoba path relatif dari root proyek jika CWD adalah root proyek
    path_candidate_project_root = os.path.join(os.getcwd(), "mortapy", "tables", "tabel_mortalita_penduduk_indonesia_2023.csv")
    # Mencoba path relatif dari folder tests
    path_candidate_from_tests = os.path.join(os.path.dirname(__file__), '..', 'mortapy', 'tables', 'tabel_mortalita_penduduk_indonesia_2023.csv')

    if "GITHUB_WORKSPACE" in os.environ: # Khusus untuk GitHub Actions
        TEST_TABLE_PATH_DEFAULT = os.path.join(os.environ["GITHUB_WORKSPACE"], "mortapy", "tables", "tabel_mortalita_penduduk_indonesia_2023.csv")
    elif os.path.exists(path_candidate_project_root) and "mortapy" == os.path.basename(os.getcwd()):
         TEST_TABLE_PATH_DEFAULT = path_candidate_project_root
    elif os.path.exists(path_candidate_from_tests):
        TEST_TABLE_PATH_DEFAULT = path_candidate_from_tests
    else: # Fallback
        TEST_TABLE_PATH_DEFAULT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mortapy', 'tables', 'tabel_mortalita_penduduk_indonesia_2023.csv')
        if not os.path.exists(TEST_TABLE_PATH_DEFAULT):
            TEST_TABLE_PATH_DEFAULT = "mortapy/tables/tabel_mortalita_penduduk_indonesia_2023.csv" # Last resort
except Exception:
    TEST_TABLE_PATH_DEFAULT = "mortapy/tables/tabel_mortalita_penduduk_indonesia_2023.csv"


@pytest.fixture
def default_table() -> MortalityTable:
    """Fixture untuk memuat tabel mortalita default (hanya ultima)."""
    return MortalityTable(ultimate_file_path=TEST_TABLE_PATH_DEFAULT)

@pytest.fixture
def calc_basic() -> ActuarialCalculator:
    """Fixture untuk kalkulator dasar hanya dengan suku bunga."""
    return ActuarialCalculator(interest_rate=0.05)

@pytest.fixture
def simple_ultimate_table_for_core(tmp_path) -> MortalityTable:
    """Membuat objek MortalityTable dengan data ultima dummy untuk tes core."""
    ultimate_content = ("x,qx_pria,qx_wanita\n"
                        "95,0.2,0.15\n"
                        "96,0.3,0.25\n"
                        "97,0.5,0.4\n"
                        "98,0.8,0.7\n"
                        "99,1.0,1.0\n")
    ultimate_p = tmp_path / "dummy_ult_core.csv"
    ultimate_p.write_text(ultimate_content)
    return MortalityTable(ultimate_file_path=str(ultimate_p))

@pytest.fixture
def simple_select_ultimate_table_for_core(tmp_path) -> MortalityTable:
    """Membuat objek MortalityTable dengan data seleksi dan ultima dummy untuk tes core."""
    ultimate_content = ("x,qx_pria,qx_wanita\n"
                        "60,0.10,0.09\n"
                        "61,0.12,0.11\n"
                        "62,0.15,0.14\n" # Efek seleksi dari [60] berakhir di sini jika select_duration=2
                        "63,0.18,0.17\n" # Efek seleksi dari [61] berakhir di sini jika select_duration=2
                        "64,1.0,1.0\n") # Max age ultima
    ultimate_p = tmp_path / "dummy_ult_core_sel.csv"
    ultimate_p.write_text(ultimate_content)

    select_content = ("age_select,d0_pria,d0_wanita,d1_pria,d1_wanita\n"
                      "60,0.05,0.04,0.08,0.06\n"  # q_[60], q_[60]+1
                      "61,0.07,0.05,0.10,0.07\n") # q_[61], q_[61]+1
    select_p = tmp_path / "dummy_sel_core.csv"
    select_p.write_text(select_content)
    
    return MortalityTable(
        ultimate_file_path=str(ultimate_p), 
        select_file_path=str(select_p), 
        select_duration=2 # Periode seleksi 2 tahun
    )

# === Tes untuk Metode Berbasis Tabel ===
def test_survival_probability_from_table_core(calc_basic: ActuarialCalculator, default_table: MortalityTable):
    """Tes _n p_x dengan tabel dari core (menggunakan parameter nama baru)."""
    assert calc_basic.survival_probability_from_table(attained_age_start=30, n_years=0, gender='pria', table=default_table) == 1.0
    p1 = calc_basic.survival_probability_from_table(attained_age_start=30, n_years=1, gender='pria', table=default_table)
    p2 = calc_basic.survival_probability_from_table(attained_age_start=30, n_years=2, gender='pria', table=default_table)
    assert p2 < p1 if p1 > 0 else p2 == p1
    assert 0 <= p1 <= 1.0
    assert calc_basic.survival_probability_from_table(attained_age_start=default_table.max_age_ultimate + 1, n_years=1, gender='pria', table=default_table) == 0.0

def test_survival_probability_from_table_core_select(calc_basic: ActuarialCalculator, simple_select_ultimate_table_for_core: MortalityTable):
    """Tes _n p_[x]+t dengan tabel seleksi dari core."""
    table = simple_select_ultimate_table_for_core
    age_select = 60
    gender: Literal["pria", "wanita"] = 'pria'

    # Kasus 1: Seluruhnya dalam periode seleksi
    # _2 p_[60] = p_[60] * p_[60]+1
    # q_[60]_pria   = 0.05 -> p_[60]_pria   = 0.95
    # q_[60]+1_pria = 0.08 -> p_[60]+1_pria = 0.92
    # _2 p_[60]_pria = 0.95 * 0.92 = 0.874
    assert calc_basic.survival_probability_from_table(
        attained_age_start=60, n_years=2, gender=gender, table=table, 
        age_at_selection=age_select, initial_duration_selected=0
    ) == pytest.approx(0.95 * 0.92)

    # Kasus 2: Dimulai dari seleksi, berakhir di ultima
    # _3 p_[60] = p_[60] * p_[60]+1 * p_62 (ultima)
    # q_62_pria (ultima) = 0.15 -> p_62_pria = 0.85
    # _3 p_[60]_pria = 0.95 * 0.92 * 0.85
    assert calc_basic.survival_probability_from_table(
        attained_age_start=60, n_years=3, gender=gender, table=table, 
        age_at_selection=age_select, initial_duration_selected=0
    ) == pytest.approx(0.95 * 0.92 * 0.85)

def test_death_probability_from_table_core(calc_basic: ActuarialCalculator, default_table: MortalityTable):
    age, n, gender = 30, 2, 'pria'
    p_val = calc_basic.survival_probability_from_table(attained_age_start=age, n_years=n, gender=gender, table=default_table)
    q_val = calc_basic.death_probability_from_table(attained_age_start=age, n_years=n, gender=gender, table=default_table)
    assert q_val == pytest.approx(1.0 - p_val)

# ... (Tes lain untuk deferred_death, fom, pdf, nsp, pv_annuity dengan parameter seleksi jika relevan) ...
def test_ex_curtate_from_table_core(calc_basic: ActuarialCalculator, simple_ultimate_table_for_core: MortalityTable):
    table = simple_ultimate_table_for_core
    # e_98 (pria) = p_98 = 1 - q_98 = 1 - 0.8 = 0.2 (karena q_99 = 1.0)
    # max_age_ultimate = 99, omega-x = 99-98 = 1. Loop k=1.
    # k=1: _1p_98 = p_98
    assert calc_basic.ex_curtate_from_table(98, 'pria', table) == pytest.approx(1.0 - 0.8)
    # e_{97:1|} (pria) = p_97 = 1 - 0.5 = 0.5
    assert calc_basic.ex_curtate_from_table(97, 'pria', table, n_temp=1) == pytest.approx(1.0 - 0.5)

def test_e_sq_curtate_from_table_core(calc_basic: ActuarialCalculator, simple_ultimate_table_for_core: MortalityTable):
    table = simple_ultimate_table_for_core
    # E[K_97^2] (pria) = (2*0+1)*_1p_97 + (2*1+1)*_2p_97
    # _1p_97 = 0.5
    # _2p_97 = p_97 * p_98 = 0.5 * 0.2 = 0.1
    # E[K_97^2] = 1*0.5 + 3*0.1 = 0.5 + 0.3 = 0.8
    assert calc_basic.e_sq_curtate_from_table(97, 'pria', table) == pytest.approx(0.8)

def test_ex_complete_from_table_core(calc_basic: ActuarialCalculator, simple_ultimate_table_for_core: MortalityTable):
    table = simple_ultimate_table_for_core
    age = 97
    gender = 'pria'
    # e_circ_97 (UDD) = sum_{k=0}^{omega-x-1} _k p_x (1 - 0.5 q_{x+k})
    # omega-x-1 = 99-97-1 = 1. Loop k=0, 1.
    # k=0: _0p_97 * (1 - 0.5*q_97) = 1 * (1 - 0.5*0.5) = 1 - 0.25 = 0.75
    # k=1: _1p_97 * (1 - 0.5*q_98) = 0.5 * (1 - 0.5*0.8) = 0.5 * (1-0.4) = 0.5 * 0.6 = 0.3
    # e_circ_97 = 0.75 + 0.3 = 1.05
    assert calc_basic.ex_complete_from_table(age, gender, table, assumption_fractional='udd') == pytest.approx(1.05)
    # Aproksimasi e_x + 0.5 = 0.6 + 0.5 = 1.1 (dekat)

def test_e_sq_complete_from_table_core(calc_basic: ActuarialCalculator, simple_ultimate_table_for_core: MortalityTable):
    age = 97
    gender = 'pria'
    ex_curtate = calc_basic.ex_curtate_from_table(age, gender, simple_ultimate_table_for_core) # 0.6
    e_sq_curtate = calc_basic.e_sq_curtate_from_table(age, gender, simple_ultimate_table_for_core) # 0.8
    # Aproksimasi UDD: E[T_x^2] ~ E[K_x^2] + e_x + 1/3
    expected_e_sq_complete = e_sq_curtate + ex_curtate + (1.0/3.0) # 0.8 + 0.6 + 0.333... = 1.7333...
    assert calc_basic.e_sq_complete_from_table(age, gender, simple_ultimate_table_for_core, assumption_fractional='udd') == pytest.approx(expected_e_sq_complete, abs=1e-1)


# === Tes Metode Berbasis Asumsi (tidak ada perubahan signifikan di sini) ===
@pytest.fixture
def calc_assumption_core() -> ActuarialCalculator:
    return ActuarialCalculator(interest_rate=0.05)

def test_survival_probability_from_assumption_core(calc_assumption_core: ActuarialCalculator):
    qx_val = 0.01; px_func_yearly = lambda age_input: 1.0 - qx_val; omega = 120
    assert calc_assumption_core.survival_probability_from_assumption(30, 2.0, px_func_yearly, omega) == pytest.approx((1.0-qx_val)**2)
    expected_cfm = ((1.0-qx_val)**2) * ((1.0-qx_val)**0.5)
    assert calc_assumption_core.survival_probability_from_assumption(30, 2.5, px_func_yearly, omega, 'cfm') == pytest.approx(expected_cfm)
    expected_udd = ((1.0-qx_val)**2) * (1.0 - 0.5 * qx_val)
    assert calc_assumption_core.survival_probability_from_assumption(30, 2.5, px_func_yearly, omega, 'udd') == pytest.approx(expected_udd)

def test_death_probability_from_assumption_core(calc_assumption_core: ActuarialCalculator):
    px_func = lambda age_input: 0.98; omega = 110; n_years = 2.5
    tpx = calc_assumption_core.survival_probability_from_assumption(30, n_years, px_func, omega)
    tqx = calc_assumption_core.death_probability_from_assumption(30, n_years, px_func, omega)
    assert tqx == pytest.approx(1.0 - tpx)

def test_deferred_death_probability_from_assumption_core(calc_assumption_core: ActuarialCalculator):
    px_yearly_func = lambda age_input: 0.95; omega = 100; age, t, u = 40, 2.5, 3.5
    t_px = calc_assumption_core.survival_probability_from_assumption(age, t, px_yearly_func, omega)
    # _u q_{x+t} = 1 - (_(t+u)p_x / _t p_x)
    t_plus_u_px = calc_assumption_core.survival_probability_from_assumption(age, t + u, px_yearly_func, omega)
    u_qx_xt = 1.0 - (t_plus_u_px / t_px if abs(t_px) > 1e-12 else 0.0)
    expected_val = t_px * u_qx_xt
    
    actual_val = calc_assumption_core.deferred_death_probability_from_assumption(age, t, u, px_yearly_func, omega)
    assert actual_val == pytest.approx(expected_val)

def test_ex_curtate_from_assumption_core(calc_assumption_core: ActuarialCalculator):
    px_val = 0.95; px_func_yearly = lambda age_input: px_val; omega = 100; age = 98
    expected_ex = px_val + (px_val * px_val)
    assert calc_assumption_core.ex_curtate_from_assumption(age, px_func_yearly, omega) == pytest.approx(expected_ex)

def test_e_sq_curtate_from_assumption_core(calc_assumption_core: ActuarialCalculator):
    px_val = 0.9; px_func_yearly = lambda age_input: px_val; omega = 50; age = 48
    _1p_48 = px_val; _2p_48 = px_val * px_val
    expected_e_sq = (1 * _1p_48) + (3 * _2p_48)
    assert calc_assumption_core.e_sq_curtate_from_assumption(age, px_func_yearly, omega) == pytest.approx(expected_e_sq)

def test_ex_complete_from_assumption_core(calc_assumption_core: ActuarialCalculator):
    qx_val = 0.02; px_func = lambda age: 1.0 - qx_val; qx_func_for_udd = lambda age: qx_val; omega = 110
    ex_curtate = calc_assumption_core.ex_curtate_from_assumption(30, px_func, omega)
    expected_ex_complete = ex_curtate + 0.5
    assert calc_assumption_core.ex_complete_from_assumption(30, px_func, qx_func_for_udd, omega, assumption_fractional='udd') == pytest.approx(expected_ex_complete)

def test_e_sq_complete_from_assumption_core(calc_assumption_core: ActuarialCalculator):
    qx_val = 0.02; px_func = lambda age: 1.0 - qx_val; qx_func_for_udd = lambda age: qx_val; omega = 110
    ex_curtate = calc_assumption_core.ex_curtate_from_assumption(30, px_func, omega)
    e_sq_curtate = calc_assumption_core.e_sq_curtate_from_assumption(30, px_func, omega)
    expected_e_sq_complete = e_sq_curtate + ex_curtate + (1.0/3.0)
    assert calc_assumption_core.e_sq_complete_from_assumption(30, px_func, qx_func_for_udd, omega, assumption_fractional='udd') == pytest.approx(expected_e_sq_complete)