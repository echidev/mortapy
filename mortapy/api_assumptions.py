# mortapy/api_assumptions.py
from typing import Literal, Optional, Callable, List
import math
from .core_calculator import ActuarialCalculator
from .result import ActuarialResult

# Default values
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
    omega: int = 150 # Default omega tinggi, akan di-override oleh De Moivre/Beta
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
                integral_Bc_part_t = B_m * period # * (c_m ** age_input) tidak ada jika c=1
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
    params: List[float]
) -> ActuarialResult:
    """
    Menghitung probabilitas hidup _{period}p_{age} berdasarkan asumsi distribusi murni.
    """
    _ , px_func_yearly, omega_calc, assumption_desc_short, _, px_func_cont = \
        _create_assumption_functions(assumption_type, params)
    
    calc = ActuarialCalculator(interest_rate=interest_rate)
    value: float
    
    if assumption_type in ['de_moivre', 'beta_distribution', 'constant_mu_cfm', 'gompertz', 'makeham']:
        value = px_func_cont(age, period)
    elif assumption_type in ['constant_qx', 'constant_px']:
        value = calc.survival_probability_from_assumption(age, period, px_func_yearly, omega_calc) 
    else: 
        raise NotImplementedError(f"Logika survival untuk {assumption_type} belum ada di API.")

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
    """Menghitung _{period}q_{age} berdasarkan asumsi."""
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
    """Menghitung _{deferral}|{death_period} q_x berdasarkan asumsi (formula perkalian)."""
    if deferral_period < 0 or death_period <= 0:
        raise ValueError("Periode penundaan non-negatif & periode kematian positif.")

    # _t p_x
    prob_survive_deferral_result = survival_probability_from_assumption(age, deferral_period, interest_rate, assumption_type, params)
    tpx_value = prob_survive_deferral_result.value
    if abs(tpx_value) < 1e-12: 
        # Buat string formula yang sesuai
        deferral_str_f = str(int(deferral_period)) if deferral_period == int(deferral_period) else f"{deferral_period:.2f}"
        death_period_str_f = str(int(death_period)) if death_period == int(death_period) else f"{death_period:.2f}"
        formula_str_f = rf"{{}}_{{{deferral_str_f}|{death_period_str_f}}}q_{{{age}}}"
        desc_f = prob_survive_deferral_result.description.replace("Probabilitas Hidup", "Prob. Kematian Ditunda")
        return ActuarialResult(0.0, formula_str_f, desc_f)

    # _u q_{x+t}
    # Untuk menghitung _u q_{x+t}, usia awal adalah age + deferral_period, periode adalah death_period
    # Kita panggil death_probability_from_assumption dengan parameter yang disesuaikan.
    # Perlu px_func_cont untuk menangani usia awal non-bulat (age_after_deferral) dengan benar.
    # Atau, jika px_func_cont tidak dipakai, death_probability akan menggunakan px_func_yearly
    # dan ActuarialCalculator akan melakukan interpolasi fraksional.
    
    # Pendekatan yang lebih bersih: _t p_x * (1 - _u p_{x+t})
    # di mana _u p_{x+t} = _(t+u)p_x / _t p_x
    
    prob_survive_total_period_result = survival_probability_from_assumption(age, deferral_period + death_period, interest_rate, assumption_type, params)
    u_px_plus_t = prob_survive_total_period_result.value / tpx_value if tpx_value > 1e-12 else 0.0
    prob_die_within_n_after_deferral_val = 1.0 - u_px_plus_t
    
    value = tpx_value * prob_die_within_n_after_deferral_val
    
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
    interest_rate: float, # Tidak dipakai langsung, untuk konsistensi
    assumption_type: ASSUMPTION_TYPES_LITERAL,
    params: List[float]
) -> ActuarialResult:
    """Menghitung μ_{age+t_offset} berdasarkan asumsi distribusi murni."""
    if t_offset < 0: raise ValueError("t_offset tidak boleh negatif.")
    _ , _ , _ , assumption_desc, mu_func_continuous, _ = _create_assumption_functions(assumption_type, params)
    value = mu_func_continuous(age, t_offset)
    
    age_display = f"{age}"
    if t_offset > 0:
        # age_display_val = age + t_offset # Tidak perlu ini lagi
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
    """Menghitung PDF kematian f_X(age+t_period) = _{t_period}p_{age} * μ_{age+t_period}."""
    if t_period < 0: raise ValueError("t_period tidak boleh negatif.")
    survival_result = survival_probability_from_assumption(age, t_period, interest_rate, assumption_type, params)
    tpx_value = survival_result.value
    
    # Untuk mu_{age+t_period}, usia bulat awalnya adalah 'age', dan offsetnya adalah 't_period'
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
    """Menghitung A_x dari asumsi."""
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
    """Menghitung ä_x dari asumsi."""
    calc = ActuarialCalculator(interest_rate=interest_rate)
    _, px_func, omega, assumption_desc, _, _ = _create_assumption_functions(assumption_type, params)
    value = calc.pv_annuity_due_whole_life_from_assumption(age, px_func, omega)
    formula_str = rf"\ddot{{a}}_{{{age}}}"
    description = f"PV Anuitas Whole Life Due (Asumsi: {assumption_desc}), Usia {age}"
    return ActuarialResult(value, formula_str, description)


# --- FUNGSI BARU UNTUK MOMEN CURTATE BERBASIS ASUMSI ---
def expected_curtate_future_lifetime_from_assumption(
    age: int,
    interest_rate: float, # Untuk konsistensi ActuarialCalculator
    assumption_type: ASSUMPTION_TYPES_LITERAL,
    params: List[float],
    n_temp: Optional[int] = None 
) -> ActuarialResult:
    """
    Menghitung ekspektasi curtate future lifetime (e_x atau e_{x:n|}) 
    berdasarkan asumsi distribusi murni.
    """
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
    age: int,
    interest_rate: float,
    assumption_type: ASSUMPTION_TYPES_LITERAL,
    params: List[float],
    n_temp: Optional[int] = None
) -> ActuarialResult:
    """
    Menghitung momen kedua dari curtate future lifetime (E[K_x^2] atau E[(K_{x:n|})^2])
    berdasarkan asumsi distribusi murni.
    """
    calc = ActuarialCalculator(interest_rate=interest_rate)
    _ , px_func_yearly, omega, assumption_desc, _, _ = _create_assumption_functions(assumption_type, params)

    value = calc.e_sq_curtate_from_assumption(age, px_func_yearly, omega, n_temp)
    
    subscript_content = str(age)
    symbol_K = "K"
    term_desc = ""
    if n_temp is not None:
        subscript_content += rf":\overline{{{n_temp}}}|"
        term_desc = f"{n_temp}-tahun temporary "
    
    formula_str = rf"E[K_{{{subscript_content}}}^2]" # Sederhanakan simbol untuk E[K^2]
    
    description = f"Momen Kedua Curtate Future Lifetime {term_desc}(Asumsi: {assumption_desc}), Usia {age}"
    return ActuarialResult(value, formula_str, description)

def variance_curtate_future_lifetime_from_assumption(
    age: int,
    interest_rate: float,
    assumption_type: ASSUMPTION_TYPES_LITERAL,
    params: List[float],
    n_temp: Optional[int] = None
) -> ActuarialResult:
    """
    Menghitung variansi dari curtate future lifetime (Var(K_x) atau Var(K_{x:n|}))
    berdasarkan asumsi distribusi murni. Var(K) = E[K^2] - (E[K])^2.
    """
    # Tidak perlu membuat instance calc baru, karena ex dan e_sq sudah API level
    ex_result = expected_curtate_future_lifetime_from_assumption(
        age, interest_rate, assumption_type, params, n_temp
    )
    e_sq_result = second_moment_curtate_future_lifetime_from_assumption(
        age, interest_rate, assumption_type, params, n_temp
    )
    
    value = e_sq_result.value - (ex_result.value ** 2)
    
    subscript_content = str(age)
    term_desc = ""
    assumption_desc_from_ex = ex_result.description.split("(",1)[1].split(")",1)[0] if "(" in ex_result.description else "Asumsi tidak diketahui"


    if n_temp is not None:
        subscript_content += rf":\overline{{{n_temp}}}|"
        term_desc = f"{n_temp}-tahun temporary "
        
    formula_str = rf"Var[K_{{{subscript_content}}}]"
    description = f"Variansi Curtate Future Lifetime {term_desc}({assumption_desc_from_ex}), Usia {age}"
    return ActuarialResult(value, formula_str, description)