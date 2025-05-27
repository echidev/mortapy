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
from typing import Literal

# Path untuk tabel default
try:
    path_candidate_1 = os.path.join("mortapy", "tables", "tabel_mortalita_penduduk_indonesia_2023.csv")
    path_candidate_2 = os.path.join(os.path.dirname(__file__), '..', 'mortapy', 'tables', 'tabel_mortalita_penduduk_indonesia_2023.csv')
    if os.path.exists(path_candidate_1):
        TEST_TABLE_PATH_DEFAULT_API = path_candidate_1
    elif os.path.exists(path_candidate_2):
        TEST_TABLE_PATH_DEFAULT_API = path_candidate_2
    else:
        TEST_TABLE_PATH_DEFAULT_API = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mortapy', 'tables', 'tabel_mortalita_penduduk_indonesia_2023.csv')
except Exception:
    TEST_TABLE_PATH_DEFAULT_API = "mortapy/tables/tabel_mortalita_penduduk_indonesia_2023.csv"

# --- Parameter umum untuk tes API tabel ---
AGE_API_TABLE = 35
INTEREST_RATE_API_TABLE = 0.05
GENDER_API_TABLE: Literal["pria", "wanita"] = 'pria'
N_YEARS_API_TABLE = 5
DEFER_T_API_TABLE = 2
DEATH_U_API_TABLE = 3
T_OFFSET_API_TABLE = 0.5 # Ini akan menjadi 0.50 dalam format string

def test_nsp_wl_table_default():
    result = nsp_wl_table(age=AGE_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE, gender=GENDER_API_TABLE)
    assert isinstance(result, ActuarialResult)
    assert result.value > 0
    expected_formula_part = rf"A_{{{AGE_API_TABLE}"
    if load_default_table().has_gender_columns :
        expected_formula_part += rf"; \text{{{GENDER_API_TABLE.lower()}}}" # DENGAN SPASI
    expected_formula_part += r"}"
    assert result.formula_latex == expected_formula_part

def test_pv_annuity_due_wl_table_default():
    result = pv_annuity_due_wl_table(age=AGE_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE, gender='wanita')
    assert isinstance(result, ActuarialResult)
    assert result.value > 0
    expected_formula_part = rf"\ddot{{a}}_{{{AGE_API_TABLE}"
    if load_default_table().has_gender_columns:
        expected_formula_part += rf"; \text{{wanita}}" # DENGAN SPASI
    expected_formula_part += r"}"
    assert result.formula_latex == expected_formula_part

def test_survival_prob_table_default():
    result = survival_prob_table(age=AGE_API_TABLE, n_years=N_YEARS_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE, gender=GENDER_API_TABLE)
    assert isinstance(result, ActuarialResult)
    assert 0 <= result.value <= 1.0
    expected_formula_part = rf"{{}}_{{{N_YEARS_API_TABLE}}}p_{{{AGE_API_TABLE}"
    if load_default_table().has_gender_columns:
        expected_formula_part += rf"; \text{{{GENDER_API_TABLE.lower()}}}" # DENGAN SPASI
    expected_formula_part += r"}"
    assert result.formula_latex == expected_formula_part

def test_death_prob_table_default():
    result = death_prob_table(age=AGE_API_TABLE, n_years=N_YEARS_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE, gender=GENDER_API_TABLE)
    assert isinstance(result, ActuarialResult)
    assert 0 <= result.value <= 1.0
    corresponding_px_result = survival_prob_table(age=AGE_API_TABLE, n_years=N_YEARS_API_TABLE, interest_rate=INTEREST_RATE_API_TABLE, gender=GENDER_API_TABLE)
    assert result.value == pytest.approx(1.0 - corresponding_px_result.value)
    expected_formula_part = rf"{{}}_{{{N_YEARS_API_TABLE}}}q_{{{AGE_API_TABLE}"
    if load_default_table().has_gender_columns:
        expected_formula_part += rf"; \text{{{GENDER_API_TABLE.lower()}}}" # DENGAN SPASI
    expected_formula_part += r"}"
    assert result.formula_latex == expected_formula_part

def test_deferred_death_prob_table_default():
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
    expected_formula_part = rf"{{}}_{{{DEFER_T_API_TABLE}|{DEATH_U_API_TABLE}}}q_{{{AGE_API_TABLE}"
    if load_default_table().has_gender_columns:
        expected_formula_part += rf"; \text{{{GENDER_API_TABLE.lower()}}}" # DENGAN SPASI
    expected_formula_part += r"}"
    assert result.formula_latex == expected_formula_part

def test_fom_table_default_cfm():
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
    
    age_display = f"{AGE_API_TABLE}+{T_OFFSET_API_TABLE:.2f}".rstrip('0').rstrip('.')
    expected_formula_part = rf"\mu_{{{age_display}"
    if table.has_gender_columns:
        expected_formula_part += rf"; \text{{{GENDER_API_TABLE.lower()}}}" # DENGAN SPASI
    expected_formula_part += r"}}"
    assert result.formula_latex == expected_formula_part

def test_fom_table_default_udd():
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

    age_display = f"{AGE_API_TABLE}+{T_OFFSET_API_TABLE:.2f}".rstrip('0').rstrip('.')
    expected_formula_part = rf"\mu_{{{age_display}"
    if table.has_gender_columns:
        expected_formula_part += rf"; \text{{{GENDER_API_TABLE.lower()}}}" # DENGAN SPASI
    expected_formula_part += r"}}"
    assert result.formula_latex == expected_formula_part

def test_pdf_death_table_default_cfm():
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
    px_base = table.px(AGE_API_TABLE, GENDER_API_TABLE)
    tpx_val = px_base ** T_OFFSET_API_TABLE

    mu_val_res = fom_table(AGE_API_TABLE, T_OFFSET_API_TABLE, INTEREST_RATE_API_TABLE, GENDER_API_TABLE, assumption_fractional='cfm')
    mu_val = mu_val_res.value

    assert result.value == pytest.approx(tpx_val * mu_val)

    # Membuat keseluruhan string formula yang diharapkan
    period_str_for_tpx_expected = f"{T_OFFSET_API_TABLE:.2f}" # Menghasilkan "0.50"
    age_for_tpx_in_pdf = str(AGE_API_TABLE)
    
    # Untuk bagian mu, kita ambil dari formula fom_table yang sudah diuji
    # Ini adalah formula_latex dari fom_table(AGE_API_TABLE + int(0), T_OFFSET_API_TABLE, ...)
    # karena pdf_death_table memanggil fom_table dengan age=(age + integer_part_t) dan t_offset=fractional_part_t
    # Dalam kasus ini, integer_part_t dari T_OFFSET_API_TABLE (0.5) adalah 0, fractional_part_t adalah 0.5
    # Jadi, fom_table dipanggil dengan age=AGE_API_TABLE, t_offset=T_OFFSET_API_TABLE
    
    age_for_mu_display_in_pdf = f"{AGE_API_TABLE}+{T_OFFSET_API_TABLE:.2f}".rstrip('0').rstrip('.')


    expected_tpx_part = rf"{{}}_{{{period_str_for_tpx_expected}}}p_{{{age_for_tpx_in_pdf}"
    if table.has_gender_columns:
        expected_tpx_part += rf"; \text{{{GENDER_API_TABLE.lower()}}}" # DENGAN SPASI
    expected_tpx_part += r"}"

    expected_mu_part = rf"\mu_{{{age_for_mu_display_in_pdf}"
    if table.has_gender_columns:
        expected_mu_part += rf"; \text{{{GENDER_API_TABLE.lower()}}}" # DENGAN SPASI
    expected_mu_part += r"}}"

    expected_full_formula = rf"{expected_tpx_part} \cdot {expected_mu_part}"
    
    # print(f"\n--- DEBUGGING test_pdf_death_table_default_cfm ---")
    # print(f"Ekspektasi Full Formula : '{expected_full_formula}'")
    # print(f"Representasi Ekspektasi : {repr(expected_full_formula)}")
    # print(f"Hasil Aktual Formula    : '{result.formula_latex}'")
    # print(f"Representasi Hasil Aktual: {repr(result.formula_latex)}")

    assert result.formula_latex == expected_full_formula


def test_table_gender_validation():
    """Tes validasi gender saat menggunakan tabel."""
    expected_error_message = r"Parameter 'gender' \('pria' atau 'wanita'\) wajib untuk tabel berbasis gender ini\."
    with pytest.raises(ValueError, match=expected_error_message):
        nsp_wl_table(age=35, interest_rate=0.05, gender="tidakvalid") # type: ignore