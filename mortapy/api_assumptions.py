# mortapy/api_assumptions.py
from typing import Literal, Optional, Callable, List
import math
from .core_calculator import ActuarialCalculator
from .result import ActuarialResult

# (DEFAULT values tetap sama)
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
    # (Isi fungsi ini tetap sama seperti versi terakhir yang sudah benar)
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
        
        qx_func_yearly = lambda age_input: (1.0 / (omega - age_input)) if age_input < omega and (omega - age_input) > 0 else 1.0
        px_func_yearly = lambda age_input: ((omega - age_input - 1.0) / (omega - age_input)) if age_input < omega - 1 and (omega - age_input) > 0 else 0.0
        mu_func_continuous = lambda age_input, t_offset: (1.0 / (omega - (age_input + t_offset))) if (age_input + t_offset) < omega and (omega - (age_input + t_offset)) > 0 else float('inf')
        
        def px_de_moivre_cont(age_input: int, period: float) -> float:
            if age_input < 0 : raise ValueError("Usia tidak boleh negatif.")
            if period < 0 : raise ValueError("Periode tidak boleh negatif.")
            if age_input >= omega: return 1.0 if period == 0 else 0.0
            if age_input + period >= omega: return 0.0
            denominator = omega - age_input
            return (omega - age_input - period) / denominator if denominator > 0 else 0.0
        px_func_continuous = px_de_moivre_cont
        assumption_description = f"De Moivre (ω={omega})"
        
    elif assumption_type == 'beta_distribution': 
        if not params or len(params) < 2: raise ValueError("Parameter omega dan alpha dibutuhkan untuk 'beta_distribution'.")
        current_omega, alpha = int(params[0]), params[1]
        if current_omega <= 0: raise ValueError("Omega harus integer positif.")
        if alpha <= 0 : raise ValueError("Alpha harus positif.")
        omega = current_omega

        px_func_yearly = lambda age_input: ((omega - age_input - 1.0) / (omega - age_input))**alpha if age_input < omega - 1 and (omega-age_input)>0 else 0.0
        qx_func_yearly = lambda age_input: 1.0 - px_func_yearly(age_input)
        
        mu_func_continuous = lambda age_input, t_offset: (alpha / (omega - (age_input + t_offset))) if (age_input + t_offset) < omega and (omega - (age_input + t_offset)) > 0 else float('inf')
        
        def px_beta_cont(age_input: int, period: float) -> float:
            if age_input < 0 : raise ValueError("Usia tidak boleh negatif.")
            if period < 0 : raise ValueError("Periode tidak boleh negatif.")
            if age_input >= omega: return 1.0 if period == 0 else 0.0
            if age_input + period >= omega: return 0.0
            denominator = omega - age_input
            return ((omega - age_input - period) / denominator)**alpha if denominator > 0 else 0.0
        px_func_continuous = px_beta_cont
        assumption_description = f"Beta Dist. (ω={omega}, α={alpha:.2f})"

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
        if c_g <= 0 or (abs(c_g - 1.0) < 1e-9 and B_g < 0) or (abs(c_g - 1.0) >= 1e-9 and B_g <= 0):
            raise ValueError("Parameter B,c Gompertz tidak valid.")
        
        mu_func_continuous = lambda age_input, t_offset: B_g * (c_g ** (age_input + t_offset))
        
        def p_yearly_gompertz(age_input: int) -> float:
            mu_val_at_x = B_g * (c_g ** age_input)
            if abs(c_g - 1.0) < 1e-9 : return math.exp(-mu_val_at_x)
            integral_mu = mu_val_at_x * (c_g - 1.0) / math.log(c_g)
            return math.exp(-integral_mu)
        px_func_yearly = p_yearly_gompertz
        qx_func_yearly = lambda age_input: 1.0 - px_func_yearly(age_input)
        
        def px_gompertz_cont(age_input: int, period: float) -> float:
            if period < 0: raise ValueError("Periode tidak boleh negatif.")
            if age_input < 0: raise ValueError("Usia tidak boleh negatif.")
            if abs(c_g - 1.0) < 1e-9 : return math.exp(-B_g * period * (c_g ** age_input))
            integral_mu_t = B_g * (c_g**age_input) * (c_g**period - 1.0) / math.log(c_g)
            return math.exp(-integral_mu_t)
        px_func_continuous = px_gompertz_cont
        assumption_description = f"Gompertz (B={B_g:.6g}, c={c_g:.6g})"
        omega = 150 

    elif assumption_type == 'makeham':
        if not params or len(params) < 3: raise ValueError("Parameter A, B, dan c dibutuhkan untuk 'makeham'.")
        A_m, B_m, c_m = params[0], params[1], params[2]
        if c_m <= 0 or (abs(c_m - 1.0) < 1e-9 and B_m < 0) or (abs(c_m - 1.0) >=1e-9 and B_m <=0) or A_m < 0:
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
    age: int, period: float, interest_rate: float,
    assumption_type: ASSUMPTION_TYPES_LITERAL, params: List[float]
) -> ActuarialResult:
    qx_f_yr, px_f_yr, omg, assumption_desc, mu_f_cont, px_f_cont = _create_assumption_functions(assumption_type, params)
    calc = ActuarialCalculator(interest_rate=interest_rate)
    value: float
    if assumption_type in ['de_moivre', 'beta_distribution', 'constant_mu_cfm', 'gompertz', 'makeham']:
        value = px_f_cont(age, period)
    elif assumption_type in ['constant_qx', 'constant_px']:
        value = calc.survival_probability_from_assumption(age, period, px_f_yr, omg) 
    else: raise NotImplementedError(f"Logika survival untuk {assumption_type} belum ada di API.")
    p_str = str(int(period)) if period == int(period) else f"{period:.2f}"
    f_str = rf"{{}}_{{{p_str}}}p_{{{age}}}"
    desc = f"Probabilitas Hidup {p_str} Tahun ({assumption_desc}), Usia {age}"
    return ActuarialResult(value, f_str, desc)

def death_probability_from_assumption(
    age: int, period: float, interest_rate: float,
    assumption_type: ASSUMPTION_TYPES_LITERAL, params: List[float]
) -> ActuarialResult:
    surv_res = survival_probability_from_assumption(age, period, interest_rate, assumption_type, params)
    val = 1.0 - surv_res.value
    p_str = str(int(period)) if period == int(period) else f"{period:.2f}"
    f_str = rf"{{}}_{{{p_str}}}q_{{{age}}}"
    desc_suffix = surv_res.description.split("(", 1)[1].split(")", 1)[0] if "(" in surv_res.description else "asumsi tidak diketahui"
    desc = f"Probabilitas Kematian {p_str} Tahun ({desc_suffix}), Usia {age}"
    return ActuarialResult(val, f_str, desc)

def deferred_death_probability_from_assumption(
    age: int, deferral_period: float, death_period: float, interest_rate: float,
    assumption_type: ASSUMPTION_TYPES_LITERAL, params: List[float]
) -> ActuarialResult:
    if deferral_period < 0 or death_period <= 0: raise ValueError("Periode tidak valid.")
    
    # Gunakan formula perkalian: _t p_x * _u q_{x+t}
    # _t p_x
    tpx_res = survival_probability_from_assumption(age, deferral_period, interest_rate, assumption_type, params)
    tpx_val = tpx_res.value
    if abs(tpx_val) < 1e-12:
        defer_str_f = str(int(deferral_period)) if deferral_period == int(deferral_period) else f"{deferral_period:.2f}"
        death_p_str_f = str(int(death_period)) if death_period == int(death_period) else f"{death_period:.2f}"
        f_str_f = rf"{{}}_{{{defer_str_f}|{death_p_str_f}}}q_{{{age}}}"
        desc_f = tpx_res.description.replace("Probabilitas Hidup", "Prob. Kematian Ditunda")
        return ActuarialResult(0.0, f_str_f, desc_f)

    # _u q_{x+t}
    # Untuk asumsi kontinu, usia awal bisa float. Untuk diskrit + interpolasi, perlu ditangani.
    # Fungsi death_probability_from_assumption kita menerima usia awal integer.
    # Ini bagian yang rumit jika deferral_period adalah float untuk asumsi constant_qx/px.
    # Kita akan memanggilnya dengan usia bulat terdekat, dan periode yang disesuaikan.
    
    # Pendekatan paling akurat untuk _uq_{x+t} adalah 1 - _up_{x+t}
    # di mana _up_{x+t} = _{t+u}p_x / _tp_x
    
    total_period = deferral_period + death_period
    t_plus_u_px_res = survival_probability_from_assumption(age, total_period, interest_rate, assumption_type, params)
    
    u_px_plus_t_val = t_plus_u_px_res.value / tpx_val if tpx_val > 1e-12 else 0.0
    u_qx_plus_t_val = 1.0 - u_px_plus_t_val
    
    value = tpx_val * u_qx_plus_t_val
    
    deferral_str = str(int(deferral_period)) if deferral_period == int(deferral_period) else f"{deferral_period:.2f}"
    death_period_str = str(int(death_period)) if death_period == int(death_period) else f"{death_period:.2f}"
    formula_str = rf"{{}}_{{{deferral_str}|{death_period_str}}}q_{{{age}}}"
    assumption_desc_from_survival = tpx_res.description.split("(", 1)[1].split(")", 1)[0] if "(" in tpx_res.description else "asumsi tidak diketahui"
    description = f"Probabilitas Kematian Ditunda {deferral_str}|{death_period_str} ({assumption_desc_from_survival}), Usia {age}"
    return ActuarialResult(value, formula_str, description)

def force_of_mortality_at_age_t(
    age: int, t_offset: float, interest_rate: float,
    assumption_type: ASSUMPTION_TYPES_LITERAL, params: List[float]
) -> ActuarialResult:
    if t_offset < 0: raise ValueError("t_offset tidak boleh negatif.")
    _ , _ , _ , assumption_desc, mu_func_continuous, _ = _create_assumption_functions(assumption_type, params)
    value = mu_func_continuous(age, t_offset)
    age_display = f"{age}"
    if t_offset > 0:
        age_display_str_offset = f"{t_offset:.2f}".rstrip('0').rstrip('.')
        age_display += f"+{age_display_str_offset}"
    formula_str = rf"\mu_{{{age_display}}}"
    description = f"Force of Mortality ({assumption_desc}), Usia Tepat {age_display}"
    return ActuarialResult(value, formula_str, description)

def pdf_death_at_age_t(
    age: int, t_period: float, interest_rate: float,
    assumption_type: ASSUMPTION_TYPES_LITERAL, params: List[float]
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
    assumption_desc_from_survival = survival_result.description.split("(", 1)[1].rsplit(")", 1)[0] if "(" in survival_result.description else "asumsi tidak diketahui"
    description = f"PDF Kematian pada Usia Tepat {age_at_death_display} ({assumption_desc_from_survival})"
    return ActuarialResult(value, formula_str, description)

def nsp_whole_life_from_assumption(
    age: int, interest_rate: float,
    assumption_type: ASSUMPTION_TYPES_LITERAL, params: List[float]
) -> ActuarialResult:
    calc = ActuarialCalculator(interest_rate=interest_rate)
    qx_func, px_func, omega, assumption_desc, _, _ = _create_assumption_functions(assumption_type, params)
    value = calc.nsp_whole_life_from_assumption(age, qx_func, px_func, omega)
    formula_str = rf"A_{{{age}}}"
    description = f"NSP Whole Life (Asumsi: {assumption_desc}), Usia {age}"
    return ActuarialResult(value, formula_str, description)

def pv_annuity_due_whole_life_from_assumption(
    age: int, interest_rate: float,
    assumption_type: ASSUMPTION_TYPES_LITERAL, params: List[float]
) -> ActuarialResult:
    calc = ActuarialCalculator(interest_rate=interest_rate)
    _, px_func, omega, assumption_desc, _, _ = _create_assumption_functions(assumption_type, params)
    value = calc.pv_annuity_due_whole_life_from_assumption(age, px_func, omega)
    formula_str = rf"\ddot{{a}}_{{{age}}}"
    description = f"PV Anuitas Whole Life Due (Asumsi: {assumption_desc}), Usia {age}"
    return ActuarialResult(value, formula_str, description)

# --- Fungsi Momen Curtate Berbasis Asumsi ---
def expected_curtate_future_lifetime_from_assumption(
    age: int, interest_rate: float,
    assumption_type: ASSUMPTION_TYPES_LITERAL, params: List[float],
    n_temp: Optional[int] = None
) -> ActuarialResult:
    calc = ActuarialCalculator(interest_rate=interest_rate)
    _ , px_func_yearly, omega, assumption_desc, _, _ = _create_assumption_functions(assumption_type, params)
    value = calc.ex_curtate_from_assumption(age, px_func_yearly, omega, n_temp)
    subscript_content = str(age)
    term_desc = ""
    if n_temp is not None:
        subscript_content += rf":\overline{{{n_temp}}}|"
        term_desc = f"{n_temp}-tahun temporary "
    formula_str = rf"e_{{{subscript_content}}}"
    description = f"Ekspektasi Curtate Future Lifetime {term_desc}(Asumsi: {assumption_desc}), Usia {age}"
    return ActuarialResult(value, formula_str, description)

def second_moment_curtate_future_lifetime_from_assumption(
    age: int, interest_rate: float,
    assumption_type: ASSUMPTION_TYPES_LITERAL, params: List[float],
    n_temp: Optional[int] = None
) -> ActuarialResult:
    calc = ActuarialCalculator(interest_rate=interest_rate)
    _ , px_func_yearly, omega, assumption_desc, _, _ = _create_assumption_functions(assumption_type, params)
    value = calc.e_sq_curtate_from_assumption(age, px_func_yearly, omega, n_temp)
    subscript_content = str(age)
    if n_temp is not None:
        subscript_content += rf":\overline{{{n_temp}}}|"
    formula_str = rf"E[K_{{{subscript_content}}}^2]"
    term_desc = f"{n_temp}-tahun temporary " if n_temp is not None else ""
    description = f"Momen Kedua Curtate Future Lifetime {term_desc}(Asumsi: {assumption_desc}), Usia {age}"
    return ActuarialResult(value, formula_str, description)

def variance_curtate_future_lifetime_from_assumption(
    age: int, interest_rate: float,
    assumption_type: ASSUMPTION_TYPES_LITERAL, params: List[float],
    n_temp: Optional[int] = None
) -> ActuarialResult:
    ex_result = expected_curtate_future_lifetime_from_assumption(age, interest_rate, assumption_type, params, n_temp)
    e_sq_result = second_moment_curtate_future_lifetime_from_assumption(age, interest_rate, assumption_type, params, n_temp)
    value = e_sq_result.value - (ex_result.value ** 2)
    subscript_content = str(age)
    term_desc = ""
    if n_temp is not None:
        subscript_content += rf":\overline{{{n_temp}}}|"
        term_desc = f"{n_temp}-tahun temporary "
    formula_str = rf"Var[K_{{{subscript_content}}}]"
    assumption_desc_from_ex = ex_result.description.split("(",1)[1].split(")",1)[0] if "(" in ex_result.description else "asumsi tidak diketahui"
    description = f"Variansi Curtate Future Lifetime {term_desc}({assumption_desc_from_ex}), Usia {age}"
    return ActuarialResult(value, formula_str, description)


# --- FUNGSI BARU UNTUK MOMEN COMPLETE BERBASIS ASUMSI ---
def expected_complete_future_lifetime_from_assumption(
    age: int,
    interest_rate: float,
    assumption_type: ASSUMPTION_TYPES_LITERAL,
    params: List[float],
    n_temp: Optional[int] = None
) -> ActuarialResult:
    """
    Menghitung ekspektasi complete future lifetime (e_circ_x atau e_circ_{x:n|}) 
    berdasarkan asumsi distribusi murni.
    """
    calc = ActuarialCalculator(interest_rate=interest_rate)
    qx_func_yr, px_func_yr, omega, assumption_desc, mu_func_cont, px_func_cont = \
        _create_assumption_functions(assumption_type, params)
    value: float

    if assumption_type in ['de_moivre', 'beta_distribution', 'constant_mu_cfm', 'gompertz', 'makeham'] and n_temp is None:
        # Whole life - Hitung integral dari _t p_x dt dari 0 hingga omega-x
        # atau gunakan formula closed-form jika ada
        if assumption_type == 'de_moivre': value = (omega - age) / 2.0 if age < omega else 0.0
        elif assumption_type == 'beta_distribution': value = (omega - age) / (params[1] + 1.0) if age < omega else 0.0
        elif assumption_type == 'constant_mu_cfm': value = 1.0 / params[0] if params[0] > 1e-9 else float('inf')
        else: # Gompertz, Makeham - integral numerik atau aproksimasi
            value = calc.ex_complete_from_assumption(age, px_func_yr, qx_func_yr, omega, n_temp, 'udd', px_func_cont) # Aproksimasi UDD
    else: # constant_qx, constant_px, atau kasus temporary
        value = calc.ex_complete_from_assumption(age, px_func_yr, qx_func_yr, omega, n_temp, 'udd', px_func_cont if assumption_type in ['de_moivre', 'beta_distribution', 'constant_mu_cfm', 'gompertz', 'makeham'] else None)

    subscript_content = str(age)
    term_desc = ""
    if n_temp is not None:
        subscript_content += rf":\overline{{{n_temp}}}|"
        term_desc = f"{n_temp}-tahun temporary "
    formula_str = rf"\mathring{{e}}_{{{subscript_content}}}"
    description = f"Ekspektasi Complete Future Lifetime {term_desc}(Asumsi: {assumption_desc}), Usia {age}"
    return ActuarialResult(value, formula_str, description)

def second_moment_complete_future_lifetime_from_assumption(
    age: int,
    interest_rate: float,
    assumption_type: ASSUMPTION_TYPES_LITERAL,
    params: List[float],
    n_temp: Optional[int] = None
) -> ActuarialResult:
    """
    Menghitung E[T_x^2] atau E[(T_{x:n|})^2] berdasarkan asumsi murni.
    """
    calc = ActuarialCalculator(interest_rate=interest_rate)
    qx_func_yr, px_func_yr, omega, assumption_desc, mu_func_cont, px_func_cont = \
        _create_assumption_functions(assumption_type, params)
    value: float

    if assumption_type in ['de_moivre', 'beta_distribution', 'constant_mu_cfm'] and n_temp is None:
        if assumption_type == 'de_moivre': value = ((omega - age)**2) / 3.0 if age < omega else 0.0
        elif assumption_type == 'beta_distribution':
            omega_val, alpha_val = params[0], params[1] # type: ignore
            value = 2 * ((omega_val - age)**2) / ((alpha_val + 1.0)*(alpha_val + 2.0)) if age < omega_val else 0.0
        elif assumption_type == 'constant_mu_cfm':
            mu_val = params[0]
            value = 2.0 / (mu_val**2) if mu_val > 1e-9 else float('inf')
        else: # Fallback untuk Gompertz, Makeham (integral rumit)
            value = calc.e_sq_complete_from_assumption(age, px_func_yr, qx_func_yr, omega, n_temp, 'udd', px_func_cont)
    else: # constant_qx, constant_px, atau kasus temporary
        value = calc.e_sq_complete_from_assumption(age, px_func_yr, qx_func_yr, omega, n_temp, 'udd', px_func_cont if assumption_type in ['de_moivre', 'beta_distribution', 'constant_mu_cfm', 'gompertz', 'makeham'] else None)

    subscript_content = str(age)
    term_desc = ""
    if n_temp is not None:
        subscript_content += rf":\overline{{{n_temp}}}|"
        term_desc = f"{n_temp}-tahun temporary "
    formula_str = rf"E[T_{{{subscript_content}}}^2]"
    description = f"Momen Kedua Complete Future Lifetime {term_desc}(Asumsi: {assumption_desc}), Usia {age}"
    return ActuarialResult(value, formula_str, description)

def variance_complete_future_lifetime_from_assumption(
    age: int,
    interest_rate: float,
    assumption_type: ASSUMPTION_TYPES_LITERAL,
    params: List[float],
    n_temp: Optional[int] = None
) -> ActuarialResult:
    """
    Menghitung Var(T_x) atau Var(T_{x:n|}) berdasarkan asumsi murni.
    Var(T) = E[T^2] - (E[T])^2.
    """
    ex_circ_result = expected_complete_future_lifetime_from_assumption(age, interest_rate, assumption_type, params, n_temp)
    e_sq_circ_result = second_moment_complete_future_lifetime_from_assumption(age, interest_rate, assumption_type, params, n_temp)
    value = e_sq_circ_result.value - (ex_circ_result.value ** 2)
    
    subscript_content = str(age)
    term_desc = ""
    assumption_desc_from_ex = ex_circ_result.description.split("(",1)[1].split(")",1)[0] if "(" in ex_circ_result.description else "asumsi tidak diketahui"
    if n_temp is not None:
        subscript_content += rf":\overline{{{n_temp}}}|"
        term_desc = f"{n_temp}-tahun temporary "
    formula_str = rf"Var[T_{{{subscript_content}}}]"
    description = f"Variansi Complete Future Lifetime {term_desc}({assumption_desc_from_ex}), Usia {age}"
    return ActuarialResult(value, formula_str, description)