# tests/test_api_assumptions.py
import pytest
from mortapy import (
    nsp_wl_assumption, 
    pv_annuity_due_wl_assumption,
    survival_prob_assumption,
    death_prob_assumption,
    deferred_death_prob_assumption,
    fom_assumption,
    pdf_death_assumption
)
from mortapy.result import ActuarialResult
import math

# Parameter umum
AGE_API_ASSUM = 35
INTEREST_RATE_API_ASSUM = 0.05
PERIOD_FLOAT_API_ASSUM = 2.5
PERIOD_INT_API_ASSUM = 2
DEFER_T_API_ASSUM = 1.5
DEATH_U_API_ASSUM = 3.2
T_OFFSET_FOM = 0.75


# --- Parameter untuk Asumsi ---
QX_PARAMS = [0.01]
PX_PARAMS = [0.98]
DE_MOIVRE_PARAMS = [110.0] # Omega
CFM_PARAMS = [0.02]       # Mu
GOMPERTZ_PARAMS = [0.00005, 1.09] # B, c
MAKEHAM_PARAMS = [0.0001, 0.00003, 1.1] # A, B, c

# === Tes untuk survival_probability_from_assumption ===
@pytest.mark.parametrize("assumption_type, params, manual_calc_func, expected_desc_keyword", [
    ('constant_qx', QX_PARAMS, lambda age, period, p: (1.0 - p[0])**period, "q_x konstan"),
    ('constant_px', PX_PARAMS, lambda age, period, p: p[0]**period, "p_x konstan"),
    ('de_moivre', DE_MOIVRE_PARAMS, lambda age, period, p: (p[0]-age-period)/(p[0]-age) if (p[0]-age)!=0 and age+period < p[0] else (0.0 if age+period >= p[0] else (1.0 if period == 0 and age >= p[0] else 0.0)), "de moivre"),
    ('constant_mu_cfm', CFM_PARAMS, lambda age, period, p: math.exp(-p[0]*period), "cfm"),
    ('gompertz', GOMPERTZ_PARAMS, lambda age, period, p: math.exp(-p[0]*(p[1]**age)*(p[1]**period-1)/math.log(p[1])) if p[1]!=1 else math.exp(-p[0]*period), "gompertz"),
    ('makeham', MAKEHAM_PARAMS, lambda age, period, p: math.exp(-(p[0]*period + p[1]*(p[2]**age)*(p[2]**period-1)/math.log(p[2]))) if p[2]!=1 else math.exp(-(p[0]*period + p[1]*period)), "makeham"),
])
def test_survival_prob_various_assumptions(assumption_type, params, manual_calc_func, expected_desc_keyword): # Tambah expected_desc_keyword
    """Tes survival_probability_from_assumption dengan berbagai asumsi."""
    result = survival_prob_assumption(
        age=AGE_API_ASSUM,
        period=PERIOD_FLOAT_API_ASSUM,
        interest_rate=INTEREST_RATE_API_ASSUM,
        assumption_type=assumption_type, 
        params=params
    )
    assert isinstance(result, ActuarialResult)
    expected_value = manual_calc_func(AGE_API_ASSUM, PERIOD_FLOAT_API_ASSUM, params)
    assert result.value == pytest.approx(expected_value)
    assert f"_{{{PERIOD_FLOAT_API_ASSUM:.2f}}}p_{{{AGE_API_ASSUM}}}" in result.formula_latex
    assert expected_desc_keyword in result.description.lower() # Gunakan keyword yang diharapkan


# === Tes untuk death_probability_from_assumption ===
@pytest.mark.parametrize("assumption_type, params", [
    ('constant_qx', QX_PARAMS), ('constant_px', PX_PARAMS), 
    ('de_moivre', DE_MOIVRE_PARAMS), ('constant_mu_cfm', CFM_PARAMS),
    ('gompertz', GOMPERTZ_PARAMS), ('makeham', MAKEHAM_PARAMS)
])
def test_death_prob_various_assumptions(assumption_type, params):
    """Tes death_probability_from_assumption."""
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

# === Tes untuk deferred_death_probability_from_assumption ===
@pytest.mark.parametrize("assumption_type, params", [
    ('constant_qx', QX_PARAMS), ('constant_px', PX_PARAMS),
    ('de_moivre', DE_MOIVRE_PARAMS), ('constant_mu_cfm', CFM_PARAMS),
    ('gompertz', GOMPERTZ_PARAMS), ('makeham', MAKEHAM_PARAMS)
])
def test_deferred_death_prob_various_assumptions(assumption_type, params):
    """Tes deferred_death_probability_from_assumption."""
    result = deferred_death_prob_assumption(
        age=AGE_API_ASSUM, deferral_period=DEFER_T_API_ASSUM, death_period=DEATH_U_API_ASSUM,
        interest_rate=INTEREST_RATE_API_ASSUM, assumption_type=assumption_type, params=params # type: ignore
    )
    t_px_res = survival_prob_assumption(AGE_API_ASSUM, DEFER_T_API_ASSUM, INTEREST_RATE_API_ASSUM, assumption_type, params) # type: ignore
    t_plus_u_px_res = survival_prob_assumption(AGE_API_ASSUM, DEFER_T_API_ASSUM + DEATH_U_API_ASSUM, INTEREST_RATE_API_ASSUM, assumption_type, params) # type: ignore
    
    assert isinstance(result, ActuarialResult)
    assert result.value == pytest.approx(t_px_res.value - t_plus_u_px_res.value)
    assert f"_{{{DEFER_T_API_ASSUM:.2f}|{DEATH_U_API_ASSUM:.2f}}}q_{{{AGE_API_ASSUM}}}" in result.formula_latex


# === Tes untuk force_of_mortality_at_age_t ===
@pytest.mark.parametrize("assumption_type, params, manual_mu_func", [
    ('constant_qx', QX_PARAMS, lambda age, t_off, p: -math.log(1.0 - p[0]) if p[0]<1 else float('inf')),
    ('constant_px', PX_PARAMS, lambda age, t_off, p: -math.log(p[0]) if p[0]>0 else float('inf')),
    ('de_moivre', DE_MOIVRE_PARAMS, lambda age, t_off, p: 1.0/(p[0]-(age+t_off)) if (age+t_off) < p[0] and (p[0]-(age+t_off))!=0 else float('inf')),
    ('constant_mu_cfm', CFM_PARAMS, lambda age, t_off, p: p[0]),
    ('gompertz', GOMPERTZ_PARAMS, lambda age, t_off, p: p[0] * (p[1]**(age+t_off))),
    ('makeham', MAKEHAM_PARAMS, lambda age, t_off, p: p[0] + p[1] * (p[2]**(age+t_off))),
])
def test_fom_various_assumptions(assumption_type, params, manual_mu_func):
    """Tes force_of_mortality_at_age_t."""
    result = fom_assumption(
        age=AGE_API_ASSUM, t_offset=T_OFFSET_FOM, interest_rate=INTEREST_RATE_API_ASSUM,
        assumption_type=assumption_type, params=params # type: ignore
    )
    assert isinstance(result, ActuarialResult)
    expected_mu = manual_mu_func(AGE_API_ASSUM, T_OFFSET_FOM, params)
    assert result.value == pytest.approx(expected_mu)
    age_display = f"{AGE_API_ASSUM}+{T_OFFSET_FOM:.2f}".rstrip('0').rstrip('.')
    assert f"\\mu_{{{age_display}}}" in result.formula_latex


# === Tes untuk pdf_death_at_age_t ===
@pytest.mark.parametrize("assumption_type, params", [
    ('constant_mu_cfm', CFM_PARAMS), # Contoh satu asumsi, tambahkan lain jika perlu
    ('de_moivre', DE_MOIVRE_PARAMS),
    ('gompertz', GOMPERTZ_PARAMS),
])
def test_pdf_death_various_assumptions(assumption_type, params):
    """Tes pdf_death_at_age_t."""
    t_period_pdf = T_OFFSET_FOM # Gunakan t_offset yang sama sebagai periode t
    
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
    assert result_pdf.value == pytest.approx(result_tpx.value * result_mu.value)
    # Verifikasi formula bisa lebih kompleks, tapi setidaknya cek simbol utama
    age_at_death_display = f"{AGE_API_ASSUM}+{t_period_pdf:.2f}".rstrip('0').rstrip('.')
    assert f"p_{{{AGE_API_ASSUM}}}" in result_pdf.formula_latex
    assert f"\\mu_{{{age_at_death_display}}}" in result_pdf.formula_latex


# --- Tes untuk NSP dan Anuitas (cukup satu asumsi untuk contoh, bisa diperluas) ---
def test_nsp_wl_all_assumptions_smoke():
    """Smoke test untuk nsp_wl_assumption dengan semua tipe."""
    assumptions = {
        'constant_qx': QX_PARAMS, 'constant_px': PX_PARAMS,
        'de_moivre': DE_MOIVRE_PARAMS, 'constant_mu_cfm': CFM_PARAMS,
        'gompertz': GOMPERTZ_PARAMS, 'makeham': MAKEHAM_PARAMS
    }
    for assumption_type, params in assumptions.items():
        result = nsp_wl_assumption(
            age=AGE_API_ASSUM, interest_rate=INTEREST_RATE_API_ASSUM, 
            assumption_type=assumption_type, params=params # type: ignore
        )
        assert isinstance(result, ActuarialResult)
        assert result.value >= 0 # NSP tidak boleh negatif

def test_pv_annuity_all_assumptions_smoke():
    """Smoke test untuk pv_annuity_due_wl_assumption dengan semua tipe."""
    assumptions = {
        'constant_qx': QX_PARAMS, 'constant_px': PX_PARAMS,
        'de_moivre': DE_MOIVRE_PARAMS, 'constant_mu_cfm': CFM_PARAMS,
        'gompertz': GOMPERTZ_PARAMS, 'makeham': MAKEHAM_PARAMS
    }
    for assumption_type, params in assumptions.items():
        result = pv_annuity_due_wl_assumption(
            age=AGE_API_ASSUM, interest_rate=INTEREST_RATE_API_ASSUM, 
            assumption_type=assumption_type, params=params # type: ignore
        )
        assert isinstance(result, ActuarialResult)
        assert result.value >= 0 # PV Anuitas tidak boleh negatif


def test_invalid_assumption_params_extended():
    """Tes untuk parameter asumsi yang tidak valid (lanjutan)."""
    with pytest.raises(ValueError):
        survival_prob_assumption(AGE_API_ASSUM, 1.0, INTEREST_RATE_API_ASSUM, 'gompertz', params=[0.001])
    with pytest.raises(ValueError):
        survival_prob_assumption(AGE_API_ASSUM, 1.0, INTEREST_RATE_API_ASSUM, 'makeham', params=[0.001, 0.0001])
    with pytest.raises(ValueError, match="Nilai q_x untuk 'constant_qx' harus antara 0 dan 1."):
        survival_prob_assumption(AGE_API_ASSUM, 1.0, INTEREST_RATE_API_ASSUM, 'constant_qx', params=[1.5])
    with pytest.raises(ValueError, match="Omega untuk De Moivre harus integer positif."):
        survival_prob_assumption(AGE_API_ASSUM, 1.0, INTEREST_RATE_API_ASSUM, 'de_moivre', params=[-100])
    with pytest.raises(ValueError, match="Nilai μ untuk 'constant_mu_cfm' harus non-negatif."):
        survival_prob_assumption(AGE_API_ASSUM, 1.0, INTEREST_RATE_API_ASSUM, 'constant_mu_cfm', params=[-0.01])