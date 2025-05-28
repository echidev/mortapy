# mortapy/api_assumptions.py
from typing import Literal, Optional, Callable, List
import math
from .core_calculator import ActuarialCalculator
from .result import ActuarialResult

DEFAULT_OMEGA_DEMOIVRE: int = 110 
DEFAULT_ALPHA_BETA_DIST: float = 1.0 
DEFAULT_MU_CFM: float = 0.02 
DEFAULT_QX_CONSTANT: float = 0.01
DEFAULT_PX_CONSTANT: float = 0.98 
DEFAULT_GOMPERTZ_B: float = 0.00005
DEFAULT_GOMPERTZ_C: float = 1.08
DEFAULT_MAKEHAM_A: float = 0.00022
DEFAULT_MAKEHAM_B: float = 0.000027
DEFAULT_MAKEHAM_C: float = 1.075

ASSUMPTION_TYPES_LITERAL = Literal[
    'constant_qx', 'constant_px', 
    'de_moivre', 'beta_distribution',
    'constant_mu_cfm',
    'gompertz', 'makeham'
]

def _create_assumption_functions(
    assumption_type: ASSUMPTION_TYPES_LITERAL,
    params: List[float]
) -> tuple[
        Callable[[int], float], 
        Callable[[int], float], 
        int,                   
        str,                   
        Callable[[int, float], float], 
        Callable[[int, float], float]  
    ]:
    qx_func_yearly: Callable[[int], float]
    px_func_yearly: Callable[[int], float]
    mu_func_continuous: Callable[[int, float], float]
    px_func_continuous: Callable[[int, float], float] 
    omega: int = 150 
    assumption_description: str = ""

    if assumption_type == 'constant_qx':
        if not params or len(params) < 1: raise ValueError("Parameter qx_value dibutuhkan untuk 'constant_qx'.")
        qx_val = params[0]
        if not (0 <= qx_val <= 1): raise ValueError("Nilai q_x untuk 'constant_qx' harus antara 0 dan 1.")
        qx_func_yearly = lambda age_input: qx_val
        px_func_yearly = lambda age_input: 1.0 - qx_val
        mu_val = -math.log(1.0 - qx_val) if qx_val < 1.0 else float('inf')
        mu_func_continuous = lambda age_input, t_offset: mu_val
        px_func_continuous = lambda age_input, period: (1.0 - qx_val) ** period if qx_val < 1.0 else (0.0 if period > 0 else 1.0)
        assumption_description = f"q_x konstan = {qx_val}"
    
    elif assumption_type == 'constant_px':
        if not params or len(params) < 1: raise ValueError("Parameter px_value dibutuhkan untuk 'constant_px'.")
        px_val = params[0]
        if not (0 <= px_val <= 1): raise ValueError("Nilai p_x untuk 'constant_px' harus antara 0 dan 1.")
        px_func_yearly = lambda age_input: px_val
        qx_func_yearly = lambda age_input: 1.0 - px_val
        mu_val = -math.log(px_val) if px_val > 0 else float('inf')
        mu_func_continuous = lambda age_input, t_offset: mu_val
        px_func_continuous = lambda age_input, period: px_val ** period
        assumption_description = f"p_x konstan = {px_val}"

    elif assumption_type == 'de_moivre':
        if not params or len(params) < 1: raise ValueError("Parameter omega dibutuhkan untuk 'de_moivre'.")
        current_omega = int(params[0])
        if current_omega <= 0: raise ValueError("Omega untuk De Moivre harus integer positif.")
        omega = current_omega
        
        qx_func_yearly = lambda age_input: (1.0 / (omega - age_input)) if age_input < omega and (omega - age_input) != 0 else 1.0
        px_func_yearly = lambda age_input: ((omega - age_input - 1.0) / (omega - age_input)) if age_input < omega - 1 and (omega - age_input) !=0 else 0.0
        mu_func_continuous = lambda age_input, t_offset: (1.0 / (omega - (age_input + t_offset))) if (age_input + t_offset) < omega and (omega - (age_input + t_offset)) != 0 else float('inf')
        
        def px_de_moivre_cont(age_input: int, period: float) -> float:
            if age_input < 0 : raise ValueError("Usia tidak boleh negatif.")
            if period < 0 : raise ValueError("Periode tidak boleh negatif.")
            if age_input >= omega: return 1.0 if period == 0 else 0.0
            if age_input + period >= omega: return 0.0
            return (omega - age_input - period) / (omega - age_input) if (omega - age_input) != 0 else 0.0
        px_func_continuous = px_de_moivre_cont
        assumption_description = f"De Moivre (ω={omega})"
        
    elif assumption_type == 'beta_distribution': 
        if not params or len(params) < 2: raise ValueError("Parameter omega dan alpha dibutuhkan untuk 'beta_distribution'.")
        current_omega, alpha = int(params[0]), params[1]
        if current_omega <= 0: raise ValueError("Omega harus integer positif.")
        if alpha <= 0 : raise ValueError("Alpha harus positif.")
        omega = current_omega

        px_func_yearly = lambda age_input: ((omega - age_input - 1.0) / (omega - age_input))**alpha if age_input < omega - 1 and (omega-age_input)!=0 else 0.0
        qx_func_yearly = lambda age_input: 1.0 - px_func_yearly(age_input)
        
        mu_func_continuous = lambda age_input, t_offset: (alpha / (omega - (age_input + t_offset))) if (age_input + t_offset) < omega and (omega - (age_input + t_offset)) !=0 else float('inf')
        
        def px_beta_cont(age_input: int, period: float) -> float:
            if age_input < 0 : raise ValueError("Usia tidak boleh negatif.")
            if period < 0 : raise ValueError("Periode tidak boleh negatif.")
            if age_input >= omega: return 1.0 if period == 0 else 0.0
            if age_input + period >= omega: return 0.0
            return ((omega - age_input - period) / (omega - age_input))**alpha if (omega-age_input) !=0 else 0.0
        px_func_continuous = px_beta_cont
        assumption_description = f"Beta Dist. (ω={omega}, α={alpha:.2f})" # Format alpha

    elif assumption_type == 'constant_mu_cfm':
        if not params or len(params) < 1: raise ValueError("Parameter mu dibutuhkan untuk 'constant_mu_cfm'.")
        mu = params[0]
        if mu < 0: raise ValueError("Nilai μ untuk 'constant_mu_cfm' harus non-negatif.")
        px_val_yearly = math.exp(-mu)
        qx_val_yearly = 1.0 - px_val_yearly
        qx_func_yearly = lambda age_input: qx_val_yearly
        px_func_yearly = lambda age_input: px_val_yearly
        mu_func_continuous = lambda age_input, t_offset: mu
        px_func_continuous = lambda age_input, period: math.exp(-mu * period)
        assumption_description = f"CFM (μ={mu})"

    elif assumption_type == 'gompertz':
        if not params or len(params) < 2: raise ValueError("Parameter B dan c dibutuhkan untuk 'gompertz'.")
        B_g, c_g = params[0], params[1]
        if c_g <= 0 or (c_g == 1.0 and B_g < 0) or (c_g != 1.0 and B_g <= 0):
            raise ValueError("Parameter B,c Gompertz tidak valid.")
        
        mu_func_continuous = lambda age_input, t_offset: B_g * (c_g ** (age_input + t_offset))
        
        def p_yearly_gompertz(age_input: int) -> float:
            mu_val_at_x = B_g * (c_g ** age_input)
            if abs(c_g - 1.0) < 1e-9 : return math.exp(-mu_val_at_x) # c mendekati 1
            integral_mu = mu_val_at_x * (c_g - 1.0) / math.log(c_g)
            return math.exp(-integral_mu)
        px_func_yearly = p_yearly_gompertz
        qx_func_yearly = lambda age_input: 1.0 - px_func_yearly(age_input)
        
        def px_gompertz_cont(age_input: int, period: float) -> float:
            if period < 0: raise ValueError("Periode tidak boleh negatif.")
            if age_input < 0: raise ValueError("Usia tidak boleh negatif.")
            if abs(c_g - 1.0) < 1e-9 : return math.exp(-B_g * period) # Jika c=1, mu(x+s) = B, _t p_x = exp(-Bt)
            # _t p_x = exp( - integral(B*c^(x+s) ds, s from 0 to t) )
            integral_mu_t = B_g * (c_g**age_input) * (c_g**period - 1.0) / math.log(c_g)
            return math.exp(-integral_mu_t)
        px_func_continuous = px_gompertz_cont
        assumption_description = f"Gompertz (B={B_g:.6g}, c={c_g:.6g})"
        omega = 150 

    elif assumption_type == 'makeham':
        if not params or len(params) < 3: raise ValueError("Parameter A, B, dan c dibutuhkan untuk 'makeham'.")
        A_m, B_m, c_m = params[0], params[1], params[2]
        if c_m <= 0 or (c_m == 1.0 and B_m < 0) or (c_m != 1.0 and B_m <=0) or A_m < 0:
             raise ValueError("Parameter A,B,c Makeham tidak valid.")

        mu_func_continuous = lambda age_input, t_offset: A_m + B_m * (c_m ** (age_input + t_offset))

        def p_yearly_makeham(age_input: int) -> float:
            integral_A = A_m
            integral_Bc_part: float
            if abs(c_m - 1.0) < 1e-9 : integral_Bc_part = B_m
            else:
                mu_g_part = B_m * (c_m**age_input)
                integral_Bc_part = mu_g_part * (c_m - 1.0) / math.log(c_m)
            return math.exp(-(integral_A + integral_Bc_part))
        px_func_yearly = p_yearly_makeham
        qx_func_yearly = lambda age_input: 1.0 - px_func_yearly(age_input)

        def px_makeham_cont(age_input: int, period: float) -> float:
            if period < 0: raise ValueError("Periode tidak boleh negatif.")
            if age_input < 0: raise ValueError("Usia tidak boleh negatif.")
            integral_A_t = A_m * period
            integral_Bc_part_t: float
            if abs(c_m - 1.0) < 1e-9:
                integral_Bc_part_t = B_m * period
            else:
                integral_Bc_part_t = B_m * (c_m**age_input) * (c_m**period - 1.0) / math.log(c_m)
            return math.exp(-(integral_A_t + integral_Bc_part_t))
        px_func_continuous = px_makeham_cont
        assumption_description = f"Makeham (A={A_m:.6g}, B={B_m:.6g}, c={c_m:.6g})"
        omega = 150
    else:
        raise ValueError(f"Tipe asumsi tidak dikenal: {assumption_type}")
    
    return qx_func_yearly, px_func_yearly, omega, assumption_description, mu_func_continuous, px_func_continuous

# --- Fungsi API Publik Berbasis Asumsi ---

def survival_probability_from_assumption(
    age: int,
    period: float, 
    interest_rate: float,
    assumption_type: ASSUMPTION_TYPES_LITERAL,
    params: List[float],
    # assumption_fractional_core: Optional[Literal['udd', 'cfm']] = 'cfm' # Jika ingin kontrol interpolasi di core
) -> ActuarialResult:
    _ , px_func_yearly, omega_calc, assumption_desc_short, _, px_func_cont = \
        _create_assumption_functions(assumption_type, params)
    
    calc = ActuarialCalculator(interest_rate=interest_rate)
    value: float
    
    if assumption_type in ['de_moivre', 'beta_distribution', 'constant_mu_cfm', 'gompertz', 'makeham']:
        value = px_func_cont(age, period)
    elif assumption_type in ['constant_qx', 'constant_px']:
        # Metode di core akan menangani interpolasi fraksional (default CFM)
        value = calc.survival_probability_from_assumption(age, period, px_func_yearly, omega_calc) 
    else: 
        raise NotImplementedError(f"Logika survival untuk {assumption_type} belum diimplementasikan di API.")

    period_str = str(int(period)) if period == int(period) else f"{period:.2f}"
    formula_str = rf"{{}}_{{{period_str}}}p_{{{age}}}"
    description = f"Probabilitas Hidup {period_str} Tahun ({assumption_desc_short}), Usia {age}"
    return ActuarialResult(value, formula_str, description)

def death_probability_from_assumption(
    age: int,
    period: float,
    interest_rate: float,
    assumption_type: ASSUMPTION_TYPES_LITERAL,
    params: List[float]
) -> ActuarialResult:
    survival_result = survival_probability_from_assumption(age, period, interest_rate, assumption_type, params)
    value = 1.0 - survival_result.value
    
    period_str = str(int(period)) if period == int(period) else f"{period:.2f}"
    formula_str = rf"{{}}_{{{period_str}}}q_{{{age}}}"
    
    assumption_desc_from_survival = "asumsi tidak diketahui"
    if "(" in survival_result.description and ")" in survival_result.description:
        assumption_desc_from_survival = survival_result.description.split("(", 1)[1].rsplit(")", 1)[0]
        
    description = f"Probabilitas Kematian {period_str} Tahun ({assumption_desc_from_survival}), Usia {age}"
    return ActuarialResult(value, formula_str, description)

def deferred_death_probability_from_assumption(
    age: int,
    deferral_period: float,
    death_period: float,
    interest_rate: float,
    assumption_type: ASSUMPTION_TYPES_LITERAL,
    params: List[float]
) -> ActuarialResult:
    if deferral_period < 0 or death_period <= 0:
        raise ValueError("Periode penundaan non-negatif & periode kematian positif.")

    # _t p_x
    prob_survive_deferral_result = survival_probability_from_assumption(age, deferral_period, interest_rate, assumption_type, params)
    tpx_value = prob_survive_deferral_result.value
    
    # _u q_{x+t} = 1 - _u p_{x+t}
    # Untuk menghitung _u p_{x+t}, usia awalnya adalah 'age + deferral_period' dan periodenya 'death_period'
    # Kita panggil lagi survival_probability_from_assumption dengan parameter yang disesuaikan
    # Ini akan menggunakan fungsi kontinu yang benar jika asumsinya kontinu.
    
    _ , _ , _ , _ , _ , px_func_cont_for_calc = \
        _create_assumption_functions(assumption_type, params)

    # _u p_{x+t} = px_cont_func(age_awal=(age+deferral_period), periode=death_period)
    # Perlu penyesuaian bagaimana px_cont_func menangani age_awal non-bulat jika ia hanya menerima int.
    # Untuk De Moivre, CFM, Gompertz, Makeham, px_cont_func(age_int, period_float_from_age_int)
    # Kita hitung _uq_{x+t} sebagai _tp_x \cdot (1 - _up_{x+t}) ini salah
    # Kita hitung sebagai _tp_x \cdot _uq_{x+t}
    # di mana _uq_{x+t} = 1 - _up_{x+t}
    
    # Paling mudah tetap pakai _tp_x - _{t+u}p_x untuk konsistensi
    prob_survive_total_period_result = survival_probability_from_assumption(age, deferral_period + death_period, interest_rate, assumption_type, params)
    value = tpx_value - prob_survive_total_period_result.value
    
    deferral_str = str(int(deferral_period)) if deferral_period == int(deferral_period) else f"{deferral_period:.2f}"
    death_period_str = str(int(death_period)) if death_period == int(death_period) else f"{death_period:.2f}"
    
    formula_str = rf"{{}}_{{{deferral_str}|{death_period_str}}}q_{{{age}}}"
    assumption_desc_from_survival = "asumsi tidak diketahui"
    if "(" in prob_survive_deferral_result.description and ")" in prob_survive_deferral_result.description:
        assumption_desc_from_survival = prob_survive_deferral_result.description.split("(", 1)[1].rsplit(")", 1)[0]
    description = f"Probabilitas Kematian Ditunda {deferral_str}|{death_period_str} ({assumption_desc_from_survival}), Usia {age}"
    return ActuarialResult(value, formula_str, description)

def force_of_mortality_at_age_t(
    age: int, 
    t_offset: float, 
    interest_rate: float,
    assumption_type: ASSUMPTION_TYPES_LITERAL,
    params: List[float]
) -> ActuarialResult:
    if t_offset < 0: raise ValueError("t_offset tidak boleh negatif.")
    _ , _ , _ , assumption_desc, mu_func_continuous, _ = _create_assumption_functions(assumption_type, params)
    value = mu_func_continuous(age, t_offset)
    
    age_display = f"{age}"
    if t_offset > 0:
        age_display_val = age + t_offset
        age_display_str_offset = f"{t_offset:.2f}".rstrip('0').rstrip('.')
        age_display += f"+{age_display_str_offset}"
        
    formula_str = rf"\mu_{{{age_display}}}"
    description = f"Force of Mortality ({assumption_desc}), Usia Tepat {age_display}"
    return ActuarialResult(value, formula_str, description)

def pdf_death_at_age_t(
    age: int, 
    t_period: float, 
    interest_rate: float,
    assumption_type: ASSUMPTION_TYPES_LITERAL,
    params: List[float]
) -> ActuarialResult:
    if t_period < 0: raise ValueError("t_period tidak boleh negatif.")
    survival_result = survival_probability_from_assumption(age, t_period, interest_rate, assumption_type, params)
    tpx_value = survival_result.value
    
    fom_result = force_of_mortality_at_age_t(age, t_period, interest_rate, assumption_type, params)
    mu_value_at_time_t = fom_result.value

    value = tpx_value * mu_value_at_time_t
    
    tpx_formula_part = survival_result.formula_latex
    mu_formula_part = fom_result.formula_latex
    
    formula_str = rf"{tpx_formula_part} \cdot {mu_formula_part}"
    
    age_at_death_display_raw = age + t_period
    age_at_death_display = f"{age_at_death_display_raw:.2f}".rstrip('0').rstrip('.') if t_period > 0 else str(age)
    
    assumption_desc_from_survival = "asumsi tidak diketahui"
    if "(" in survival_result.description and ")" in survival_result.description:
        assumption_desc_from_survival = survival_result.description.split("(", 1)[1].rsplit(")", 1)[0]
    description = f"PDF Kematian pada Usia Tepat {age_at_death_display} ({assumption_desc_from_survival})"
    return ActuarialResult(value, formula_str, description)

def nsp_whole_life_from_assumption(
    age: int,
    interest_rate: float,
    assumption_type: ASSUMPTION_TYPES_LITERAL,
    params: List[float]
) -> ActuarialResult:
    calc = ActuarialCalculator(interest_rate=interest_rate)
    qx_func, px_func, omega, assumption_desc, _, _ = _create_assumption_functions(assumption_type, params)
    value = calc.nsp_whole_life_from_assumption(age, qx_func, px_func, omega)
    formula_str = rf"A_{{{age}}}"
    description = f"NSP Whole Life (Asumsi: {assumption_desc}), Usia {age}"
    return ActuarialResult(value, formula_str, description)

def pv_annuity_due_whole_life_from_assumption(
    age: int,
    interest_rate: float,
    assumption_type: ASSUMPTION_TYPES_LITERAL,
    params: List[float]
) -> ActuarialResult:
    calc = ActuarialCalculator(interest_rate=interest_rate)
    _, px_func, omega, assumption_desc, _, _ = _create_assumption_functions(assumption_type, params)
    value = calc.pv_annuity_due_whole_life_from_assumption(age, px_func, omega)
    formula_str = rf"\ddot{{a}}_{{{age}}}"
    description = f"PV Anuitas Whole Life Due (Asumsi: {assumption_desc}), Usia {age}"
    return ActuarialResult(value, formula_str, description)