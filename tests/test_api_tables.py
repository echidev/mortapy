# tests/test_api_tables.py
import pytest
from mortapy import (
    nsp_wl_table,
    pv_annuity_due_wl_table,
    survival_prob_table, # Kita akan gunakan ini
    death_prob_table,    # Dan ini
    deferred_death_prob_table,
    fom_table,
    pdf_death_table,
    load_default_table,
    MortalityTable,
    ex_curtate_table, 
    e_sq_curtate_table, 
    var_k_table
)
from mortapy.core_calculator import ActuarialCalculator 
from mortapy.result import ActuarialResult
import os
import math
from typing import Literal, Optional, Any

# (Logika path TEST_TABLE_PATH_DEFAULT_API tetap sama)
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

def _build_expected_latex_subscript(base_val: Any, gender_val: Optional[str] = None, is_gender_table: bool = False, n_temp: Optional[int] = None) -> str:
    subscript = str(base_val)
    if n_temp is not None:
        subscript += rf":\overline{{{n_temp}}}|"
    if is_gender_table and gender_val:
        subscript += rf"; \text{{{gender_val.lower()}}}"
    return subscript

# ... (fungsi tes lain dari nsp_wl_table_default hingga death_prob_table_default tetap sama) ...
def test_nsp_wl_table_default():
    result = nsp_wl_table(age=AGE_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE, gender=GENDER_API_TABLE)
    assert isinstance(result, ActuarialResult)
    assert result.value > 0
    table = load_default_table()
    expected_subscript = _build_expected_latex_subscript(AGE_API_TABLE, GENDER_API_TABLE, table.has_gender_columns)
    assert result.formula_latex == rf"A_{{{expected_subscript}}}"

def test_pv_annuity_due_wl_table_default():
    result = pv_annuity_due_wl_table(age=AGE_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE, gender='wanita')
    assert isinstance(result, ActuarialResult)
    assert result.value > 0
    table = load_default_table()
    expected_subscript = _build_expected_latex_subscript(AGE_API_TABLE, 'wanita', table.has_gender_columns)
    assert result.formula_latex == rf"\ddot{{a}}_{{{expected_subscript}}}"

def test_survival_prob_table_default():
    result = survival_prob_table(age=AGE_API_TABLE, n_years=N_YEARS_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE, gender=GENDER_API_TABLE)
    assert isinstance(result, ActuarialResult)
    assert 0 <= result.value <= 1.0
    table = load_default_table()
    expected_subscript = _build_expected_latex_subscript(AGE_API_TABLE, GENDER_API_TABLE, table.has_gender_columns)
    assert result.formula_latex == rf"{{}}_{{{N_YEARS_API_TABLE}}}p_{{{expected_subscript}}}"

def test_death_prob_table_default():
    result = death_prob_table(age=AGE_API_TABLE, n_years=N_YEARS_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE, gender=GENDER_API_TABLE)
    assert isinstance(result, ActuarialResult)
    assert 0 <= result.value <= 1.0
    corresponding_px_result = survival_prob_table(age=AGE_API_TABLE, n_years=N_YEARS_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE, gender=GENDER_API_TABLE)
    assert result.value == pytest.approx(1.0 - corresponding_px_result.value)
    table = load_default_table()
    expected_subscript = _build_expected_latex_subscript(AGE_API_TABLE, GENDER_API_TABLE, table.has_gender_columns)
    assert result.formula_latex == rf"{{}}_{{{N_YEARS_API_TABLE}}}q_{{{expected_subscript}}}"

def test_deferred_death_prob_table_default():
    result = deferred_death_prob_table(
        age=AGE_API_TABLE, deferral_period=DEFER_T_API_TABLE, n_years_death=DEATH_U_API_TABLE,
        interest_rate=INTEREST_RATE_API_TABLE, gender=GENDER_API_TABLE
    )
    assert isinstance(result, ActuarialResult)
    assert 0 <= result.value <= 1.0
    
    # Verifikasi dengan formula perkalian menggunakan fungsi API yang sudah ada
    t_px_res = survival_prob_table(
        AGE_API_TABLE, DEFER_T_API_TABLE, INTEREST_RATE_API_TABLE, GENDER_API_TABLE
    )
    u_q_xt_res = death_prob_table(
        AGE_API_TABLE + DEFER_T_API_TABLE, DEATH_U_API_TABLE, INTEREST_RATE_API_TABLE, GENDER_API_TABLE
    )
    
    assert result.value == pytest.approx(t_px_res.value * u_q_xt_res.value, abs=1e-7)

    table = load_default_table() # Untuk is_gender_table di _build_expected_latex_subscript
    expected_subscript = _build_expected_latex_subscript(AGE_API_TABLE, GENDER_API_TABLE, table.has_gender_columns)
    assert result.formula_latex == rf"{{}}_{{{DEFER_T_API_TABLE}|{DEATH_U_API_TABLE}}}q_{{{expected_subscript}}}"


# ... (Fungsi tes lainnya dari fom_table_default_cfm hingga test_var_k_table_default tetap sama seperti versi terakhir yang berhasil)
def test_fom_table_default_cfm():
    result = fom_table(
        age=AGE_API_TABLE, t_offset=T_OFFSET_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE,
        gender=GENDER_API_TABLE, assumption_fractional='cfm'
    )
    assert isinstance(result, ActuarialResult)
    assert result.value >= 0
    table = load_default_table()
    px_val = table.px(AGE_API_TABLE, GENDER_API_TABLE)
    expected_mu_cfm = -math.log(px_val) if px_val > 0 else float('inf')
    assert result.value == pytest.approx(expected_mu_cfm)
    
    age_display_raw = AGE_API_TABLE + T_OFFSET_API_TABLE
    age_display_in_test = f"{age_display_raw:.2f}".rstrip('0').rstrip('.') if T_OFFSET_API_TABLE > 0 else str(AGE_API_TABLE)
    expected_subscript = _build_expected_latex_subscript(age_display_in_test, GENDER_API_TABLE, table.has_gender_columns)
    assert result.formula_latex == rf"\mu_{{{expected_subscript}}}"

def test_fom_table_default_udd():
    result = fom_table(
        age=AGE_API_TABLE, t_offset=T_OFFSET_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE,
        gender=GENDER_API_TABLE, assumption_fractional='udd'
    )
    assert isinstance(result, ActuarialResult)
    assert result.value >= 0
    table = load_default_table()
    qx_val = table.qx(AGE_API_TABLE, GENDER_API_TABLE)
    denominator_udd = (1.0 - T_OFFSET_API_TABLE * qx_val)
    expected_mu_udd = qx_val / denominator_udd if denominator_udd > 1e-12 else float('inf')
    assert result.value == pytest.approx(expected_mu_udd)
    age_display_raw = AGE_API_TABLE + T_OFFSET_API_TABLE
    age_display_in_test = f"{age_display_raw:.2f}".rstrip('0').rstrip('.') if T_OFFSET_API_TABLE > 0 else str(AGE_API_TABLE)
    expected_subscript = _build_expected_latex_subscript(age_display_in_test, GENDER_API_TABLE, table.has_gender_columns)
    assert result.formula_latex == rf"\mu_{{{expected_subscript}}}"

def test_pdf_death_table_default_cfm():
    result = pdf_death_table(
        age=AGE_API_TABLE, t_period=T_OFFSET_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE,
        gender=GENDER_API_TABLE, assumption_fractional='cfm'
    )
    assert isinstance(result, ActuarialResult)
    assert result.value >= 0
    table = load_default_table()
    px_base = table.px(AGE_API_TABLE, GENDER_API_TABLE) 
    tpx_val = 0.0
    if px_base > 0 : tpx_val = px_base ** T_OFFSET_API_TABLE 
    elif T_OFFSET_API_TABLE == 0: tpx_val = 1.0
    mu_val_res = fom_table(AGE_API_TABLE, T_OFFSET_API_TABLE, INTEREST_RATE_API_TABLE, GENDER_API_TABLE, assumption_fractional='cfm')
    mu_val = mu_val_res.value
    assert result.value == pytest.approx(tpx_val * mu_val)
    period_str_for_tpx_expected = f"{T_OFFSET_API_TABLE:.2f}".rstrip('0').rstrip('.')
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

def test_ex_curtate_table_default():
    result_wl = ex_curtate_table(age=AGE_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE, gender=GENDER_API_TABLE)
    assert isinstance(result_wl, ActuarialResult)
    assert result_wl.value >= 0
    table = load_default_table()
    expected_sub_wl = _build_expected_latex_subscript(AGE_API_TABLE, GENDER_API_TABLE, table.has_gender_columns)
    assert result_wl.formula_latex == rf"e_{{{expected_sub_wl}}}"
    result_temp = ex_curtate_table(age=AGE_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE, gender=GENDER_API_TABLE, n_temp=N_TEMP_MOMENT_TABLE)
    assert isinstance(result_temp, ActuarialResult)
    assert result_temp.value >= 0
    expected_sub_temp = _build_expected_latex_subscript(AGE_API_TABLE, GENDER_API_TABLE, table.has_gender_columns, n_temp=N_TEMP_MOMENT_TABLE)
    assert result_temp.formula_latex == rf"e_{{{expected_sub_temp}}}"
    if result_wl.value > 0 : 
        assert result_temp.value <= result_wl.value

def test_e_sq_curtate_table_default():
    result_wl = e_sq_curtate_table(age=AGE_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE, gender=GENDER_API_TABLE)
    assert isinstance(result_wl, ActuarialResult)
    assert result_wl.value >= 0
    table = load_default_table()
    expected_sub_wl = _build_expected_latex_subscript(AGE_API_TABLE, GENDER_API_TABLE, table.has_gender_columns)
    assert result_wl.formula_latex == rf"E[K_{{{expected_sub_wl}}}^2]"
    result_temp = e_sq_curtate_table(age=AGE_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE, gender=GENDER_API_TABLE, n_temp=N_TEMP_MOMENT_TABLE)
    assert isinstance(result_temp, ActuarialResult)
    assert result_temp.value >= 0
    expected_sub_temp = _build_expected_latex_subscript(AGE_API_TABLE, GENDER_API_TABLE, table.has_gender_columns, n_temp=N_TEMP_MOMENT_TABLE)
    assert result_temp.formula_latex == rf"E[K_{{{expected_sub_temp}}}^2]"
    if result_wl.value > 0:
         assert result_temp.value <= result_wl.value

def test_var_k_table_default():
    result_wl = var_k_table(age=AGE_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE, gender=GENDER_API_TABLE)
    assert isinstance(result_wl, ActuarialResult)
    assert result_wl.value >= 0 
    table = load_default_table()
    expected_sub_wl = _build_expected_latex_subscript(AGE_API_TABLE, GENDER_API_TABLE, table.has_gender_columns)
    assert result_wl.formula_latex == rf"Var[K_{{{expected_sub_wl}}}]"
    ex_res = ex_curtate_table(AGE_API_TABLE, INTEREST_RATE_API_TABLE, GENDER_API_TABLE)
    e_sq_res = e_sq_curtate_table(AGE_API_TABLE, INTEREST_RATE_API_TABLE, GENDER_API_TABLE)
    assert result_wl.value == pytest.approx(e_sq_res.value - (ex_res.value**2), abs=1e-7)