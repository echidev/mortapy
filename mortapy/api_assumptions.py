# mortapy/api_assumptions.py
from typing import Literal, Optional, Callable, List # Pastikan List diimpor
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
) -> tuple[Callable[[int], float], Callable[[int], float], int, str]:
    """
    Membuat fungsi qx_func, px_func, omega (usia maksimum), dan deskripsi asumsi
    berdasarkan tipe asumsi dan parameter yang diberikan.
    """
    qx_func: Callable[[int], float]
    px_func: Callable[[int], float]
    omega: int = 150 
    assumption_description: str = ""

    if assumption_type == 'constant_qx':
        if not params or len(params) < 1:
            raise ValueError("Parameter qx_value dibutuhkan untuk 'constant_qx'.")
        qx_val = params[0]
        if not (0 <= qx_val <= 1):
            raise ValueError("Nilai q_x untuk 'constant_qx' harus antara 0 dan 1.")
        qx_func = lambda age_input: qx_val
        px_func = lambda age_input: 1.0 - qx_val
        assumption_description = f"q_x konstan = {qx_val}"
    
    elif assumption_type == 'constant_px':
        if not params or len(params) < 1:
            raise ValueError("Parameter px_value dibutuhkan untuk 'constant_px'.")
        px_val = params[0]
        if not (0 <= px_val <= 1):
            raise ValueError("Nilai p_x untuk 'constant_px' harus antara 0 dan 1.")
        px_func = lambda age_input: px_val
        qx_func = lambda age_input: 1.0 - px_val
        assumption_description = f"p_x konstan = {px_val}"

    elif assumption_type == 'de_moivre':
        if not params or len(params) < 1:
            raise ValueError("Parameter omega dibutuhkan untuk 'de_moivre'.")
        current_omega = int(params[0])
        if current_omega <= 0:
            raise ValueError("Omega untuk De Moivre harus integer positif.")
        omega = current_omega
        
        def qx_de_moivre(age_input: int) -> float:
            if age_input < omega:
                denominator = omega - age_input
                return 1.0 / denominator if denominator > 0 else 1.0
            return 1.0 
        
        def px_de_moivre(age_input: int) -> float:
            if age_input < omega - 1 : 
                 denominator = omega - age_input
                 return (omega - age_input - 1.0) / denominator if denominator > 0 else 0.0
            return 0.0 
            
        qx_func = qx_de_moivre
        px_func = px_de_moivre
        assumption_description = f"De Moivre (ω={omega})"
        
    elif assumption_type == 'constant_mu_cfm':
        if not params or len(params) < 1:
            raise ValueError("Parameter mu dibutuhkan untuk 'constant_mu_cfm'.")
        mu = params[0]
        if mu < 0:
            raise ValueError("Nilai μ untuk 'constant_mu_cfm' harus non-negatif.")
        px_val_yearly = math.exp(-mu)
        qx_val_yearly = 1.0 - px_val_yearly
        qx_func = lambda age_input: qx_val_yearly
        px_func = lambda age_input: px_val_yearly
        assumption_description = f"CFM (μ={mu})"

    elif assumption_type == 'gompertz':
        if not params or len(params) < 2:
            raise ValueError("Parameter B dan c dibutuhkan untuk 'gompertz'.")
        B_gompertz, c_gompertz = params[0], params[1]
        if c_gompertz <= 0 or (c_gompertz == 1.0 and B_gompertz < 0) or (c_gompertz != 1.0 and B_gompertz <= 0):
            raise ValueError("Parameter B dan c untuk Gompertz tidak valid (B>0, c>0). Jika c=1, B harus non-negatif.")

        def mu_x_gompertz(age_input: int) -> float:
            return B_gompertz * (c_gompertz ** age_input)

        def p_yearly_gompertz(age_input: int) -> float:
            mu_val_at_x = mu_x_gompertz(age_input)
            if c_gompertz == 1.0:
                return math.exp(-mu_val_at_x)
            else:
                integral_mu = mu_val_at_x * (c_gompertz - 1.0) / math.log(c_gompertz)
                return math.exp(-integral_mu)
        
        px_func = p_yearly_gompertz
        qx_func = lambda age_input: 1.0 - px_func(age_input)
        assumption_description = f"Gompertz (B={B_gompertz:.6g}, c={c_gompertz:.6g})"
        omega = 150 

    elif assumption_type == 'makeham':
        if not params or len(params) < 3:
            raise ValueError("Parameter A, B, dan c dibutuhkan untuk 'makeham'.")
        A_makeham, B_makeham, c_makeham = params[0], params[1], params[2]
        if c_makeham <= 0 or (c_makeham == 1.0 and B_makeham < 0) or (c_makeham != 1.0 and B_makeham <=0) or A_makeham < 0:
             raise ValueError("Parameter A, B, c untuk Makeham tidak valid (A>=0, B>0, c>0 atau jika c=1, B>=0).")

        def mu_x_makeham(age_input: int) -> float:
            return A_makeham + B_makeham * (c_makeham ** age_input)

        def p_yearly_makeham(age_input: int) -> float:
            integral_A = A_makeham
            integral_Bc_part: float
            if c_makeham == 1.0: 
                integral_Bc_part = B_makeham
            else:
                # mu_gompertz_part_at_x
                mu_g_part = B_makeham * (c_makeham**age_input)
                integral_Bc_part = mu_g_part * (c_makeham - 1.0) / math.log(c_makeham)
            return math.exp(-(integral_A + integral_Bc_part))

        px_func = p_yearly_makeham
        qx_func = lambda age_input: 1.0 - px_func(age_input)
        assumption_description = f"Makeham (A={A_makeham:.6g}, B={B_makeham:.6g}, c={c_makeham:.6g})"
        omega = 150
    else:
        raise ValueError(f"Tipe asumsi tidak dikenal: {assumption_type}")
    
    return qx_func, px_func, omega, assumption_description


def nsp_whole_life_from_assumption( # <-- PASTIKAN NAMA FUNGSI INI PERSIS SEPERTI INI
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
    qx_func, px_func, omega, assumption_desc = _create_assumption_functions(assumption_type, params)
    
    value = calc.nsp_whole_life_from_assumption(age, qx_func, px_func, omega)
    
    formula_str = rf"A_{{{age}}}"
    description = f"NSP Whole Life (Asumsi: {assumption_desc}), Usia {age}"
        
    return ActuarialResult(value, formula_str, description)

def pv_annuity_due_whole_life_from_assumption( # <-- PASTIKAN NAMA FUNGSI INI PERSIS SEPERTI INI
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
    qx_func, px_func, omega, assumption_desc = _create_assumption_functions(assumption_type, params)
        
    value = calc.pv_annuity_due_whole_life_from_assumption(age, px_func, omega)
    
    formula_str = rf"\ddot{{a}}_{{{age}}}"
    description = f"PV Anuitas Whole Life Due (Asumsi: {assumption_desc}), Usia {age}"
        
    return ActuarialResult(value, formula_str, description)

def survival_probability_from_assumption( # <-- PASTIKAN NAMA FUNGSI INI PERSIS SEPERTI INI
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
    
    if assumption_type == 'de_moivre':
        if not params or len(params) < 1: raise ValueError("Parameter omega dibutuhkan untuk 'de_moivre'.")
        omega_val = int(params[0]) # Ganti nama variabel omega agar tidak konflik dengan omega dari _create_assumption_functions
        if age < 0: raise ValueError("Usia tidak boleh negatif.")
        if omega_val <= 0: raise ValueError("Omega harus positif.")
        if period < 0: raise ValueError("Periode tidak boleh negatif.")
        
        if age >= omega_val: value = 1.0 if period == 0 else 0.0
        elif age + period >= omega_val: value = 0.0
        else: value = (omega_val - age - period) / (omega_val - age) if (omega_val - age) != 0 else 0.0
        assumption_description_suffix = f"De Moivre (ω={omega_val})"
    
    elif assumption_type == 'constant_mu_cfm':
        if not params or len(params) < 1: raise ValueError("Parameter mu dibutuhkan untuk 'constant_mu_cfm'.")
        mu = params[0]
        if mu < 0: raise ValueError("Nilai μ untuk 'constant_mu_cfm' harus non-negatif.")
        if period < 0: raise ValueError("Periode tidak boleh negatif.")
        value = math.exp(-mu * period)
        assumption_description_suffix = f"CFM (μ={mu})"

    elif assumption_type in ['constant_qx', 'constant_px', 'gompertz', 'makeham']:
        qx_func, px_func, omega_calc, assumption_desc_short = _create_assumption_functions(assumption_type, params)
        calc = ActuarialCalculator(interest_rate=interest_rate)
        value = calc.survival_probability_from_assumption(age, period, px_func, omega_calc) 
        assumption_description_suffix = f"Asumsi {assumption_desc_short}"
    else:
        raise ValueError(f"Tipe asumsi tidak dikenal: {assumption_type}")

    period_str = str(int(period)) if period == int(period) else f"{period:.2f}"
    formula_str = rf"{{}}_{{{period_str}}}p_{{{age}}}"
    description = f"Probabilitas Hidup {period_str} Tahun ({assumption_description_suffix}), Usia {age}"
    
    return ActuarialResult(value, formula_str, description)