import pytest
from mortapy import (
    nsp_wl_assumption,  
    pv_annuity_due_wl_assumption,
    survival_prob_assumption
)
from mortapy.result import ActuarialResult 
import math

AGE = 35
INTEREST_RATE = 0.05
OMEGA_TEST = 110
MU_TEST = 0.02
QX_CONST_TEST = 0.01
PX_CONST_TEST = 0.98

def test_nsp_wl_assumption_constant_qx():
    """Tes NSP Whole Life dengan asumsi qx konstan."""
    result = nsp_wl_assumption(
        age=AGE, 
        interest_rate=INTEREST_RATE, 
        assumption_type='constant_qx', 
        param1=QX_CONST_TEST
    )
    assert isinstance(result, ActuarialResult)
    assert result.value > 0 
    assert f"A_{{{AGE}}}" in result.formula_latex
    assert f"q_x konstan = {QX_CONST_TEST}" in result.description
    # Nilai eksak bisa dihitung manual atau dari sumber tepercaya untuk qx konstan

def test_nsp_wl_assumption_constant_px():
    """Tes NSP Whole Life dengan asumsi px konstan."""
    result = nsp_wl_assumption(
        age=AGE, 
        interest_rate=INTEREST_RATE, 
        assumption_type='constant_px', 
        param1=PX_CONST_TEST
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
        param1=OMEGA_TEST
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
        param1=MU_TEST
    )
    assert isinstance(result, ActuarialResult)
    assert result.value > 0
    assert f"A_{{{AGE}}}" in result.formula_latex
    assert f"CFM (μ={MU_TEST})" in result.description

# --- Tes untuk pv_annuity_due_whole_life_from_assumption ---
def test_pv_annuity_assumption_constant_qx():
    result = pv_annuity_due_wl_assumption(
        age=AGE, interest_rate=INTEREST_RATE, assumption_type='constant_qx', param1=QX_CONST_TEST
    )
    assert isinstance(result, ActuarialResult)
    assert result.value > 0
    assert f"\\ddot{{a}}_{{{AGE}}}" in result.formula_latex

# --- Tes untuk survival_probability_from_assumption ---
def test_survival_prob_assumption_constant_qx():
    period = 2.5
    result = survival_prob_assumption(
        age=AGE, period=period, interest_rate=INTEREST_RATE, assumption_type='constant_qx', param1=QX_CONST_TEST
    )
    assert isinstance(result, ActuarialResult)
    expected_value = (1.0 - QX_CONST_TEST) ** period
    assert result.value == pytest.approx(expected_value)
    assert f"_{{{period:.2f}}}p_{{{AGE}}}" in result.formula_latex # Memastikan format periode
    assert f"q_x konstan = {QX_CONST_TEST}" in result.description

def test_survival_prob_assumption_de_moivre():
    period = 5.0
    result = survival_prob_assumption(
        age=AGE, period=period, interest_rate=INTEREST_RATE, assumption_type='de_moivre', param1=OMEGA_TEST
    )
    assert isinstance(result, ActuarialResult)
    expected_value = (OMEGA_TEST - AGE - period) / (OMEGA_TEST - AGE)
    assert result.value == pytest.approx(expected_value)
    assert f"_{{{int(period)}}}p_{{{AGE}}}" in result.formula_latex # Periode bulat
    assert f"De Moivre (ω={OMEGA_TEST})" in result.description

def test_survival_prob_assumption_constant_mu_cfm():
    period = 3.7
    result = survival_prob_assumption(
        age=AGE, period=period, interest_rate=INTEREST_RATE, assumption_type='constant_mu_cfm', param1=MU_TEST
    )
    assert isinstance(result, ActuarialResult)
    expected_value = math.exp(-MU_TEST * period)
    assert result.value == pytest.approx(expected_value)
    assert f"_{{{period:.2f}}}p_{{{AGE}}}" in result.formula_latex
    assert f"CFM (μ={MU_TEST})" in result.description

def test_invalid_assumption_type():
    """Tes untuk tipe asumsi yang tidak valid."""
    with pytest.raises(ValueError, match="Tipe asumsi tidak dikenal"):
        nsp_wl_assumption(age=AGE, interest_rate=INTEREST_RATE, assumption_type="unknown_type", param1=0.1) # type: ignore