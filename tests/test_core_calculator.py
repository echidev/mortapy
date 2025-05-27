# tests/test_core_calculator.py
import pytest
from mortapy.tables.base import MortalityTable
from mortapy.core_calculator import ActuarialCalculator
import os
import math

# Path untuk memuat tabel default di fixture
TEST_TABLE_PATH = os.path.join(os.path.dirname(__file__), '..', 'mortapy', 'tables', 'tabel_mortalita_penduduk_indonesia_2023.csv')

@pytest.fixture
def default_table() -> MortalityTable:
    """Fixture untuk memuat tabel mortalita default."""
    # Perbaiki path jika error, ini asumsi dijalankan dari root proyek
    # atau sesuaikan dengan path _get_default_table di api_tables.py
    alt_path_from_project_root = os.path.join("mortapy", "tables", "tabel_mortalita_penduduk_indonesia_2023.csv")
    if os.path.exists(alt_path_from_project_root):
        return MortalityTable(alt_path_from_project_root)
    return MortalityTable(TEST_TABLE_PATH) # Fallback ke path lama jika ada

@pytest.fixture
def calc_with_table(default_table: MortalityTable) -> ActuarialCalculator:
    """Fixture untuk kalkulator yang menggunakan tabel."""
    return ActuarialCalculator(interest_rate=0.05)

# --- Tes untuk Metode Berbasis Tabel ---
def test_survival_prob_table_logic(calc_with_table: ActuarialCalculator, default_table: MortalityTable):
    """Tes logika dasar _n p_x dengan tabel."""
    assert calc_with_table.survival_probability_from_table(age=30, n_years=0, gender='pria', table=default_table) == 1.0
    p1 = calc_with_table.survival_probability_from_table(age=30, n_years=1, gender='pria', table=default_table)
    p2 = calc_with_table.survival_probability_from_table(age=30, n_years=2, gender='pria', table=default_table)
    assert p2 < p1
    assert 0 < p1 <= 1.0

def test_nsp_ax_table_logic(calc_with_table: ActuarialCalculator, default_table: MortalityTable):
    """Tes logika dasar A_x dengan tabel."""
    ax30 = calc_with_table.nsp_whole_life_from_table(age=30, gender='pria', table=default_table)
    ax50 = calc_with_table.nsp_whole_life_from_table(age=50, gender='pria', table=default_table)
    assert ax50 > ax30 # Premi lebih mahal untuk usia lebih tua
    assert ax30 > 0

def test_pv_annuity_table_logic(calc_with_table: ActuarialCalculator, default_table: MortalityTable):
    """Tes logika dasar ä_x dengan tabel."""
    adue30 = calc_with_table.pv_annuity_due_whole_life_from_table(age=30, gender='wanita', table=default_table)
    adue50 = calc_with_table.pv_annuity_due_whole_life_from_table(age=50, gender='wanita', table=default_table)
    assert adue30 > adue50 # Anuitas lebih mahal untuk usia lebih muda
    assert adue30 > 0

# --- Tes untuk Metode Berbasis Asumsi ---
@pytest.fixture
def calc_assumption() -> ActuarialCalculator:
    """Fixture untuk kalkulator tanpa tabel (hanya suku bunga)."""
    return ActuarialCalculator(interest_rate=0.05)

def test_survival_prob_assumption_constant_qx(calc_assumption: ActuarialCalculator):
    """Tes _n p_x dengan asumsi qx konstan."""
    qx_val = 0.01
    px_func = lambda age: 1.0 - qx_val
    omega = 120 # Asumsi omega untuk loop
    
    assert calc_assumption.survival_probability_from_assumption(age=30, n_years=0, px_function=px_func, omega=omega) == 1.0
    val_2p30 = calc_assumption.survival_probability_from_assumption(age=30, n_years=2, px_function=px_func, omega=omega)
    assert val_2p30 == pytest.approx((1.0 - qx_val)**2)

def test_nsp_assumption_constant_qx(calc_assumption: ActuarialCalculator):
    qx_val = 0.02
    qx_func = lambda age_input: qx_val # qx konstan
    px_func = lambda age_input: 1.0 - qx_val # px konstan
    omega = 110 # <-- Omega yang digunakan oleh fungsi
    
    ax30 = calc_assumption.nsp_whole_life_from_assumption(
        age=30, 
        qx_function=qx_func, 
        px_function=px_func, 
        omega=omega # <-- Pastikan omega ini diteruskan
    )
    assert ax30 > 0
    
    # Formula closed-form untuk Ax dengan qx dan px konstan, periode tak hingga
    expected_ax_infinite = (qx_val * calc_assumption.v) / (1 - ((1.0 - qx_val) * calc_assumption.v))
    
    # Kita tahu hasil dari fungsi kita (dengan omega=110) akan sedikit lebih kecil
    # daripada formula tak hingga. Daripada membandingkan kesamaan absolut,
    # kita bisa cek apakah hasilnya "cukup dekat" atau menghitungnya dengan loop terbatas.

    # Untuk presisi, kita hitung manual dengan loop terbatas yang sama di tes:
    expected_ax_finite = 0.0
    p_val = 1.0 - qx_val
    # Loop dari k=0 hingga omega-age-1 = 110-30-1 = 79
    for k in range(omega - 30): 
        prob_survive_k_years = p_val ** k
        prob_die_next_year = qx_val
        discounted_benefit = (calc_assumption.v ** (k + 1)) * prob_survive_k_years * prob_die_next_year
        expected_ax_finite += discounted_benefit
        if prob_survive_k_years * p_val == 0 and k > 0: # jika prob hidup berikutnya 0
             break

    assert ax30 == pytest.approx(expected_ax_finite)


# TODO: Tambahkan tes untuk pv_annuity_due_whole_life_from_assumption
# TODO: Tambahkan tes untuk asumsi De Moivre dan CFM Constant Mu di core_calculator