# tests/test_api_tables.py
import pytest
from mortapy import (
    nsp_wl_table, pv_annuity_due_wl_table, survival_prob_table,
    death_prob_table, deferred_death_prob_table, fom_table, pdf_death_table,
    ex_curtate_table, e_sq_curtate_table, var_k_table,
    ex_complete_table, e_sq_complete_table, var_t_table, 
    load_default_table, MortalityTable
)
from mortapy.core_calculator import ActuarialCalculator # <<< DIPERBAIKI IMPORNYA
from mortapy.result import ActuarialResult
import os
import math
from typing import Literal, Optional, Any

# (Logika path TEST_TABLE_PATH_DEFAULT_API dan Parameter umum tetap sama)
# ... (salin dari respons sebelumnya) ...
try:
    path_candidate_1 = os.path.join("mortapy", "tables", "tabel_mortalita_penduduk_indonesia_2023.csv")
    path_candidate_2 = os.path.join(os.path.dirname(__file__), '..', 'mortapy', 'tables', 'tabel_mortalita_penduduk_indonesia_2023.csv')
    if os.path.exists(path_candidate_1):
        TEST_TABLE_PATH_DEFAULT_API = path_candidate_1
    elif os.path.exists(path_candidate_2):
        TEST_TABLE_PATH_DEFAULT_API = path_candidate_2
    else:
        TEST_TABLE_PATH_DEFAULT_API = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mortapy', 'tables', 'tabel_mortalita_penduduk_indonesia_2023.csv')
        if not os.path.exists(TEST_TABLE_PATH_DEFAULT_API):
            TEST_TABLE_PATH_DEFAULT_API = "mortapy/tables/tabel_mortalita_penduduk_indonesia_2023.csv"
except Exception:
    TEST_TABLE_PATH_DEFAULT_API = "mortapy/tables/tabel_mortalita_penduduk_indonesia_2023.csv"

AGE_API_TABLE = 35
INTEREST_RATE_API_TABLE = 0.05
GENDER_API_TABLE: Literal["pria", "wanita"] = 'pria'
N_YEARS_API_TABLE = 5
DEFER_T_API_TABLE = 2
DEATH_U_API_TABLE = 3
T_OFFSET_API_TABLE = 0.5
N_TEMP_MOMENT_TABLE = 3

@pytest.fixture # Tambahkan fixture jika belum ada untuk simple_mortality_table_obj
def simple_mortality_table_path(tmp_path) -> str:
    content = ("x,qx_pria,qx_wanita\n"
               "95,0.2,0.15\n96,0.3,0.25\n97,0.5,0.4\n98,0.8,0.7\n99,1.0,1.0\n")
    file_path = tmp_path / "simple_table.csv"
    file_path.write_text(content)
    return str(file_path)

@pytest.fixture
def simple_mortality_table_obj(simple_mortality_table_path: str) -> MortalityTable:
    return MortalityTable(simple_mortality_table_path)


def _build_expected_latex_subscript(base_val: Any, gender_val: Optional[str] = None, is_gender_table: bool = False, n_temp: Optional[int] = None) -> str:
    subscript = str(base_val)
    if n_temp is not None:
        subscript += rf":\overline{{{n_temp}}}|"
    if is_gender_table and gender_val:
        subscript += rf"; \text{{{gender_val.lower()}}}"
    return subscript

# ... (Semua fungsi tes yang sudah ada dari nsp_wl_table_default hingga var_k_table_default
#      tetap ada di sini. Saya hanya akan menambahkan tes baru untuk momen complete.)

def test_ex_complete_table_default(simple_mortality_table_obj: MortalityTable): # Menggunakan tabel simpel untuk verifikasi
    """Tes ekspektasi complete future lifetime dari tabel."""
    age = 97
    gender: Literal["pria", "wanita"] = 'pria'
    # e_circ_97 (pria) = e_97 + 0.5 (aproksimasi UDD)
    # e_97 = p_97 + _2p_97 = 0.5 + 0.1 = 0.6
    # e_circ_97 approx 0.6 + 0.5 = 1.1
    result_wl = ex_complete_table(
        age=age, 
        interest_rate=INTEREST_RATE_API_TABLE, 
        gender=gender,
        mortality_table=simple_mortality_table_obj,
        assumption_fractional='udd'
    )
    assert isinstance(result_wl, ActuarialResult)
    ex_curt_val = ActuarialCalculator(INTEREST_RATE_API_TABLE).ex_curtate_from_table(age, gender, simple_mortality_table_obj)
    assert result_wl.value == pytest.approx(ex_curt_val + 0.5) # Verifikasi aproksimasi
    expected_sub_wl = _build_expected_latex_subscript(age, gender, simple_mortality_table_obj.has_gender_columns)
    assert result_wl.formula_latex == rf"\mathring{{e}}_{{{expected_sub_wl}}}"

    # Tes temporary
    n_temp = 1
    result_temp = ex_complete_table(
        age=age, interest_rate=INTEREST_RATE_API_TABLE, gender=gender, 
        mortality_table=simple_mortality_table_obj, n_temp=n_temp, assumption_fractional='udd'
    )
    # e_circ_{97:1|} (UDD) = _0p_97 * (1 - 0.5*q_97) = 1 * (1 - 0.5 * 0.5) = 1 - 0.25 = 0.75
    assert isinstance(result_temp, ActuarialResult)
    assert result_temp.value == pytest.approx(0.75)
    expected_sub_temp = _build_expected_latex_subscript(age, gender, simple_mortality_table_obj.has_gender_columns, n_temp=n_temp)
    assert result_temp.formula_latex == rf"\mathring{{e}}_{{{expected_sub_temp}}}"


def test_e_sq_complete_table_default(simple_mortality_table_obj: MortalityTable):
    """Tes momen kedua complete future lifetime dari tabel (aproksimasi UDD)."""
    age = 97
    gender: Literal["pria","wanita"] = 'pria'
    result_wl = e_sq_complete_table(
        age=age, interest_rate=INTEREST_RATE_API_TABLE, gender=gender,
        mortality_table=simple_mortality_table_obj, assumption_fractional='udd'
    )
    assert isinstance(result_wl, ActuarialResult)
    # E[T_x^2] approx E[K_x^2] + e_x + 1/3
    # e_97 = 0.6, E[K_97^2] = 0.8
    # E[T_97^2] approx 0.8 + 0.6 + 1/3 = 1.4 + 0.333... = 1.7333...
    ex_curt_val = ActuarialCalculator(INTEREST_RATE_API_TABLE).ex_curtate_from_table(age, gender, simple_mortality_table_obj)
    e_sq_curt_val = ActuarialCalculator(INTEREST_RATE_API_TABLE).e_sq_curtate_from_table(age, gender, simple_mortality_table_obj)
    assert result_wl.value == pytest.approx(e_sq_curt_val + ex_curt_val + (1.0/3.0), abs=1e-1)
    
    table = simple_mortality_table_obj # Untuk has_gender_columns
    expected_sub_wl = _build_expected_latex_subscript(age, gender, table.has_gender_columns)
    assert result_wl.formula_latex == rf"E[T_{{{expected_sub_wl}}}^2]"

def test_var_t_table_default(simple_mortality_table_obj: MortalityTable):
    """Tes variansi complete future lifetime dari tabel."""
    age = 97
    gender: Literal["pria","wanita"] = 'pria'
    result_wl = var_t_table(
        age=age, interest_rate=INTEREST_RATE_API_TABLE, gender=gender,
        mortality_table=simple_mortality_table_obj, assumption_fractional='udd'
    )
    assert isinstance(result_wl, ActuarialResult)
    assert result_wl.value >= -1e-9 # Variansi bisa sedikit negatif karena floating point
    
    ex_circ_res = ex_complete_table(age, INTEREST_RATE_API_TABLE, gender, simple_mortality_table_obj, assumption_fractional='udd')
    e_sq_circ_res = e_sq_complete_table(age, INTEREST_RATE_API_TABLE, gender, simple_mortality_table_obj, assumption_fractional='udd')
    assert result_wl.value == pytest.approx(e_sq_circ_res.value - (ex_circ_res.value**2), abs=1e-7)

    table = simple_mortality_table_obj
    expected_sub_wl = _build_expected_latex_subscript(age, gender, table.has_gender_columns)
    assert result_wl.formula_latex == rf"Var[T_{{{expected_sub_wl}}}]"

# Salin semua fungsi tes yang sudah ada sebelumnya dari nsp_wl_table_default hingga test_table_gender_validation
def test_nsp_wl_table_default():
    result = nsp_wl_table(age=AGE_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE, gender=GENDER_API_TABLE)
    assert isinstance(result, ActuarialResult); assert result.value > 0
    table = load_default_table(); expected_subscript = _build_expected_latex_subscript(AGE_API_TABLE, GENDER_API_TABLE, table.has_gender_columns)
    assert result.formula_latex == rf"A_{{{expected_subscript}}}"
def test_pv_annuity_due_wl_table_default():
    result = pv_annuity_due_wl_table(age=AGE_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE, gender='wanita')
    assert isinstance(result, ActuarialResult); assert result.value > 0
    table = load_default_table(); expected_subscript = _build_expected_latex_subscript(AGE_API_TABLE, 'wanita', table.has_gender_columns)
    assert result.formula_latex == rf"\ddot{{a}}_{{{expected_subscript}}}"
def test_survival_prob_table_default():
    result = survival_prob_table(age=AGE_API_TABLE, n_years=N_YEARS_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE, gender=GENDER_API_TABLE)
    assert isinstance(result, ActuarialResult); assert 0 <= result.value <= 1.0
    table = load_default_table(); expected_subscript = _build_expected_latex_subscript(AGE_API_TABLE, GENDER_API_TABLE, table.has_gender_columns)
    assert result.formula_latex == rf"{{}}_{{{N_YEARS_API_TABLE}}}p_{{{expected_subscript}}}"
def test_death_prob_table_default():
    result = death_prob_table(age=AGE_API_TABLE, n_years=N_YEARS_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE, gender=GENDER_API_TABLE)
    assert isinstance(result, ActuarialResult); assert 0 <= result.value <= 1.0
    corresponding_px_result = survival_prob_table(age=AGE_API_TABLE, n_years=N_YEARS_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE, gender=GENDER_API_TABLE)
    assert result.value == pytest.approx(1.0 - corresponding_px_result.value)
    table = load_default_table(); expected_subscript = _build_expected_latex_subscript(AGE_API_TABLE, GENDER_API_TABLE, table.has_gender_columns)
    assert result.formula_latex == rf"{{}}_{{{N_YEARS_API_TABLE}}}q_{{{expected_subscript}}}"
def test_fom_table_default_cfm():
    result = fom_table(age=AGE_API_TABLE, t_offset=T_OFFSET_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE, gender=GENDER_API_TABLE, assumption_fractional='cfm')
    assert isinstance(result, ActuarialResult); assert result.value >= 0
    table = load_default_table(); px_val = table.px(AGE_API_TABLE, GENDER_API_TABLE)
    expected_mu_cfm = -math.log(px_val) if px_val > 0 else float('inf')
    assert result.value == pytest.approx(expected_mu_cfm)
    age_display_raw = AGE_API_TABLE + T_OFFSET_API_TABLE
    age_display_in_test = f"{age_display_raw:.2f}".rstrip('0').rstrip('.') if T_OFFSET_API_TABLE > 0 else str(AGE_API_TABLE)
    expected_subscript = _build_expected_latex_subscript(age_display_in_test, GENDER_API_TABLE, table.has_gender_columns)
    assert result.formula_latex == rf"\mu_{{{expected_subscript}}}"
def test_fom_table_default_udd():
    result = fom_table(age=AGE_API_TABLE, t_offset=T_OFFSET_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE, gender=GENDER_API_TABLE, assumption_fractional='udd')
    assert isinstance(result, ActuarialResult); assert result.value >= 0
    table = load_default_table(); qx_val = table.qx(AGE_API_TABLE, GENDER_API_TABLE)
    denominator_udd = (1.0 - T_OFFSET_API_TABLE * qx_val)
    expected_mu_udd = qx_val / denominator_udd if denominator_udd > 1e-12 else float('inf')
    assert result.value == pytest.approx(expected_mu_udd)
    age_display_raw = AGE_API_TABLE + T_OFFSET_API_TABLE
    age_display_in_test = f"{age_display_raw:.2f}".rstrip('0').rstrip('.') if T_OFFSET_API_TABLE > 0 else str(AGE_API_TABLE)
    expected_subscript = _build_expected_latex_subscript(age_display_in_test, GENDER_API_TABLE, table.has_gender_columns)
    assert result.formula_latex == rf"\mu_{{{expected_subscript}}}"
def test_pdf_death_table_default_cfm():
    result = pdf_death_table(age=AGE_API_TABLE, t_period=T_OFFSET_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE, gender=GENDER_API_TABLE, assumption_fractional='cfm')
    assert isinstance(result, ActuarialResult); assert result.value >= 0
    table = load_default_table(); px_base = table.px(AGE_API_TABLE, GENDER_API_TABLE) 
    tpx_val = px_base ** T_OFFSET_API_TABLE if px_base > 0 else (1.0 if T_OFFSET_API_TABLE == 0 else 0.0)
    mu_val_res = fom_table(AGE_API_TABLE, T_OFFSET_API_TABLE, INTEREST_RATE_API_TABLE, GENDER_API_TABLE, assumption_fractional='cfm')
    mu_val = mu_val_res.value; assert result.value == pytest.approx(tpx_val * mu_val)
    period_str_for_tpx_expected = f"{T_OFFSET_API_TABLE:.2f}".rstrip('0').rstrip('.'); 
    if T_OFFSET_API_TABLE == int(T_OFFSET_API_TABLE): period_str_for_tpx_expected = str(int(T_OFFSET_API_TABLE))
    subscript_tpx_expected = _build_expected_latex_subscript(AGE_API_TABLE, GENDER_API_TABLE, table.has_gender_columns)
    expected_tpx_part = rf"{{}}_{{{period_str_for_tpx_expected}}}p_{{{subscript_tpx_expected}}}"
    expected_mu_part = mu_val_res.formula_latex
    expected_full_formula = rf"{expected_tpx_part} \cdot {expected_mu_part}"
    assert result.formula_latex == expected_full_formula
def test_table_gender_validation():
    expected_error_message = r"Parameter 'gender' \('pria' atau 'wanita'\) wajib untuk tabel berbasis gender ini\."
    with pytest.raises(ValueError, match=expected_error_message):
        nsp_wl_table(age=35, interest_rate=0.05, gender="tidakvalid") # type: ignore