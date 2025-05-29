# tests/test_api_tables.py
import pytest
from mortapy import (
    nsp_wl_table, pv_annuity_due_wl_table, survival_prob_table,
    death_prob_table, deferred_death_prob_table, fom_table, pdf_death_table,
    ex_curtate_table, e_sq_curtate_table, var_k_table,
    ex_complete_table, e_sq_complete_table, var_t_table,
    load_default_table, MortalityTable
)
from mortapy.core_calculator import ActuarialCalculator # <<< DIPASTIKAN IMPOR ADA
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

AGE_API_TABLE = 35; INTEREST_RATE_API_TABLE = 0.05; GENDER_API_TABLE: Literal["pria", "wanita"] = 'pria'
N_YEARS_API_TABLE = 5; DEFER_T_API_TABLE = 2; DEATH_U_API_TABLE = 3
T_OFFSET_API_TABLE = 0.5; N_TEMP_MOMENT_TABLE = 3

@pytest.fixture
def simple_mortality_table_for_api_path(tmp_path) -> str: # Nama fixture diubah agar unik
    content = ("x,qx_pria,qx_wanita\n"
               "95,0.2,0.15\n96,0.3,0.25\n97,0.5,0.4\n98,0.8,0.7\n99,1.0,1.0\n")
    file_path = tmp_path / "simple_table_api_test.csv"; file_path.write_text(content)
    return str(file_path)

@pytest.fixture
def simple_mortality_table_api_obj(simple_mortality_table_for_api_path: str) -> MortalityTable:
    return MortalityTable(ultimate_file_path=simple_mortality_table_for_api_path)


def _build_expected_latex_subscript(base_val: Any, gender_val: Optional[str] = None, is_gender_table: bool = False, n_temp: Optional[int] = None) -> str:
    subscript = str(base_val)
    if n_temp is not None: subscript += rf":\overline{{{n_temp}}}|"
    if is_gender_table and gender_val: subscript += rf"; \text{{{gender_val.lower()}}}"
    return subscript

# --- Tes Fungsi Aktuaria Dasar (Tabel) ---
def test_nsp_wl_table_default():
    result = nsp_wl_table(age=AGE_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE, gender=GENDER_API_TABLE)
    assert isinstance(result, ActuarialResult); assert result.value > 0
    table = load_default_table(); expected_subscript = _build_expected_latex_subscript(AGE_API_TABLE, GENDER_API_TABLE, table.has_gender_columns_ultimate)
    assert result.formula_latex == rf"A_{{{expected_subscript}}}"

def test_pv_annuity_due_wl_table_default():
    result = pv_annuity_due_wl_table(age=AGE_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE, gender='wanita')
    assert isinstance(result, ActuarialResult); assert result.value > 0
    table = load_default_table(); expected_subscript = _build_expected_latex_subscript(AGE_API_TABLE, 'wanita', table.has_gender_columns_ultimate)
    assert result.formula_latex == rf"\ddot{{a}}_{{{expected_subscript}}}"

def test_survival_prob_table_default():
    result = survival_prob_table(age=AGE_API_TABLE, n_years=N_YEARS_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE, gender=GENDER_API_TABLE)
    assert isinstance(result, ActuarialResult); assert 0 <= result.value <= 1.0
    table = load_default_table(); expected_subscript = _build_expected_latex_subscript(AGE_API_TABLE, GENDER_API_TABLE, table.has_gender_columns_ultimate)
    assert result.formula_latex == rf"{{}}_{{{N_YEARS_API_TABLE}}}p_{{{expected_subscript}}}"

def test_death_prob_table_default():
    result = death_prob_table(age=AGE_API_TABLE, n_years=N_YEARS_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE, gender=GENDER_API_TABLE)
    assert isinstance(result, ActuarialResult); assert 0 <= result.value <= 1.0
    corresponding_px_result = survival_prob_table(age=AGE_API_TABLE, n_years=N_YEARS_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE, gender=GENDER_API_TABLE)
    assert result.value == pytest.approx(1.0 - corresponding_px_result.value)
    table = load_default_table(); expected_subscript = _build_expected_latex_subscript(AGE_API_TABLE, GENDER_API_TABLE, table.has_gender_columns_ultimate)
    assert result.formula_latex == rf"{{}}_{{{N_YEARS_API_TABLE}}}q_{{{expected_subscript}}}"

def test_deferred_death_prob_table_default():
    result = deferred_death_prob_table(age=AGE_API_TABLE, deferral_period=DEFER_T_API_TABLE, n_years_death=DEATH_U_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE, gender=GENDER_API_TABLE)
    assert isinstance(result, ActuarialResult); assert 0 <= result.value <= 1.0
    # Verifikasi dengan formula perkalian menggunakan fungsi API
    t_px_res_api = survival_prob_table(AGE_API_TABLE, DEFER_T_API_TABLE, INTEREST_RATE_API_TABLE, GENDER_API_TABLE)
    u_q_xt_res_api = death_prob_table(AGE_API_TABLE + DEFER_T_API_TABLE, DEATH_U_API_TABLE, INTEREST_RATE_API_TABLE, GENDER_API_TABLE)
    assert result.value == pytest.approx(t_px_res_api.value * u_q_xt_res_api.value, abs=1e-7)
    table = load_default_table(); expected_subscript = _build_expected_latex_subscript(AGE_API_TABLE, GENDER_API_TABLE, table.has_gender_columns_ultimate)
    assert result.formula_latex == rf"{{}}_{{{DEFER_T_API_TABLE}|{DEATH_U_API_TABLE}}}q_{{{expected_subscript}}}"

def test_fom_table_default_cfm():
    result = fom_table(age=AGE_API_TABLE, t_offset=T_OFFSET_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE, gender=GENDER_API_TABLE, assumption_fractional='cfm')
    assert isinstance(result, ActuarialResult); assert result.value >= 0
    table = load_default_table(); px_val = table.get_px(AGE_API_TABLE, GENDER_API_TABLE) # Menggunakan get_px
    expected_mu_cfm = -math.log(px_val) if px_val > 0 else float('inf')
    assert result.value == pytest.approx(expected_mu_cfm)
    age_display_raw = AGE_API_TABLE + T_OFFSET_API_TABLE
    age_display_in_test = f"{age_display_raw:.2f}".rstrip('0').rstrip('.') if T_OFFSET_API_TABLE > 0 else str(AGE_API_TABLE)
    expected_subscript = _build_expected_latex_subscript(age_display_in_test, GENDER_API_TABLE, table.has_gender_columns_ultimate)
    assert result.formula_latex == rf"\mu_{{{expected_subscript}}}"

def test_fom_table_default_udd():
    result = fom_table(age=AGE_API_TABLE, t_offset=T_OFFSET_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE, gender=GENDER_API_TABLE, assumption_fractional='udd')
    assert isinstance(result, ActuarialResult); assert result.value >= 0
    table = load_default_table(); qx_val = table.get_qx(AGE_API_TABLE, GENDER_API_TABLE) # Menggunakan get_qx
    denominator_udd = (1.0 - T_OFFSET_API_TABLE * qx_val)
    expected_mu_udd = qx_val / denominator_udd if denominator_udd > 1e-12 else float('inf')
    assert result.value == pytest.approx(expected_mu_udd)
    age_display_raw = AGE_API_TABLE + T_OFFSET_API_TABLE
    age_display_in_test = f"{age_display_raw:.2f}".rstrip('0').rstrip('.') if T_OFFSET_API_TABLE > 0 else str(AGE_API_TABLE)
    expected_subscript = _build_expected_latex_subscript(age_display_in_test, GENDER_API_TABLE, table.has_gender_columns_ultimate)
    assert result.formula_latex == rf"\mu_{{{expected_subscript}}}"

def test_pdf_death_table_default_cfm():
    result = pdf_death_table(age=AGE_API_TABLE, t_period=T_OFFSET_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE, gender=GENDER_API_TABLE, assumption_fractional='cfm')
    assert isinstance(result, ActuarialResult); assert result.value >= 0
    table = load_default_table(); px_base = table.get_px(AGE_API_TABLE, GENDER_API_TABLE) 
    tpx_val = px_base ** T_OFFSET_API_TABLE if px_base > 0 else (1.0 if T_OFFSET_API_TABLE == 0 else 0.0)
    mu_val_res = fom_table(AGE_API_TABLE, T_OFFSET_API_TABLE, INTEREST_RATE_API_TABLE, GENDER_API_TABLE, assumption_fractional='cfm')
    mu_val = mu_val_res.value; assert result.value == pytest.approx(tpx_val * mu_val)
    period_str_for_tpx_expected = f"{T_OFFSET_API_TABLE:.2f}".rstrip('0').rstrip('.'); 
    if T_OFFSET_API_TABLE == int(T_OFFSET_API_TABLE): period_str_for_tpx_expected = str(int(T_OFFSET_API_TABLE))
    subscript_tpx_expected = _build_expected_latex_subscript(AGE_API_TABLE, GENDER_API_TABLE, table.has_gender_columns_ultimate)
    expected_tpx_part = rf"{{}}_{{{period_str_for_tpx_expected}}}p_{{{subscript_tpx_expected}}}"
    expected_mu_part = mu_val_res.formula_latex
    expected_full_formula = rf"{expected_tpx_part} \cdot {expected_mu_part}"
    assert result.formula_latex == expected_full_formula

def test_table_gender_validation():
    expected_error_message = r"Parameter 'gender' \('pria' atau 'wanita'\) wajib untuk tabel berbasis gender ini\."
    with pytest.raises(ValueError, match=expected_error_message):
        nsp_wl_table(age=35, interest_rate=0.05, gender="tidakvalid") # type: ignore

# --- Tes Momen Curtate dari Tabel ---
def test_ex_curtate_table_default(simple_mortality_table_api_obj : MortalityTable): # Menggunakan tabel dummy
    table = simple_mortality_table_api_obj
    age, gender, n_temp = 97, 'pria', 1
    # e_{97:1|} (pria) = p_97 = 1 - q_97 = 1 - 0.5 = 0.5
    result_temp = ex_curtate_table(age=age, interest_rate=INTEREST_RATE_API_TABLE, gender=gender, mortality_table=table, n_temp=n_temp)
    assert isinstance(result_temp, ActuarialResult); assert result_temp.value == pytest.approx(0.5)
    expected_sub_temp = _build_expected_latex_subscript(age, gender, table.has_gender_columns_ultimate, n_temp=n_temp)
    assert result_temp.formula_latex == rf"e_{{{expected_sub_temp}}}"

def test_e_sq_curtate_table_default(simple_mortality_table_api_obj : MortalityTable):
    table = simple_mortality_table_api_obj
    age, gender, n_temp = 97, 'pria', 1
    # E[(K_{97:1|})^2] = (2*0+1)*_1p_97 = p_97 = 0.5
    result_temp = e_sq_curtate_table(age=age, interest_rate=INTEREST_RATE_API_TABLE, gender=gender, mortality_table=table, n_temp=n_temp)
    assert isinstance(result_temp, ActuarialResult); assert result_temp.value == pytest.approx(0.5)
    expected_sub_temp = _build_expected_latex_subscript(age, gender, table.has_gender_columns_ultimate, n_temp=n_temp)
    assert result_temp.formula_latex == rf"E[K_{{{expected_sub_temp}}}^2]"

def test_var_k_table_default(simple_mortality_table_api_obj : MortalityTable):
    table = simple_mortality_table_api_obj
    age, gender = 97, 'pria'
    result_wl = var_k_table(age=age, interest_rate=INTEREST_RATE_API_TABLE, gender=gender, mortality_table=table)
    assert isinstance(result_wl, ActuarialResult); assert result_wl.value >= -1e-9
    expected_sub_wl = _build_expected_latex_subscript(age, gender, table.has_gender_columns_ultimate)
    assert result_wl.formula_latex == rf"Var[K_{{{expected_sub_wl}}}]"
    ex_res = ex_curtate_table(age, INTEREST_RATE_API_TABLE, gender, table)
    e_sq_res = e_sq_curtate_table(age, INTEREST_RATE_API_TABLE, gender, table)
    assert result_wl.value == pytest.approx(e_sq_res.value - (ex_res.value**2), abs=1e-7)

# --- Tes Momen Complete dari Tabel ---
def test_ex_complete_table_default(simple_mortality_table_api_obj: MortalityTable):
    table = simple_mortality_table_api_obj
    age, gender, n_temp = 97, 'pria', 1
    result_temp = ex_complete_table(age=age, interest_rate=INTEREST_RATE_API_TABLE, gender=gender, mortality_table=table, n_temp=n_temp, assumption_fractional='udd')
    assert isinstance(result_temp, ActuarialResult); assert result_temp.value >= 0
    expected_sub_temp = _build_expected_latex_subscript(age, gender, table.has_gender_columns_ultimate, n_temp=n_temp)
    assert result_temp.formula_latex == rf"\mathring{{e}}_{{{expected_sub_temp}}}"
    # e_circ_{97:1|} (UDD) = _0p_97 * (1 - 0.5*q_97) = 1 * (1 - 0.5 * 0.5) = 0.75
    assert result_temp.value == pytest.approx(0.75)

def test_e_sq_complete_table_default(simple_mortality_table_api_obj: MortalityTable):
    table = simple_mortality_table_api_obj
    age, gender, n_temp = 97, 'pria', 1
    result_temp = e_sq_complete_table(age=age, interest_rate=INTEREST_RATE_API_TABLE, gender=gender, mortality_table=table, n_temp=n_temp, assumption_fractional='udd')
    assert isinstance(result_temp, ActuarialResult); assert result_temp.value >= 0
    expected_sub_temp = _build_expected_latex_subscript(age, gender, table.has_gender_columns_ultimate, n_temp=n_temp)
    assert result_temp.formula_latex == rf"E[T_{{{expected_sub_temp}}}^2]"
    # E[T_{97:1|}^2] (UDD) approx E[K_{97:1|}^2] + e_{97:1|} + (1/3)*(1 - _1p_97)
    # E[K_{97:1|}^2] = 0.5 ; e_{97:1|} = 0.5 ; _1p_97 = 0.5
    # approx 0.5 + 0.5 + (1/3)*(1-0.5) = 1 + (1/3)*0.5 = 1 + 1/6 = 1.1666...
    ex_curt_temp_res = ex_curtate_table(age,INTEREST_RATE_API_TABLE,gender,table,n_temp)
    e_sq_curt_temp_res = e_sq_curtate_table(age,INTEREST_RATE_API_TABLE,gender,table,n_temp)
    _1p_97_val = survival_prob_table(age, n_temp, INTEREST_RATE_API_TABLE, gender, table).value
    expected_approx = e_sq_curt_temp_res.value + ex_curt_temp_res.value + (1.0/3.0)*(1.0 - _1p_97_val)
    assert result_temp.value == pytest.approx(expected_approx, abs=1e-1)


def test_var_t_table_default(simple_mortality_table_api_obj: MortalityTable):
    table = simple_mortality_table_api_obj
    age, gender, n_temp = 97, 'pria', 1
    result = var_t_table(age=age, interest_rate=INTEREST_RATE_API_TABLE, gender=gender, mortality_table=table, n_temp=n_temp, assumption_fractional='udd')
    assert isinstance(result, ActuarialResult); assert result.value >= -1e-9
    ex_circ_res = ex_complete_table(age,INTEREST_RATE_API_TABLE,gender,table,n_temp,'udd')
    e_sq_circ_res = e_sq_complete_table(age,INTEREST_RATE_API_TABLE,gender,table,n_temp,'udd')
    assert result.value == pytest.approx(e_sq_circ_res.value - (ex_circ_res.value**2), abs=1e-7)
    expected_sub = _build_expected_latex_subscript(age, gender, table.has_gender_columns_ultimate, n_temp=n_temp)
    assert result.formula_latex == rf"Var[T_{{{expected_sub}}}]"