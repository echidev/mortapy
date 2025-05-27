# tests/test_core_calculator.py
import pytest
from mortapy.tables.base import MortalityTable
from mortapy.core_calculator import ActuarialCalculator
import os
import math
from typing import Callable # Diperlukan untuk type hint px_function_yearly

# Path untuk memuat tabel default di fixture
# (Menggunakan logika path yang sama dengan test_tables.py)
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
def calc_with_table_fixture(default_table: MortalityTable) -> ActuarialCalculator:
    """Fixture untuk kalkulator yang akan digunakan dengan metode berbasis tabel."""
    return ActuarialCalculator(interest_rate=0.05)

# --- Tes untuk Metode Berbasis Tabel ---
def test_survival_probability_from_table_logic(calc_with_table_fixture: ActuarialCalculator, default_table: MortalityTable):
    """Tes logika dasar _n p_x dengan tabel."""
    calc = calc_with_table_fixture
    table = default_table
    assert calc.survival_probability_from_table(age=30, n_years=0, gender='pria', table=table) == 1.0
    p1 = calc.survival_probability_from_table(age=30, n_years=1, gender='pria', table=table)
    p2 = calc.survival_probability_from_table(age=30, n_years=2, gender='pria', table=table)
    assert p2 < p1 if p1 > 0 else p2 == p1 # Handle jika p1 sudah 0
    assert 0 <= p1 <= 1.0
    # Tes batas usia
    assert calc.survival_probability_from_table(age=table.max_age, n_years=1, gender='pria', table=table) == pytest.approx(1.0 - table.qx(table.max_age, 'pria'))
    assert calc.survival_probability_from_table(age=table.max_age + 1, n_years=1, gender='pria', table=table) == 0.0


def test_death_probability_from_table_logic(calc_with_table_fixture: ActuarialCalculator, default_table: MortalityTable):
    """Tes _n q_x dengan tabel."""
    calc = calc_with_table_fixture
    table = default_table
    age = 30
    n = 2
    p_val = calc.survival_probability_from_table(age, n, 'pria', table)
    q_val = calc.death_probability_from_table(age, n, 'pria', table)
    assert q_val == pytest.approx(1.0 - p_val)
    assert 0 <= q_val <= 1.0

def test_deferred_death_probability_from_table_logic(calc_with_table_fixture: ActuarialCalculator, default_table: MortalityTable):
    """Tes _{t|u}q_x dengan tabel."""
    calc = calc_with_table_fixture
    table = default_table
    age = 30
    defer_t = 2
    death_u = 3
    # t|u_qx = t_px - t+u_px
    t_px = calc.survival_probability_from_table(age, defer_t, 'pria', table)
    t_plus_u_px = calc.survival_probability_from_table(age, defer_t + death_u, 'pria', table)
    expected_val = t_px - t_plus_u_px
    
    actual_val = calc.deferred_death_probability_from_table(age, defer_t, death_u, 'pria', table)
    assert actual_val == pytest.approx(expected_val)
    assert 0 <= actual_val <= 1.0


def test_nsp_ax_table_logic(calc_with_table_fixture: ActuarialCalculator, default_table: MortalityTable):
    """Tes logika dasar A_x dengan tabel."""
    calc = calc_with_table_fixture
    table = default_table
    ax30 = calc.nsp_whole_life_from_table(age=30, gender='pria', table=table)
    ax50 = calc.nsp_whole_life_from_table(age=50, gender='pria', table=table)
    # Asumsi suku bunga positif
    assert ax50 > ax30 if ax30 < 1 else ax50 <= ax30 
    assert ax30 >= 0

def test_pv_annuity_table_logic(calc_with_table_fixture: ActuarialCalculator, default_table: MortalityTable):
    """Tes logika dasar ä_x dengan tabel."""
    calc = calc_with_table_fixture
    table = default_table
    adue30 = calc.pv_annuity_due_whole_life_from_table(age=30, gender='wanita', table=table)
    adue50 = calc.pv_annuity_due_whole_life_from_table(age=50, gender='wanita', table=default_table)
    assert adue30 > adue50
    assert adue30 > 0

# --- Tes untuk Metode Berbasis Asumsi ---
@pytest.fixture
def calc_assumption_core() -> ActuarialCalculator:
    """Fixture untuk kalkulator yang akan digunakan dengan metode berbasis asumsi."""
    return ActuarialCalculator(interest_rate=0.05)

def test_survival_prob_assumption_core_constant_qx(calc_assumption_core: ActuarialCalculator):
    """Tes _n p_x dengan asumsi qx konstan, termasuk periode fraksional."""
    qx_val = 0.01
    px_func_yearly = lambda age_input: 1.0 - qx_val
    omega = 120 
    
    assert calc_assumption_core.survival_probability_from_assumption(age=30, n_years=0, px_function_yearly=px_func_yearly, omega=omega) == 1.0
    
    # Tes periode bulat
    val_2p30_int = calc_assumption_core.survival_probability_from_assumption(age=30, n_years=2.0, px_function_yearly=px_func_yearly, omega=omega)
    assert val_2p30_int == pytest.approx((1.0 - qx_val)**2)

    # Tes periode non-bulat (menggunakan CFM untuk fraksional by default)
    val_2p5_30_float = calc_assumption_core.survival_probability_from_assumption(age=30, n_years=2.5, px_function_yearly=px_func_yearly, omega=omega)
    expected_val_cfm_frac = ((1.0 - qx_val)**2) * ((1.0 - qx_val)**0.5) 
    assert val_2p5_30_float == pytest.approx(expected_val_cfm_frac)

    # Tes periode non-bulat dengan UDD untuk fraksional
    val_2p5_30_udd_frac = calc_assumption_core.survival_probability_from_assumption(age=30, n_years=2.5, px_function_yearly=px_func_yearly, omega=omega, assumption_type_for_fractional='udd')
    px_base_for_udd = 1.0 - qx_val
    qx_base_for_udd = qx_val
    expected_val_udd_frac = (px_base_for_udd**2) * (1.0 - 0.5 * qx_base_for_udd)
    assert val_2p5_30_udd_frac == pytest.approx(expected_val_udd_frac)


def test_death_prob_assumption_core_constant_qx(calc_assumption_core: ActuarialCalculator):
    """Tes _n q_x dengan asumsi qx konstan."""
    qx_val = 0.01
    px_func_yearly = lambda age_input: 1.0 - qx_val
    omega = 120
    n = 2.5
    
    val_nqx = calc_assumption_core.death_probability_from_assumption(age=30, n_years=n, px_function_yearly=px_func_yearly, omega=omega)
    val_npx = calc_assumption_core.survival_probability_from_assumption(age=30, n_years=n, px_function_yearly=px_func_yearly, omega=omega)
    assert val_nqx == pytest.approx(1.0 - val_npx)


def test_deferred_death_prob_assumption_core_constant_qx(calc_assumption_core: ActuarialCalculator):
    """Tes _{t|u}q_x dengan asumsi qx konstan."""
    qx_val = 0.01
    px_func_yearly = lambda age_input: 1.0 - qx_val
    omega = 120
    age = 30
    defer_t = 2.0 # Bisa float
    death_u = 3.5 # Bisa float
    
    # t_px
    t_px = calc_assumption_core.survival_probability_from_assumption(age, defer_t, px_func_yearly, omega)
    # t+u_px
    t_plus_u_px = calc_assumption_core.survival_probability_from_assumption(age, defer_t + death_u, px_func_yearly, omega)
    expected_val = t_px - t_plus_u_px
    
    actual_val = calc_assumption_core.deferred_death_probability_from_assumption(age, defer_t, death_u, px_func_yearly, omega)
    assert actual_val == pytest.approx(expected_val)


def test_nsp_assumption_core_constant_qx(calc_assumption_core: ActuarialCalculator):
    """Tes A_x dengan asumsi qx konstan."""
    qx_val = 0.02
    qx_func = lambda age_input: qx_val
    px_func = lambda age_input: 1.0 - qx_val
    omega = 110
    
    ax30 = calc_assumption_core.nsp_whole_life_from_assumption(age=30, qx_function=qx_func, px_function=px_func, omega=omega)
    assert ax30 > 0
    
    expected_ax_finite = 0.0
    p_val = 1.0 - qx_val
    for k in range(omega - 30): 
        # Menggunakan survival_probability_from_assumption untuk _k p_x
        prob_survive_k_years = calc_assumption_core.survival_probability_from_assumption(30, float(k), px_func, omega)
        prob_die_next_year = qx_val
        discounted_benefit = (calc_assumption_core.v ** (k + 1)) * prob_survive_k_years * prob_die_next_year
        expected_ax_finite += discounted_benefit
        if prob_survive_k_years * p_val == 0 and k > 0:
             break
    assert ax30 == pytest.approx(expected_ax_finite)

# TODO: Tambahkan tes untuk pv_annuity_due_whole_life_from_assumption
# TODO: Tambahkan tes untuk asumsi De Moivre, CFM, Gompertz, Makeham di core_calculator