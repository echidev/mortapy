# tests/test_api_tables.py
import pytest
from mortapy import (
    nsp_wl_table,
    pv_annuity_due_wl_table,
    survival_prob_table,
    death_prob_table,
    deferred_death_prob_table,
    fom_table,
    pdf_death_table,
    load_default_table,
    MortalityTable
)
from mortapy.result import ActuarialResult
import os
import math
from typing import Literal, Optional, Any # <<< PASTIKAN BARIS INI LENGKAP

# (Logika path TEST_TABLE_PATH_DEFAULT_API tetap sama)
try:
    # Mencoba path relatif dari root proyek jika CWD adalah root proyek
    path_candidate_project_root = os.path.join(os.getcwd(), "mortapy", "tables", "tabel_mortalita_penduduk_indonesia_2023.csv")
    # Mencoba path relatif dari folder tests
    path_candidate_from_tests = os.path.join(os.path.dirname(__file__), '..', 'mortapy', 'tables', 'tabel_mortalita_penduduk_indonesia_2023.csv')
    # Mencoba path relatif jika CWD adalah folder paket mortapy/mortapy
    path_candidate_package_root = os.path.join(os.getcwd(), "tables", "tabel_mortalita_penduduk_indonesia_2023.csv")


    if "GITHUB_WORKSPACE" in os.environ: 
        TEST_TABLE_PATH_DEFAULT_API = os.path.join(os.environ["GITHUB_WORKSPACE"], "mortapy", "tables", "tabel_mortalita_penduduk_indonesia_2023.csv")
    elif os.path.exists(path_candidate_project_root) and "mortapy" == os.path.basename(os.getcwd()): 
         TEST_TABLE_PATH_DEFAULT_API = path_candidate_project_root
    elif os.path.exists(path_candidate_from_tests):
        TEST_TABLE_PATH_DEFAULT_API = path_candidate_from_tests
    elif os.path.exists(path_candidate_package_root) and "mortapy" == os.path.basename(os.path.dirname(os.getcwd())): 
        TEST_TABLE_PATH_DEFAULT_API = path_candidate_package_root
    else:
        TEST_TABLE_PATH_DEFAULT_API = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mortapy', 'tables', 'tabel_mortalita_penduduk_indonesia_2023.csv')
        if not os.path.exists(TEST_TABLE_PATH_DEFAULT_API) :
             TEST_TABLE_PATH_DEFAULT_API = "mortapy/tables/tabel_mortalita_penduduk_indonesia_2023.csv"
except Exception: 
    TEST_TABLE_PATH_DEFAULT_API = "mortapy/tables/tabel_mortalita_penduduk_indonesia_2023.csv"


# --- Parameter umum untuk tes API tabel ---
AGE_API_TABLE = 35
INTEREST_RATE_API_TABLE = 0.05
GENDER_API_TABLE: Literal["pria", "wanita"] = 'pria'
N_YEARS_API_TABLE = 5
DEFER_T_API_TABLE = 2
DEATH_U_API_TABLE = 3
T_OFFSET_API_TABLE = 0.5

def _build_expected_latex_subscript(base_val: Any, gender_val: Optional[str] = None, is_gender_table: bool = False) -> str:
    """Helper di tes untuk membuat subscript LaTeX yang diharapkan, konsisten dengan API."""
    subscript = str(base_val)
    if is_gender_table and gender_val:
        subscript += rf"; \text{{{gender_val.lower()}}}" # Dengan spasi
    return subscript

def test_nsp_wl_table_default():
    """Tes NSP Whole Life dengan tabel default."""
    result = nsp_wl_table(age=AGE_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE, gender=GENDER_API_TABLE)
    assert isinstance(result, ActuarialResult)
    assert result.value > 0
    table = load_default_table()
    expected_subscript = _build_expected_latex_subscript(AGE_API_TABLE, GENDER_API_TABLE, table.has_gender_columns)
    assert result.formula_latex == rf"A_{{{expected_subscript}}}"

def test_pv_annuity_due_wl_table_default():
    """Tes PV Anuitas Whole Life Due dengan tabel default."""
    result = pv_annuity_due_wl_table(age=AGE_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE, gender='wanita')
    assert isinstance(result, ActuarialResult)
    assert result.value > 0
    table = load_default_table()
    expected_subscript = _build_expected_latex_subscript(AGE_API_TABLE, 'wanita', table.has_gender_columns)
    assert result.formula_latex == rf"\ddot{{a}}_{{{expected_subscript}}}"

def test_survival_prob_table_default():
    """Tes Probabilitas Hidup dengan tabel default."""
    result = survival_prob_table(age=AGE_API_TABLE, n_years=N_YEARS_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE, gender=GENDER_API_TABLE)
    assert isinstance(result, ActuarialResult)
    assert 0 <= result.value <= 1.0
    table = load_default_table()
    expected_subscript = _build_expected_latex_subscript(AGE_API_TABLE, GENDER_API_TABLE, table.has_gender_columns)
    assert result.formula_latex == rf"{{}}_{{{N_YEARS_API_TABLE}}}p_{{{expected_subscript}}}"

def test_death_prob_table_default():
    """Tes Probabilitas Kematian dengan tabel default."""
    result = death_prob_table(age=AGE_API_TABLE, n_years=N_YEARS_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE, gender=GENDER_API_TABLE)
    assert isinstance(result, ActuarialResult)
    assert 0 <= result.value <= 1.0
    corresponding_px_result = survival_prob_table(age=AGE_API_TABLE, n_years=N_YEARS_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE, gender=GENDER_API_TABLE)
    assert result.value == pytest.approx(1.0 - corresponding_px_result.value)
    table = load_default_table()
    expected_subscript = _build_expected_latex_subscript(AGE_API_TABLE, GENDER_API_TABLE, table.has_gender_columns)
    assert result.formula_latex == rf"{{}}_{{{N_YEARS_API_TABLE}}}q_{{{expected_subscript}}}"

def test_deferred_death_prob_table_default():
    """Tes Probabilitas Kematian Ditunda dengan tabel default."""
    result = deferred_death_prob_table(
        age=AGE_API_TABLE,
        deferral_period=DEFER_T_API_TABLE,
        n_years_death=DEATH_U_API_TABLE,
        interest_rate=INTEREST_RATE_API_TABLE,
        gender=GENDER_API_TABLE
    )
    assert isinstance(result, ActuarialResult)
    assert 0 <= result.value <= 1.0
    t_px_res = survival_prob_table(AGE_API_TABLE, DEFER_T_API_TABLE, INTEREST_RATE_API_TABLE, GENDER_API_TABLE)
    t_plus_u_px_res = survival_prob_table(AGE_API_TABLE, DEFER_T_API_TABLE + DEATH_U_API_TABLE, INTEREST_RATE_API_TABLE, GENDER_API_TABLE)
    assert result.value == pytest.approx(t_px_res.value - t_plus_u_px_res.value)
    table = load_default_table()
    expected_subscript = _build_expected_latex_subscript(AGE_API_TABLE, GENDER_API_TABLE, table.has_gender_columns)
    assert result.formula_latex == rf"{{}}_{{{DEFER_T_API_TABLE}|{DEATH_U_API_TABLE}}}q_{{{expected_subscript}}}"

def test_fom_table_default_cfm():
    """Tes Force of Mortality (CFM) dengan tabel default."""
    result = fom_table(
        age=AGE_API_TABLE,
        t_offset=T_OFFSET_API_TABLE,
        interest_rate=INTEREST_RATE_API_TABLE,
        gender=GENDER_API_TABLE,
        assumption_fractional='cfm'
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
    """Tes Force of Mortality (UDD) dengan tabel default."""
    result = fom_table(
        age=AGE_API_TABLE,
        t_offset=T_OFFSET_API_TABLE,
        interest_rate=INTEREST_RATE_API_TABLE,
        gender=GENDER_API_TABLE,
        assumption_fractional='udd'
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
    """Tes PDF Kematian dengan tabel default dan asumsi CFM untuk interpolasi."""
    result = pdf_death_table(
        age=AGE_API_TABLE,
        t_period=T_OFFSET_API_TABLE,
        interest_rate=INTEREST_RATE_API_TABLE,
        gender=GENDER_API_TABLE,
        assumption_fractional='cfm'
    )
    assert isinstance(result, ActuarialResult)
    assert result.value >= 0

    table = load_default_table()
    px_base = table.px(AGE_API_TABLE, GENDER_API_TABLE) # p_x tahunan
    tpx_val = 0.0
    if px_base > 0 :
        tpx_val = px_base ** T_OFFSET_API_TABLE # _t_offset p_x dengan CFM
    elif T_OFFSET_API_TABLE == 0:
        tpx_val = 1.0

    mu_val_res = fom_table(AGE_API_TABLE, T_OFFSET_API_TABLE, INTEREST_RATE_API_TABLE, GENDER_API_TABLE, assumption_fractional='cfm')
    mu_val = mu_val_res.value

    assert result.value == pytest.approx(tpx_val * mu_val)

    # Membuat keseluruhan string formula yang diharapkan
    period_str_for_tpx_expected = f"{T_OFFSET_API_TABLE:.2f}".rstrip('0').rstrip('.')
    if T_OFFSET_API_TABLE == int(T_OFFSET_API_TABLE): period_str_for_tpx_expected = str(int(T_OFFSET_API_TABLE))
    
    subscript_tpx_expected = _build_expected_latex_subscript(AGE_API_TABLE, GENDER_API_TABLE, table.has_gender_columns)
    expected_tpx_part = rf"{{}}_{{{period_str_for_tpx_expected}}}p_{{{subscript_tpx_expected}}}"
    
    expected_mu_part = mu_val_res.formula_latex

    expected_full_formula = rf"{expected_tpx_part} \cdot {expected_mu_part}"
    
    assert result.formula_latex == expected_full_formula

def test_table_gender_validation():
    """Tes validasi gender saat menggunakan tabel."""
    expected_error_message = r"Parameter 'gender' \('pria' atau 'wanita'\) wajib untuk tabel berbasis gender ini\."
    with pytest.raises(ValueError, match=expected_error_message):
        nsp_wl_table(age=35, interest_rate=0.05, gender="tidakvalid") # type: ignore