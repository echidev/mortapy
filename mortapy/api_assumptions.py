# mortapy/api_assumptions.py
from typing import Literal, Optional, Callable, List
import math
from .core_calculator import ActuarialCalculator
from .result import ActuarialResult

# Default values for assumptions if not provided by the user
DEFAULT_OMEGA_DEMOIVRE: int = 110
DEFAULT_MU_CFM: float = 0.02
DEFAULT_QX_CONSTANT: float = 0.01
DEFAULT_PX_CONSTANT: float = 0.98
DEFAULT_GOMPERTZ_B: float = 0.00005
DEFAULT_GOMPERTZ_C: float = 1.09
DEFAULT_MAKEHAM_A: float = 0.00022
DEFAULT_MAKEHAM_B: float = 0.000027
DEFAULT_MAKEHAM_C: float = 1.075


def _create_assumption_functions(
    assumption_type: Literal[
        'constant_qx', 'constant_px',
        'de_moivre', 'constant_mu_cfm',
        'gompertz', 'makeham'
    ],
    params: List[float]
) -> tuple[Callable[[int], float], Callable[[int], float], int, str, Callable[[int, float], float]]:
    """
    Membuat fungsi qx_func (tahunan), px_func (tahunan), omega, deskripsi,
    dan mu_func_continuous (mu_{age+t_offset}).
    """
    qx_func: Callable[[int], float]
    px_func: Callable[[int], float]
    mu_func_continuous: Callable[[int, float], float]
    omega: int = 150
    assumption_description: str = ""

    if assumption_type == 'constant_qx':
        if not params or len(params) < 1: raise ValueError("Parameter qx_value dibutuhkan untuk 'constant_qx'.")
        qx_val = params[0]
        if not (0 <= qx_val <= 1): raise ValueError("Nilai q_x untuk 'constant_qx' harus antara 0 dan 1.")
        qx_func = lambda age_input: qx_val
        px_func = lambda age_input: 1.0 - qx_val
        mu_val_const_qx = -math.log(1.0 - qx_val) if qx_val < 1.0 else float('inf')
        mu_func_continuous = lambda age_input, t_offset: mu_val_const_qx
        assumption_description = f"q_x konstan = {qx_val}"

    elif assumption_type == 'constant_px':
        if not params or len(params) < 1: raise ValueError("Parameter px_value dibutuhkan untuk 'constant_px'.")
        px_val = params[0]
        if not (0 <= px_val <= 1): raise ValueError("Nilai p_x untuk 'constant_px' harus antara 0 dan 1.")
        px_func = lambda age_input: px_val
        qx_func = lambda age_input: 1.0 - px_val
        mu_val_const_px = -math.log(px_val) if px_val > 0 else float('inf')
        mu_func_continuous = lambda age_input, t_offset: mu_val_const_px
        assumption_description = f"p_x konstan = {px_val}"

    elif assumption_type == 'de_moivre':
        if not params or len(params) < 1: raise ValueError("Parameter omega dibutuhkan untuk 'de_moivre'.")
        current_omega = int(params[0])
        if current_omega <= 0: raise ValueError("Omega untuk De Moivre harus integer positif.")
        omega = current_omega

        qx_func = lambda age_input: (1.0 / (omega - age_input)) if age_input < omega and (omega - age_input) != 0 else 1.0
        px_func = lambda age_input: ((omega - age_input - 1.0) / (omega - age_input)) if age_input < omega - 1 and (omega - age_input) !=0 else 0.0
        mu_func_continuous = lambda age_input, t_offset: (1.0 / (omega - (age_input + t_offset))) if (age_input + t_offset) < omega and (omega - (age_input + t_offset)) != 0 else float('inf')
        assumption_description = f"De Moivre (ω={omega})"

    elif assumption_type == 'constant_mu_cfm':
        if not params or len(params) < 1: raise ValueError("Parameter mu dibutuhkan untuk 'constant_mu_cfm'.")
        mu = params[0]
        if mu < 0: raise ValueError("Nilai μ untuk 'constant_mu_cfm' harus non-negatif.")
        px_val_yearly = math.exp(-mu)
        qx_val_yearly = 1.0 - px_val_yearly
        qx_func = lambda age_input: qx_val_yearly
        px_func = lambda age_input: px_val_yearly
        mu_func_continuous = lambda age_input, t_offset: mu
        assumption_description = f"CFM (μ={mu})"

    elif assumption_type == 'gompertz':
        if not params or len(params) < 2: raise ValueError("Parameter B dan c dibutuhkan untuk 'gompertz'.")
        B_gompertz, c_gompertz = params[0], params[1]
        if c_gompertz <= 0 or (c_gompertz == 1.0 and B_gompertz < 0) or (c_gompertz != 1.0 and B_gompertz <= 0):
            raise ValueError("Parameter B dan c untuk Gompertz tidak valid (B>0, c>0). Jika c=1, B harus non-negatif.")

        def mu_gompertz_cont(age_input: int, t_offset: float) -> float:
            return B_gompertz * (c_gompertz ** (age_input + t_offset))
        mu_func_continuous = mu_gompertz_cont

        def p_yearly_gompertz(age_input: int) -> float:
            mu_val_at_x = B_gompertz * (c_gompertz ** age_input)
            if c_gompertz == 1.0: return math.exp(-mu_val_at_x)
            integral_mu = mu_val_at_x * (c_gompertz - 1.0) / math.log(c_gompertz)
            return math.exp(-integral_mu)
        px_func = p_yearly_gompertz
        qx_func = lambda age_input: 1.0 - px_func(age_input)
        assumption_description = f"Gompertz (B={B_gompertz:.6g}, c={c_gompertz:.6g})"
        omega = 150

    elif assumption_type == 'makeham':
        if not params or len(params) < 3: raise ValueError("Parameter A, B, dan c dibutuhkan untuk 'makeham'.")
        A_makeham, B_makeham, c_makeham = params[0], params[1], params[2]
        if c_makeham <= 0 or (c_makeham == 1.0 and B_makeham < 0) or (c_makeham != 1.0 and B_makeham <=0) or A_makeham < 0:
             raise ValueError("Parameter A, B, c untuk Makeham tidak valid (A>=0, B>0, c>0 atau jika c=1, B>=0).")

        def mu_makeham_cont(age_input: int, t_offset: float) -> float:
            return A_makeham + B_makeham * (c_makeham ** (age_input + t_offset))
        mu_func_continuous = mu_makeham_cont

        def p_yearly_makeham(age_input: int) -> float:
            integral_A = A_makeham
            integral_Bc_part: float
            if c_makeham == 1.0: integral_Bc_part = B_makeham
            else:
                mu_g_part = B_makeham * (c_makeham**age_input)
                integral_Bc_part = mu_g_part * (c_makeham - 1.0) / math.log(c_makeham)
            return math.exp(-(integral_A + integral_Bc_part))
        px_func = p_yearly_makeham
        qx_func = lambda age_input: 1.0 - px_func(age_input)
        assumption_description = f"Makeham (A={A_makeham:.6g}, B={B_makeham:.6g}, c={c_makeham:.6g})"
        omega = 150
    else:
        raise ValueError(f"Tipe asumsi tidak dikenal: {assumption_type}")

    return qx_func, px_func, omega, assumption_description, mu_func_continuous


def nsp_whole_life_from_assumption( # <--- NAMA FUNGSI INI
    age: int,
    interest_rate: float,
    assumption_type: Literal['constant_qx', 'constant_px', 'de_moivre', 'constant_mu_cfm', 'gompertz', 'makeham'],
    params: List[float]
) -> ActuarialResult:
    """
    Menghitung Premi Tunggal Bersih (A_x) untuk asuransi jiwa seumur hidup
    berdasarkan asumsi distribusi murni.
    """
    calc = ActuarialCalculator(interest_rate=interest_rate)
    qx_func, px_func, omega, assumption_desc, _ = _create_assumption_functions(assumption_type, params) # mu_func_continuous tidak dipakai di sini

    value = calc.nsp_whole_life_from_assumption(age, qx_func, px_func, omega)

    formula_str = rf"A_{{{age}}}"
    description = f"NSP Whole Life (Asumsi: {assumption_desc}), Usia {age}"

    return ActuarialResult(value, formula_str, description)

def pv_annuity_due_whole_life_from_assumption( # <--- NAMA FUNGSI INI
    age: int,
    interest_rate: float,
    assumption_type: Literal['constant_qx', 'constant_px', 'de_moivre', 'constant_mu_cfm', 'gompertz', 'makeham'],
    params: List[float]
) -> ActuarialResult:
    """
    Menghitung nilai sekarang dari anuitas jiwa seumur hidup awal tahun (ä_x)
    berdasarkan asumsi distribusi murni.
    """
    calc = ActuarialCalculator(interest_rate=interest_rate)
    _ , px_func, omega, assumption_desc, _ = _create_assumption_functions(assumption_type, params) # qx_func & mu_func tidak dipakai

    value = calc.pv_annuity_due_whole_life_from_assumption(age, px_func, omega)

    formula_str = rf"\ddot{{a}}_{{{age}}}"
    description = f"PV Anuitas Whole Life Due (Asumsi: {assumption_desc}), Usia {age}"

    return ActuarialResult(value, formula_str, description)

def survival_probability_from_assumption( # <--- NAMA FUNGSI INI
    age: int,
    period: float,
    interest_rate: float,
    assumption_type: Literal['constant_qx', 'constant_px', 'de_moivre', 'constant_mu_cfm', 'gompertz', 'makeham'],
    params: List[float]
) -> ActuarialResult:
    """
    Menghitung probabilitas hidup _{n}p_{x} untuk periode (bisa non-bulat) n
    berdasarkan asumsi distribusi murni.
    """
    value: float = 0.0
    assumption_description_suffix: str = ""
    _ , px_func_yearly, omega_calc, assumption_desc_short, _ = _create_assumption_functions(assumption_type, params)


    if assumption_type == 'de_moivre':
        current_omega = int(params[0])
        if age < 0: raise ValueError("Usia tidak boleh negatif.")
        if current_omega <= 0: raise ValueError("Omega harus positif.")
        if period < 0: raise ValueError("Periode tidak boleh negatif.")
        if age >= current_omega: value = 1.0 if period == 0 else 0.0
        elif age + period >= current_omega: value = 0.0
        else: value = (current_omega - age - period) / (current_omega - age) if (current_omega - age) != 0 else 0.0
        assumption_description_suffix = assumption_desc_short

    elif assumption_type == 'constant_mu_cfm':
        mu = params[0]
        if period < 0: raise ValueError("Periode tidak boleh negatif.")
        value = math.exp(-mu * period)
        assumption_description_suffix = assumption_desc_short

    elif assumption_type == 'gompertz':
        B_g, c_g = params[0], params[1]
        if period < 0: raise ValueError("Periode tidak boleh negatif.")
        if c_g == 1.0:
            value = math.exp(-B_g * period)
        else:
            integral_mu_t = B_g * (c_g**age) * (c_g**period - 1.0) / math.log(c_g)
            value = math.exp(-integral_mu_t)
        assumption_description_suffix = assumption_desc_short

    elif assumption_type == 'makeham':
        A_m, B_m, c_m = params[0], params[1], params[2]
        if period < 0: raise ValueError("Periode tidak boleh negatif.")
        integral_A_t = A_m * period
        integral_Bc_part_t: float
        if c_m == 1.0:
            integral_Bc_part_t = B_m * period
        else:
            integral_Bc_part_t = B_m * (c_m**age) * (c_m**period - 1.0) / math.log(c_m)
        value = math.exp(-(integral_A_t + integral_Bc_part_t))
        assumption_description_suffix = assumption_desc_short

    elif assumption_type in ['constant_qx', 'constant_px']:
        calc = ActuarialCalculator(interest_rate=interest_rate)
        value = calc.survival_probability_from_assumption(age, period, px_func_yearly, omega_calc)
        assumption_description_suffix = assumption_desc_short
    else:
        raise ValueError(f"Tipe asumsi tidak dikenal untuk survival probability: {assumption_type}")

    period_str = str(int(period)) if period == int(period) else f"{period:.2f}"
    formula_str = rf"{{}}_{{{period_str}}}p_{{{age}}}"
    description = f"Probabilitas Hidup {period_str} Tahun ({assumption_description_suffix}), Usia {age}"
    return ActuarialResult(value, formula_str, description)


def death_probability_from_assumption( # <--- NAMA FUNGSI INI
    age: int,
    period: float,
    interest_rate: float,
    assumption_type: Literal['constant_qx', 'constant_px', 'de_moivre', 'constant_mu_cfm', 'gompertz', 'makeham'],
    params: List[float]
) -> ActuarialResult:
    """Menghitung _{period}q_{age} berdasarkan asumsi."""
    survival_result = survival_probability_from_assumption(age, period, interest_rate, assumption_type, params)
    value = 1.0 - survival_result.value

    period_str = str(int(period)) if period == int(period) else f"{period:.2f}"
    formula_str = rf"{{}}_{{{period_str}}}q_{{{age}}}"
    # Mengambil bagian deskripsi asumsi dari hasil survival
    base_description_assumption = "Asumsi tidak diketahui"
    if "(" in survival_result.description and ")" in survival_result.description:
        base_description_assumption = survival_result.description.split("(")[1].split(")")[0]
    description = f"Probabilitas Kematian {period_str} Tahun ({base_description_assumption}), Usia {age}"
    return ActuarialResult(value, formula_str, description)

def deferred_death_probability_from_assumption( # <--- NAMA FUNGSI INI
    age: int,
    deferral_period: float,
    death_period: float,
    interest_rate: float,
    assumption_type: Literal['constant_qx', 'constant_px', 'de_moivre', 'constant_mu_cfm', 'gompertz', 'makeham'],
    params: List[float]
) -> ActuarialResult:
    """Menghitung _{deferral}|{death_period} q_x berdasarkan asumsi."""
    if deferral_period < 0 or death_period <= 0:
        raise ValueError("Periode penundaan harus non-negatif dan periode kematian harus positif.")

    prob_survive_deferral_result = survival_probability_from_assumption(age, deferral_period, interest_rate, assumption_type, params)
    prob_survive_total_period_result = survival_probability_from_assumption(age, deferral_period + death_period, interest_rate, assumption_type, params)

    value = prob_survive_deferral_result.value - prob_survive_total_period_result.value

    deferral_str = str(int(deferral_period)) if deferral_period == int(deferral_period) else f"{deferral_period:.2f}"
    death_period_str = str(int(death_period)) if death_period == int(death_period) else f"{death_period:.2f}"

    formula_str = rf"{{}}_{{{deferral_str}|{death_period_str}}}q_{{{age}}}"
    base_description_assumption = "Asumsi tidak diketahui"
    if "(" in prob_survive_deferral_result.description and ")" in prob_survive_deferral_result.description:
        base_description_assumption = prob_survive_deferral_result.description.split("(")[1].split(")")[0]
    description = f"Probabilitas Kematian Ditunda {deferral_str}|{death_period_str} ({base_description_assumption}), Usia {age}"
    return ActuarialResult(value, formula_str, description)

def force_of_mortality_at_age_t( # <--- NAMA FUNGSI INI
    age: int,
    t_offset: float,
    interest_rate: float,
    assumption_type: Literal['constant_qx', 'constant_px', 'de_moivre', 'constant_mu_cfm', 'gompertz', 'makeham'],
    params: List[float]
) -> ActuarialResult:
    """Menghitung μ_{age+t_offset} berdasarkan asumsi distribusi murni."""
    if t_offset < 0:
        raise ValueError("t_offset tidak boleh negatif.")

    _ , _ , _ , assumption_desc, mu_func_continuous = _create_assumption_functions(assumption_type, params)

    value = mu_func_continuous(age, t_offset)

    age_display = f"{age}"
    if t_offset > 0:
        age_display += f"+{t_offset:.2f}".rstrip('0').rstrip('.')

    formula_str = rf"\mu_{{{age_display}}}"
    description = f"Force of Mortality ({assumption_desc}), Usia Tepat {age_display}"
    return ActuarialResult(value, formula_str, description)

def pdf_death_at_age_t( # <--- NAMA FUNGSI INI
    age: int,
    t_period: float,
    interest_rate: float,
    assumption_type: Literal['constant_qx', 'constant_px', 'de_moivre', 'constant_mu_cfm', 'gompertz', 'makeham'],
    params: List[float]
) -> ActuarialResult:
    """Menghitung PDF kematian f_X(age+t_period) = _{t_period}p_{age} * μ_{age+t_period}."""
    if t_period < 0:
        raise ValueError("t_period tidak boleh negatif untuk PDF kematian.")

    survival_result = survival_probability_from_assumption(age, t_period, interest_rate, assumption_type, params)
    tpx_value = survival_result.value

    fom_result = force_of_mortality_at_age_t(age, t_period, interest_rate, assumption_type, params)
    mu_value_at_time_t = fom_result.value

    value = tpx_value * mu_value_at_time_t

    period_str = str(int(t_period)) if t_period == int(t_period) else f"{t_period:.2f}"
    age_at_death_display = f"{age}"
    if t_period > 0:
        age_at_death_display += f"+{period_str}".rstrip('0').rstrip('.')

    tpx_formula_part = survival_result.formula_latex
    mu_formula_part = fom_result.formula_latex

    formula_str = rf"{tpx_formula_part} \cdot {mu_formula_part}"
    base_description_assumption = "Asumsi tidak diketahui"
    if "(" in survival_result.description and ")" in survival_result.description:
        base_description_assumption = survival_result.description.split("(")[1].split(")")[0]
    description = f"PDF Kematian pada Usia Tepat {age_at_death_display} ({base_description_assumption})"
    return ActuarialResult(value, formula_str, description)