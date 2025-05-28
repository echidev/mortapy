# tests/test_api_assumptions.py
import pytest
from mortapy import (
    nsp_wl_assumption,
    pv_annuity_due_wl_assumption,
    survival_prob_assumption,
    death_prob_assumption,
    deferred_death_prob_assumption,
    fom_assumption,
    pdf_death_assumption,
    ex_curtate_assumption,
    e_sq_curtate_assumption,
    var_k_assumption
)
from mortapy.result import ActuarialResult
import math
from typing import Literal, Optional, Any, List, Callable

# Parameter umum
AGE_API_ASSUM = 35
INTEREST_RATE_API_ASSUM = 0.05
PERIOD_FLOAT_API_ASSUM = 2.5
# PERIOD_INT_API_ASSUM = 2 # Tidak terpakai langsung di semua tes asumsi saat ini
DEFER_T_API_ASSUM = 1.5
DEATH_U_API_ASSUM = 3.2
T_OFFSET_FOM = 0.75
N_TEMP_MOMENT_ASSUM = 3

# Parameter untuk Asumsi
QX_PARAMS = [0.01]
PX_PARAMS = [0.99]
DE_MOIVRE_PARAMS = [110.0]
BETA_DIST_PARAMS = [110.0, 1.0]
BETA_DIST_PARAMS_ALPHA2 = [110.0, 2.0]
CFM_PARAMS = [0.02]
GOMPERTZ_PARAMS = [0.00005, 1.09]
MAKEHAM_PARAMS = [0.0001, 0.00003, 1.1]

# === Tes untuk survival_probability_from_assumption ===
@pytest.mark.parametrize("assumption_type, params, manual_calc_func, expected_desc_keyword_part", [
    ('constant_qx', QX_PARAMS, lambda age, period, p: (1.0 - p[0])**period, "q_x konstan"),
    ('constant_px', PX_PARAMS, lambda age, period, p: p[0]**period, "p_x konstan"),
    ('de_moivre', DE_MOIVRE_PARAMS,
     lambda age, period, p: (p[0]-age-period)/(p[0]-age) if (p[0]-age)!=0 and age+period < p[0] else (0.0 if age+period >= p[0] else (1.0 if period == 0 and age+period>=p[0] else 0.0)),
     "de moivre"),
    ('beta_distribution', BETA_DIST_PARAMS,
     lambda age, period, p: ((p[0]-age-period)/(p[0]-age))**p[1] if (p[0]-age)!=0 and age+period < p[0] else (0.0 if age+period >= p[0] else (1.0 if period == 0 and age+period>=p[0] else 0.0)),
     "beta dist."),
    ('beta_distribution', BETA_DIST_PARAMS_ALPHA2,
     lambda age, period, p: ((p[0]-age-period)/(p[0]-age))**p[1] if (p[0]-age)!=0 and age+period < p[0] else (0.0 if age+period >= p[0] else (1.0 if period == 0 and age+period>=p[0] else 0.0)),
     "beta dist."),
    ('constant_mu_cfm', CFM_PARAMS, lambda age, period, p: math.exp(-p[0]*period), "cfm"),
    ('gompertz', GOMPERTZ_PARAMS,
     lambda age, period, p: math.exp(-p[0]*(p[1]**age)*(p[1]**period-1)/math.log(p[1])) if abs(p[1]-1.0) > 1e-9 else math.exp(-p[0]*period*(p[1]**age)),
     "gompertz"),
    ('makeham', MAKEHAM_PARAMS,
     lambda age, period, p: math.exp(-(p[0]*period + p[1]*(p[2]**age)*(p[2]**period-1)/math.log(p[2]))) if abs(p[2]-1.0) > 1e-9 else math.exp(-(p[0]*period + p[1]*period*(p[2]**age))),
     "makeham"),
])
def test_survival_prob_various_assumptions(assumption_type, params, manual_calc_func, expected_desc_keyword_part):
    result = survival_prob_assumption(
        age=AGE_API_ASSUM,
        period=PERIOD_FLOAT_API_ASSUM,
        interest_rate=INTEREST_RATE_API_ASSUM,
        assumption_type=assumption_type, # type: ignore
        params=params
    )
    assert isinstance(result, ActuarialResult)
    expected_value = manual_calc_func(AGE_API_ASSUM, PERIOD_FLOAT_API_ASSUM, params)
    assert result.value == pytest.approx(expected_value, abs=1e-7)
    assert f"_{{{PERIOD_FLOAT_API_ASSUM:.2f}}}p_{{{AGE_API_ASSUM}}}" in result.formula_latex
    assert expected_desc_keyword_part.lower() in result.description.lower()


# === Tes untuk death_probability_from_assumption ===
@pytest.mark.parametrize("assumption_type, params, expected_desc_keyword_part", [
    ('constant_qx', QX_PARAMS, "q_x konstan"),
    ('beta_distribution', BETA_DIST_PARAMS_ALPHA2, "beta dist."),
    ('gompertz', GOMPERTZ_PARAMS, "gompertz")
])
def test_death_prob_various_assumptions(assumption_type, params, expected_desc_keyword_part):
    result_q = death_prob_assumption(
        age=AGE_API_ASSUM, period=PERIOD_FLOAT_API_ASSUM, interest_rate=INTEREST_RATE_API_ASSUM,
        assumption_type=assumption_type, params=params # type: ignore
    )
    result_p = survival_prob_assumption(
        age=AGE_API_ASSUM, period=PERIOD_FLOAT_API_ASSUM, interest_rate=INTEREST_RATE_API_ASSUM,
        assumption_type=assumption_type, params=params # type: ignore
    )
    assert isinstance(result_q, ActuarialResult)
    assert result_q.value == pytest.approx(1.0 - result_p.value)
    assert f"_{{{PERIOD_FLOAT_API_ASSUM:.2f}}}q_{{{AGE_API_ASSUM}}}" in result_q.formula_latex
    assert expected_desc_keyword_part.lower() in result_q.description.lower()

# === Tes untuk deferred_death_probability_from_assumption ===
@pytest.mark.parametrize("assumption_type, params, expected_desc_keyword_part", [
    ('constant_mu_cfm', CFM_PARAMS, "cfm"),
    ('beta_distribution', BETA_DIST_PARAMS, "beta dist.")
])
def test_deferred_death_prob_various_assumptions(assumption_type, params, expected_desc_keyword_part):
    result = deferred_death_prob_assumption(
        age=AGE_API_ASSUM, deferral_period=DEFER_T_API_ASSUM, death_period=DEATH_U_API_ASSUM,
        interest_rate=INTEREST_RATE_API_ASSUM, assumption_type=assumption_type, params=params # type: ignore
    )
    t_px_res = survival_prob_assumption(AGE_API_ASSUM, DEFER_T_API_ASSUM, INTEREST_RATE_API_ASSUM, assumption_type, params) # type: ignore
    t_plus_u_px_res = survival_prob_assumption(AGE_API_ASSUM, DEFER_T_API_ASSUM + DEATH_U_API_ASSUM, INTEREST_RATE_API_ASSUM, assumption_type, params) # type: ignore

    assert isinstance(result, ActuarialResult)
    assert result.value == pytest.approx(t_px_res.value - t_plus_u_px_res.value, abs=1e-7)
    assert f"_{{{DEFER_T_API_ASSUM:.2f}|{DEATH_U_API_ASSUM:.2f}}}q_{{{AGE_API_ASSUM}}}" in result.formula_latex
    assert expected_desc_keyword_part.lower() in result.description.lower()


# === Tes untuk force_of_mortality_at_age_t ===
@pytest.mark.parametrize("assumption_type, params, manual_mu_func", [
    ('constant_qx', QX_PARAMS, lambda age, t_off, p: -math.log(1.0 - p[0]) if p[0]<1.0 else float('inf')),
    ('constant_px', PX_PARAMS, lambda age, t_off, p: -math.log(p[0]) if p[0]>0 else float('inf')),
    ('de_moivre', DE_MOIVRE_PARAMS, lambda age, t_off, p: 1.0/(p[0]-(age+t_off)) if (age+t_off) < p[0] and (p[0]-(age+t_off))!=0 else float('inf')),
    ('beta_distribution', BETA_DIST_PARAMS_ALPHA2, lambda age, t_off, p: p[1]/(p[0]-(age+t_off)) if (age+t_off) < p[0] and (p[0]-(age+t_off))!=0 else float('inf')),
    ('constant_mu_cfm', CFM_PARAMS, lambda age, t_off, p: p[0]),
    ('gompertz', GOMPERTZ_PARAMS, lambda age, t_off, p: p[0] * (p[1]**(age+t_off))),
    ('makeham', MAKEHAM_PARAMS, lambda age, t_off, p: p[0] + p[1] * (p[2]**(age+t_off))),
])
def test_fom_various_assumptions(assumption_type, params, manual_mu_func):
    result = fom_assumption(
        age=AGE_API_ASSUM, t_offset=T_OFFSET_FOM, interest_rate=INTEREST_RATE_API_ASSUM,
        assumption_type=assumption_type, params=params # type: ignore
    )
    assert isinstance(result, ActuarialResult)
    expected_mu = manual_mu_func(AGE_API_ASSUM, T_OFFSET_FOM, params)
    assert result.value == pytest.approx(expected_mu, abs=1e-7)

    age_display_in_test = f"{AGE_API_ASSUM}"
    if T_OFFSET_FOM > 0:
        t_offset_str_in_test = f"{T_OFFSET_FOM:.2f}".rstrip('0').rstrip('.')
        age_display_in_test += f"+{t_offset_str_in_test}"

    assert result.formula_latex == rf"\mu_{{{age_display_in_test}}}"


# === Tes untuk pdf_death_at_age_t ===
@pytest.mark.parametrize("assumption_type, params", [
    ('constant_mu_cfm', CFM_PARAMS),
    ('de_moivre', DE_MOIVRE_PARAMS),
    ('gompertz', GOMPERTZ_PARAMS),
    ('beta_distribution', BETA_DIST_PARAMS_ALPHA2),
    ('makeham', MAKEHAM_PARAMS)
])
def test_pdf_death_various_assumptions(assumption_type, params):
    t_period_pdf = T_OFFSET_FOM
    result_pdf = pdf_death_assumption(
        age=AGE_API_ASSUM, t_period=t_period_pdf, interest_rate=INTEREST_RATE_API_ASSUM,
        assumption_type=assumption_type, params=params # type: ignore
    )
    result_tpx = survival_prob_assumption(
        age=AGE_API_ASSUM, period=t_period_pdf, interest_rate=INTEREST_RATE_API_ASSUM,
        assumption_type=assumption_type, params=params # type: ignore
    )
    result_mu = fom_assumption(
        age=AGE_API_ASSUM, t_offset=t_period_pdf, interest_rate=INTEREST_RATE_API_ASSUM,
        assumption_type=assumption_type, params=params # type: ignore
    )
    assert isinstance(result_pdf, ActuarialResult)
    assert result_pdf.value == pytest.approx(result_tpx.value * result_mu.value, abs=1e-7)
    expected_formula = rf"{result_tpx.formula_latex} \cdot {result_mu.formula_latex}"
    assert result_pdf.formula_latex == expected_formula


# --- Tes untuk NSP dan Anuitas ---
ALL_ASSUMPTIONS_WITH_PARAMS_FOR_SMOKE = [
    ('constant_qx', QX_PARAMS, "q_x konstan"),
    ('constant_px', PX_PARAMS, "p_x konstan"),
    ('de_moivre', DE_MOIVRE_PARAMS, "de moivre"),
    ('beta_distribution', BETA_DIST_PARAMS, "beta dist."), # Menggunakan BETA_DIST_PARAMS
    ('beta_distribution', BETA_DIST_PARAMS_ALPHA2, "beta dist."),
    ('constant_mu_cfm', CFM_PARAMS, "cfm"),
    ('gompertz', GOMPERTZ_PARAMS, "gompertz"),
    ('makeham', MAKEHAM_PARAMS, "makeham"),
]

@pytest.mark.parametrize("assumption_type, params, expected_desc_keyword_part", ALL_ASSUMPTIONS_WITH_PARAMS_FOR_SMOKE)
def test_nsp_wl_all_assumptions_smoke(assumption_type, params, expected_desc_keyword_part):
    result = nsp_wl_assumption(
        age=AGE_API_ASSUM, interest_rate=INTEREST_RATE_API_ASSUM,
        assumption_type=assumption_type, params=params # type: ignore
    )
    assert isinstance(result, ActuarialResult)
    assert result.value >= 0
    assert expected_desc_keyword_part.lower() in result.description.lower()


@pytest.mark.parametrize("assumption_type, params, expected_desc_keyword_part", ALL_ASSUMPTIONS_WITH_PARAMS_FOR_SMOKE)
def test_pv_annuity_all_assumptions_smoke(assumption_type, params, expected_desc_keyword_part):
    result = pv_annuity_due_wl_assumption(
        age=AGE_API_ASSUM, interest_rate=INTEREST_RATE_API_ASSUM,
        assumption_type=assumption_type, params=params # type: ignore
    )
    assert isinstance(result, ActuarialResult)
    assert result.value >= 0
    assert expected_desc_keyword_part.lower() in result.description.lower()


# --- Tes untuk Momen Curtate ---
@pytest.mark.parametrize("assumption_type, params, n_temp_test, expected_desc_keyword_part", [
    ('constant_qx', QX_PARAMS, None, "q_x konstan"),
    ('constant_qx', QX_PARAMS, N_TEMP_MOMENT_ASSUM, "q_x konstan"),
    ('de_moivre', DE_MOIVRE_PARAMS, None, "de moivre"),
    ('de_moivre', DE_MOIVRE_PARAMS, N_TEMP_MOMENT_ASSUM, "de moivre"),
    ('beta_distribution', BETA_DIST_PARAMS_ALPHA2, None, "beta dist."),
    ('gompertz', GOMPERTZ_PARAMS, N_TEMP_MOMENT_ASSUM, "gompertz")
])
def test_ex_curtate_various_assumptions(assumption_type, params, n_temp_test, expected_desc_keyword_part):
    result = ex_curtate_assumption(
        age=AGE_API_ASSUM,
        interest_rate=INTEREST_RATE_API_ASSUM,
        assumption_type=assumption_type, # type: ignore
        params=params,
        n_temp=n_temp_test
    )
    assert isinstance(result, ActuarialResult)
    assert result.value >= 0
    expected_subscript = str(AGE_API_ASSUM)
    if n_temp_test is not None:
        expected_subscript += rf":\overline{{{n_temp_test}}}|"
    assert result.formula_latex == rf"e_{{{expected_subscript}}}"
    assert expected_desc_keyword_part.lower() in result.description.lower()

@pytest.mark.parametrize("assumption_type, params, n_temp_test, expected_desc_keyword_part", [
    ('constant_px', PX_PARAMS, None, "p_x konstan"),
    ('constant_px', PX_PARAMS, N_TEMP_MOMENT_ASSUM, "p_x konstan"),
    ('constant_mu_cfm', CFM_PARAMS, None, "cfm"),
    ('constant_mu_cfm', CFM_PARAMS, N_TEMP_MOMENT_ASSUM, "cfm"),
    ('makeham', MAKEHAM_PARAMS, N_TEMP_MOMENT_ASSUM, "makeham")
])
def test_e_sq_curtate_various_assumptions(assumption_type, params, n_temp_test, expected_desc_keyword_part):
    result = e_sq_curtate_assumption(
        age=AGE_API_ASSUM,
        interest_rate=INTEREST_RATE_API_ASSUM,
        assumption_type=assumption_type, # type: ignore
        params=params,
        n_temp=n_temp_test
    )
    assert isinstance(result, ActuarialResult)
    assert result.value >= 0
    expected_subscript = str(AGE_API_ASSUM)
    if n_temp_test is not None:
        expected_subscript += rf":\overline{{{n_temp_test}}}|"
    assert result.formula_latex == rf"E[K_{{{expected_subscript}}}^2]"
    assert expected_desc_keyword_part.lower() in result.description.lower()

@pytest.mark.parametrize("assumption_type, params, n_temp_test, expected_desc_keyword_part", [
    ('de_moivre', DE_MOIVRE_PARAMS, None, "de moivre"),
    ('de_moivre', DE_MOIVRE_PARAMS, N_TEMP_MOMENT_ASSUM, "de moivre"),
    ('gompertz', GOMPERTZ_PARAMS, N_TEMP_MOMENT_ASSUM, "gompertz"),
    ('beta_distribution', BETA_DIST_PARAMS_ALPHA2, None, "beta dist.")
])
def test_var_k_various_assumptions(assumption_type, params, n_temp_test, expected_desc_keyword_part):
    result = var_k_assumption(
        age=AGE_API_ASSUM,
        interest_rate=INTEREST_RATE_API_ASSUM,
        assumption_type=assumption_type, # type: ignore
        params=params,
        n_temp=n_temp_test
    )
    assert isinstance(result, ActuarialResult)
    assert result.value >= 0
    ex_res = ex_curtate_assumption(AGE_API_ASSUM, INTEREST_RATE_API_ASSUM, assumption_type, params, n_temp_test) # type: ignore
    e_sq_res = e_sq_curtate_assumption(AGE_API_ASSUM, INTEREST_RATE_API_ASSUM, assumption_type, params, n_temp_test) # type: ignore
    assert result.value == pytest.approx(e_sq_res.value - (ex_res.value**2), abs=1e-7)
    expected_subscript = str(AGE_API_ASSUM)
    if n_temp_test is not None:
        expected_subscript += rf":\overline{{{n_temp_test}}}|"
    assert result.formula_latex == rf"Var[K_{{{expected_subscript}}}]"
    assert expected_desc_keyword_part.lower() in result.description.lower()

def test_invalid_assumption_parameters_extended():
    """Tes untuk parameter asumsi yang tidak valid (lanjutan)."""
    with pytest.raises(ValueError):
        survival_prob_assumption(AGE_API_ASSUM, 1.0, INTEREST_RATE_API_ASSUM, 'gompertz', params=[0.001])
    with pytest.raises(ValueError):
        survival_prob_assumption(AGE_API_ASSUM, 1.0, INTEREST_RATE_API_ASSUM, 'makeham', params=[0.001, 0.0001])
    with pytest.raises(ValueError):
        survival_prob_assumption(AGE_API_ASSUM, 1.0, INTEREST_RATE_API_ASSUM, 'beta_distribution', params=[100.0])
    with pytest.raises(ValueError, match="Nilai q_x untuk 'constant_qx' harus antara 0 dan 1."):
        survival_prob_assumption(AGE_API_ASSUM, 1.0, INTEREST_RATE_API_ASSUM, 'constant_qx', params=[1.5])
    with pytest.raises(ValueError, match="Omega untuk De Moivre harus integer positif."):
        survival_prob_assumption(AGE_API_ASSUM, 1.0, INTEREST_RATE_API_ASSUM, 'de_moivre', params=[-100.0])
    with pytest.raises(ValueError, match="Nilai μ untuk 'constant_mu_cfm' harus non-negatif."):
        survival_prob_assumption(AGE_API_ASSUM, 1.0, INTEREST_RATE_API_ASSUM, 'constant_mu_cfm', params=[-0.01])