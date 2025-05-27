# tests/test_api_assumptions.py
import pytest
from mortapy import (
    nsp_wl_assumption, 
    pv_annuity_due_wl_assumption, 
    survival_prob_assumption
)
from mortapy.result import ActuarialResult
import math

# Parameter umum untuk tes
AGE = 35
INTEREST_RATE = 0.05
# Untuk asumsi dasar
OMEGA_TEST = 110
MU_TEST = 0.02
QX_CONST_TEST = 0.01
PX_CONST_TEST = 0.98
# Untuk Gompertz
GOMPERTZ_B_TEST = 0.00005 # Parameter B
GOMPERTZ_C_TEST = 1.09    # Parameter c
# Untuk Makeham
MAKEHAM_A_TEST = 0.0001
MAKEHAM_B_TEST = 0.00003
MAKEHAM_C_TEST = 1.1

# --- Tes untuk Asumsi yang Sudah Ada (pastikan masih relevan) ---
def test_nsp_wl_assumption_constant_qx():
    """Tes NSP Whole Life dengan asumsi qx konstan."""
    result = nsp_wl_assumption(
        age=AGE, 
        interest_rate=INTEREST_RATE, 
        assumption_type='constant_qx', 
        params=[QX_CONST_TEST] # Menggunakan list untuk params
    )
    assert isinstance(result, ActuarialResult)
    assert result.value > 0 
    assert f"A_{{{AGE}}}" in result.formula_latex
    assert f"q_x konstan = {QX_CONST_TEST}" in result.description

def test_nsp_wl_assumption_constant_px():
    """Tes NSP Whole Life dengan asumsi px konstan."""
    result = nsp_wl_assumption(
        age=AGE, 
        interest_rate=INTEREST_RATE, 
        assumption_type='constant_px', 
        params=[PX_CONST_TEST]
    )
    assert isinstance(result, ActuarialResult)
    assert result.value > 0
    assert f"A_{{{AGE}}}" in result.formula_latex
    assert f"p_x konstan = {PX_CONST_TEST}" in result.description

def test_nsp_wl_assumption_de_moivre():
    """Tes NSP Whole Life dengan asumsi De Moivre."""
    result = nsp_wl_assumption(
        age=AGE, 
        interest_rate=INTEREST_RATE, 
        assumption_type='de_moivre', 
        params=[float(OMEGA_TEST)]
    )
    assert isinstance(result, ActuarialResult)
    assert result.value > 0
    assert f"A_{{{AGE}}}" in result.formula_latex
    assert f"De Moivre (ω={OMEGA_TEST})" in result.description

def test_nsp_wl_assumption_constant_mu_cfm():
    """Tes NSP Whole Life dengan asumsi mu konstan (CFM)."""
    result = nsp_wl_assumption(
        age=AGE, 
        interest_rate=INTEREST_RATE, 
        assumption_type='constant_mu_cfm', 
        params=[MU_TEST]
    )
    assert isinstance(result, ActuarialResult)
    assert result.value > 0
    assert f"A_{{{AGE}}}" in result.formula_latex
    assert f"CFM (μ={MU_TEST})" in result.description

# --- Tes untuk PV Anuitas (Contoh untuk satu asumsi, tambahkan yang lain) ---
def test_pv_annuity_assumption_constant_qx():
    result = pv_annuity_due_wl_assumption(
        age=AGE, interest_rate=INTEREST_RATE, assumption_type='constant_qx', params=[QX_CONST_TEST]
    )
    assert isinstance(result, ActuarialResult)
    assert result.value > 0
    assert f"\\ddot{{a}}_{{{AGE}}}" in result.formula_latex

# --- Tes untuk Probabilitas Hidup (Contoh untuk satu asumsi, tambahkan yang lain) ---
def test_survival_prob_assumption_constant_qx():
    period = 2.5
    result = survival_prob_assumption(
        age=AGE, period=period, interest_rate=INTEREST_RATE, assumption_type='constant_qx', params=[QX_CONST_TEST]
    )
    assert isinstance(result, ActuarialResult)
    expected_value = (1.0 - QX_CONST_TEST) ** period
    assert result.value == pytest.approx(expected_value)
    assert f"_{{{period:.2f}}}p_{{{AGE}}}" in result.formula_latex
    assert f"q_x konstan = {QX_CONST_TEST}" in result.description

def test_survival_prob_assumption_de_moivre():
    period = 5.0
    result = survival_prob_assumption(
        age=AGE, period=period, interest_rate=INTEREST_RATE, assumption_type='de_moivre', params=[float(OMEGA_TEST)]
    )
    assert isinstance(result, ActuarialResult)
    expected_value = (OMEGA_TEST - AGE - period) / (OMEGA_TEST - AGE) if (OMEGA_TEST - AGE) != 0 else 0.0
    if AGE + period >= OMEGA_TEST : expected_value = 0.0
    if AGE >= OMEGA_TEST and period > 0 : expected_value = 0.0
    if AGE >= OMEGA_TEST and period == 0 : expected_value = 1.0


    assert result.value == pytest.approx(expected_value)
    assert f"_{{{int(period)}}}p_{{{AGE}}}" in result.formula_latex
    assert f"De Moivre (ω={OMEGA_TEST})" in result.description

def test_survival_prob_assumption_constant_mu_cfm():
    period = 3.7
    result = survival_prob_assumption(
        age=AGE, period=period, interest_rate=INTEREST_RATE, assumption_type='constant_mu_cfm', params=[MU_TEST]
    )
    assert isinstance(result, ActuarialResult)
    expected_value = math.exp(-MU_TEST * period)
    assert result.value == pytest.approx(expected_value)
    assert f"_{{{period:.2f}}}p_{{{AGE}}}" in result.formula_latex
    assert f"CFM (μ={MU_TEST})" in result.description

# --- TES BARU UNTUK GOMPERTZ ---
def test_survival_prob_assumption_gompertz():
    """Tes Probabilitas Hidup dengan asumsi Gompertz."""
    age_g = 60
    period_g = 1.0 # Periode 1 tahun untuk mencocokkan dengan p_x tahunan
    params_g = [GOMPERTZ_B_TEST, GOMPERTZ_C_TEST]
    result = survival_prob_assumption(
        age=age_g, period=period_g, interest_rate=INTEREST_RATE, 
        assumption_type='gompertz', params=params_g
    )
    assert isinstance(result, ActuarialResult)
    assert 0 < result.value < 1

    # Perhitungan manual untuk p_x Gompertz (periode 1 tahun)
    # p_x = exp(- integral(B*c^(x+s) ds, s from 0 to 1) )
    # integral = B * c^x * (c-1) / ln(c)
    mu_at_x = GOMPERTZ_B_TEST * (GOMPERTZ_C_TEST ** age_g)
    if GOMPERTZ_C_TEST == 1.0:
        expected_px = math.exp(-mu_at_x)
    else:
        integral_mu = mu_at_x * (GOMPERTZ_C_TEST - 1.0) / math.log(GOMPERTZ_C_TEST)
        expected_px = math.exp(-integral_mu)
    
    assert result.value == pytest.approx(expected_px)
    assert f"_{{{int(period_g)}}}p_{{{age_g}}}" in result.formula_latex
    assert f"Gompertz (B={GOMPERTZ_B_TEST:.6g}, c={GOMPERTZ_C_TEST:.6g})" in result.description

def test_nsp_wl_assumption_gompertz():
    """Tes NSP Whole Life dengan asumsi Gompertz."""
    params_g = [GOMPERTZ_B_TEST, GOMPERTZ_C_TEST]
    result = nsp_wl_assumption(
        age=AGE, interest_rate=INTEREST_RATE, assumption_type='gompertz', params=params_g
    )
    assert isinstance(result, ActuarialResult)
    assert result.value > 0 # Nilai eksak memerlukan loop atau formula kompleks

# --- TES BARU UNTUK MAKEHAM ---
def test_survival_prob_assumption_makeham():
    """Tes Probabilitas Hidup dengan asumsi Makeham."""
    age_m = 60
    period_m = 1.0
    params_m = [MAKEHAM_A_TEST, MAKEHAM_B_TEST, MAKEHAM_C_TEST]
    result = survival_prob_assumption(
        age=age_m, period=period_m, interest_rate=INTEREST_RATE,
        assumption_type='makeham', params=params_m
    )
    assert isinstance(result, ActuarialResult)
    assert 0 < result.value < 1

    # Perhitungan manual untuk p_x Makeham (periode 1 tahun)
    # p_x = exp( - (A + integral(B*c^(x+s) ds, s from 0 to 1)) )
    integral_A = MAKEHAM_A_TEST
    mu_gompertz_part_at_x = MAKEHAM_B_TEST * (MAKEHAM_C_TEST ** age_m)
    integral_Bc_part: float
    if MAKEHAM_C_TEST == 1.0:
        integral_Bc_part = MAKEHAM_B_TEST
    else:
        integral_Bc_part = mu_gompertz_part_at_x * (MAKEHAM_C_TEST - 1.0) / math.log(MAKEHAM_C_TEST)
    expected_px = math.exp(-(integral_A + integral_Bc_part))

    assert result.value == pytest.approx(expected_px)
    assert f"_{{{int(period_m)}}}p_{{{age_m}}}" in result.formula_latex
    assert f"Makeham (A={MAKEHAM_A_TEST:.6g}, B={MAKEHAM_B_TEST:.6g}, c={MAKEHAM_C_TEST:.6g})" in result.description


def test_nsp_wl_assumption_makeham():
    """Tes NSP Whole Life dengan asumsi Makeham."""
    params_m = [MAKEHAM_A_TEST, MAKEHAM_B_TEST, MAKEHAM_C_TEST]
    result = nsp_wl_assumption(
        age=AGE, interest_rate=INTEREST_RATE, assumption_type='makeham', params=params_m
    )
    assert isinstance(result, ActuarialResult)
    assert result.value > 0 # Nilai eksak memerlukan loop atau formula kompleks


def test_invalid_assumption_params():
    """Tes untuk parameter asumsi yang tidak valid."""
    with pytest.raises(ValueError): # Pesan error bisa lebih spesifik
        survival_prob_assumption(AGE, 1.0, INTEREST_RATE, 'gompertz', params=[0.001]) # Kurang parameter c
    with pytest.raises(ValueError):
        survival_prob_assumption(AGE, 1.0, INTEREST_RATE, 'makeham', params=[0.001, 0.0001]) # Kurang parameter c
    with pytest.raises(ValueError, match="Nilai q_x untuk 'constant_qx' harus antara 0 dan 1."):
        survival_prob_assumption(AGE, 1.0, INTEREST_RATE, 'constant_qx', params=[1.5])