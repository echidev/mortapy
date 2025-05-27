# tests/test_core_calculator.py
import pytest
from mortapy.tables.base import MortalityTable
from mortapy.core_calculator import ActuarialCalculator
import os
import math

# Path untuk memuat tabel default di fixture
TEST_TABLE_PATH_DEFAULT = os.path.join("mortapy", "tables", "tabel_mortalita_penduduk_indonesia_2023.csv")
if not os.path.exists(TEST_TABLE_PATH_DEFAULT): 
    TEST_TABLE_PATH_DEFAULT = os.path.join(os.path.dirname(__file__), '..', 'mortapy', 'tables', 'tabel_mortalita_penduduk_indonesia_2023.csv')

@pytest.fixture
def default_table() -> MortalityTable:
    return MortalityTable(TEST_TABLE_PATH_DEFAULT)

@pytest.fixture
def calc_with_table(default_table: MortalityTable) -> ActuarialCalculator:
    # Meskipun kalkulator hanya butuh interest_rate, kita buat fixture ini 
    # agar mudah digunakan dengan metode _from_table nanti.
    # Metode _from_table akan menerima 'table' sebagai argumen.
    return ActuarialCalculator(interest_rate=0.05)

# --- Tes untuk Metode Berbasis Tabel ---
def test_survival_prob_table_logic(calc_with_table: ActuarialCalculator, default_table: MortalityTable):
    assert calc_with_table.survival_probability_from_table(age=30, n_years=0, gender='pria', table=default_table) == 1.0
    p1 = calc_with_table.survival_probability_from_table(age=30, n_years=1, gender='pria', table=default_table)
    p2 = calc_with_table.survival_probability_from_table(age=30, n_years=2, gender='pria', table=default_table)
    assert p2 < p1 if p1 > 0 else p2 == p1 # Handle jika p1 sudah 0
    assert 0 <= p1 <= 1.0

def test_nsp_ax_table_logic(calc_with_table: ActuarialCalculator, default_table: MortalityTable):
    ax30 = calc_with_table.nsp_whole_life_from_table(age=30, gender='pria', table=default_table)
    ax50 = calc_with_table.nsp_whole_life_from_table(age=50, gender='pria', table=default_table)
    assert ax50 > ax30 if ax30 < 1 else ax50 <= ax30 # Jika ax30 sudah 1 (misal i=0 dan qx=1)
    assert ax30 >= 0

def test_pv_annuity_table_logic(calc_with_table: ActuarialCalculator, default_table: MortalityTable):
    adue30 = calc_with_table.pv_annuity_due_whole_life_from_table(age=30, gender='wanita', table=default_table)
    adue50 = calc_with_table.pv_annuity_due_whole_life_from_table(age=50, gender='wanita', table=default_table)
    assert adue30 > adue50
    assert adue30 > 0

# --- Tes untuk Metode Berbasis Asumsi ---
@pytest.fixture
def calc_assumption_core() -> ActuarialCalculator:
    return ActuarialCalculator(interest_rate=0.05)

def test_survival_prob_assumption_core_constant_qx(calc_assumption_core: ActuarialCalculator):
    qx_val = 0.01
    px_func = lambda age_input: 1.0 - qx_val
    omega = 120
    
    assert calc_assumption_core.survival_probability_from_assumption(age=30, n_years=0, px_function_yearly=px_func, omega=omega) == 1.0
    # Tes untuk n_years float (menggunakan CFM untuk fraksional)
    val_2p5_30 = calc_assumption_core.survival_probability_from_assumption(age=30, n_years=2.5, px_function_yearly=px_func, omega=omega)
    expected_val = ((1.0 - qx_val)**2) * ((1.0 - qx_val)**0.5) # p^2 * p^0.5 (CFM)
    assert val_2p5_30 == pytest.approx(expected_val)

def test_nsp_assumption_core_constant_qx(calc_assumption_core: ActuarialCalculator):
    qx_val = 0.02
    qx_func = lambda age_input: qx_val
    px_func = lambda age_input: 1.0 - qx_val
    omega = 110
    
    ax30 = calc_assumption_core.nsp_whole_life_from_assumption(age=30, qx_function=qx_func, px_function=px_func, omega=omega)
    assert ax30 > 0
    
    expected_ax_finite = 0.0
    p_val = 1.0 - qx_val
    for k in range(omega - 30): 
        prob_survive_k_years = p_val ** k # Untuk px konstan
        prob_die_next_year = qx_val
        discounted_benefit = (calc_assumption_core.v ** (k + 1)) * prob_survive_k_years * prob_die_next_year
        expected_ax_finite += discounted_benefit
        if prob_survive_k_years * p_val == 0 and k > 0:
             break
    assert ax30 == pytest.approx(expected_ax_finite)