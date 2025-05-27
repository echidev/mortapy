# mortapy/api_assumptions.py
from typing import Literal, Optional, Callable
import math # Diperlukan untuk math.exp()
from .core_calculator import ActuarialCalculator
from .result import ActuarialResult

# Default values for assumptions if not provided by the user
DEFAULT_OMEGA_DEMOIVRE: int = 110
DEFAULT_MU_CFM: float = 0.02
DEFAULT_QX_CONSTANT: float = 0.01
DEFAULT_PX_CONSTANT: float = 0.98 # (1 - 0.02, contoh)

def _create_assumption_functions(
    assumption_type: Literal['constant_qx', 'constant_px', 'de_moivre', 'constant_mu_cfm'],
    param1: float
) -> tuple[Callable[[int], float], Callable[[int], float], int, str]:
    """
    Membuat fungsi qx_func, px_func, omega (usia maksimum), dan deskripsi asumsi
    berdasarkan tipe asumsi dan parameter yang diberikan.

    Args:
        assumption_type (Literal['constant_qx', ...]): Tipe asumsi distribusi.
        param1 (float): Parameter utama untuk asumsi tersebut.
                        (qx untuk 'constant_qx', px untuk 'constant_px',
                         omega untuk 'de_moivre', mu untuk 'constant_mu_cfm').

    Returns:
        tuple[Callable[[int], float], Callable[[int], float], int, str]: 
            Tuple berisi (qx_function, px_function, omega, assumption_description).
    
    Raises:
        ValueError: Jika assumption_type tidak dikenal atau parameter tidak valid.
    """
    qx_func: Callable[[int], float]
    px_func: Callable[[int], float]
    omega: int = DEFAULT_OMEGA_DEMOIVRE # Default umum, akan ditimpa jika relevan
    assumption_description: str = ""

    if assumption_type == 'constant_qx':
        qx_val = param1
        if not (0 <= qx_val <= 1):
            raise ValueError("Nilai q_x untuk 'constant_qx' harus antara 0 dan 1.")
        qx_func = lambda age_input: qx_val
        px_func = lambda age_input: 1.0 - qx_val
        assumption_description = f"q_x konstan = {qx_val}"
        # Omega di sini kurang relevan, tapi core_calculator membutuhkannya.
        # Kita bisa set ke nilai default tinggi atau membuatnya lebih cerdas.
    
    elif assumption_type == 'constant_px':
        px_val = param1
        if not (0 <= px_val <= 1):
            raise ValueError("Nilai p_x untuk 'constant_px' harus antara 0 dan 1.")
        px_func = lambda age_input: px_val
        qx_func = lambda age_input: 1.0 - px_val
        assumption_description = f"p_x konstan = {px_val}"

    elif assumption_type == 'de_moivre':
        current_omega = int(param1)
        if current_omega <= 0:
            raise ValueError("Omega untuk De Moivre harus integer positif.")
        omega = current_omega # Set omega spesifik untuk De Moivre
        
        def qx_de_moivre(age_input: int) -> float:
            if age_input < omega:
                denominator = omega - age_input
                return 1.0 / denominator if denominator > 0 else 1.0 # Hindari pembagian dengan nol
            return 1.0 # Pasti meninggal pada atau setelah omega
        
        def px_de_moivre(age_input: int) -> float:
            if age_input < omega - 1: # Bisa hidup 1 tahun lagi jika masih di bawah omega-1
                 denominator = omega - age_input
                 # Pastikan denominator tidak nol
                 return (omega - age_input - 1.0) / denominator if denominator > 0 else 0.0
            return 0.0 # Tidak bisa hidup 1 tahun lagi jika usia x+1 >= omega
            
        qx_func = qx_de_moivre
        px_func = px_de_moivre
        assumption_description = f"De Moivre (ω={omega})"
        
    elif assumption_type == 'constant_mu_cfm':
        mu = param1
        if mu < 0: # mu bisa 0, yang berarti tidak ada mortalita
            raise ValueError("Nilai μ untuk 'constant_mu_cfm' harus non-negatif.")
        px_val_yearly = math.exp(-mu) # p_x tahunan dari mu
        qx_val_yearly = 1.0 - px_val_yearly
        qx_func = lambda age_input: qx_val_yearly
        px_func = lambda age_input: px_val_yearly
        assumption_description = f"CFM (μ={mu})"
    else:
        raise ValueError(f"Tipe asumsi tidak dikenal: {assumption_type}")
    
    return qx_func, px_func, omega, assumption_description


def nsp_whole_life_from_assumption(
    age: int,
    interest_rate: float,
    assumption_type: Literal['constant_qx', 'constant_px', 'de_moivre', 'constant_mu_cfm'],
    param1: float 
) -> ActuarialResult:
    """
    Menghitung Premi Tunggal Bersih (A_x) untuk asuransi jiwa seumur hidup
    berdasarkan asumsi distribusi murni.

    Args:
        age (int): Usia tertanggung.
        interest_rate (float): Tingkat suku bunga efektif per periode.
        assumption_type (Literal['constant_qx', ...]): Tipe asumsi distribusi.
        param1 (float): Parameter pertama untuk asumsi 
                        (qx untuk 'constant_qx', px untuk 'constant_px', 
                         omega untuk 'de_moivre', mu untuk 'constant_mu_cfm').

    Returns:
        ActuarialResult: Objek hasil yang berisi nilai NSP dan formula LaTeX-nya.
    """
    calc = ActuarialCalculator(interest_rate=interest_rate)
    qx_func, px_func, omega, assumption_desc = _create_assumption_functions(assumption_type, param1)
    
    value = calc.nsp_whole_life_from_assumption(age, qx_func, px_func, omega)
    
    formula_str = rf"A_{{{age}}}"
    description = f"NSP Whole Life (Asumsi: {assumption_desc}), Usia {age}"
        
    return ActuarialResult(value, formula_str, description)


def pv_annuity_due_whole_life_from_assumption(
    age: int,
    interest_rate: float,
    assumption_type: Literal['constant_qx', 'constant_px', 'de_moivre', 'constant_mu_cfm'],
    param1: float
) -> ActuarialResult:
    """
    Menghitung nilai sekarang dari anuitas jiwa seumur hidup awal tahun (ä_x)
    berdasarkan asumsi distribusi murni.

    Args:
        age (int): Usia anuitan.
        interest_rate (float): Tingkat suku bunga efektif per periode.
        assumption_type (Literal['constant_qx', ...]): Tipe asumsi distribusi.
        param1 (float): Parameter untuk asumsi (qx, px, omega, atau mu).

    Returns:
        ActuarialResult: Objek hasil yang berisi nilai PV anuitas dan formula LaTeX-nya.
    """
    calc = ActuarialCalculator(interest_rate=interest_rate)
    qx_func, px_func, omega, assumption_desc = _create_assumption_functions(assumption_type, param1)
        
    value = calc.pv_annuity_due_whole_life_from_assumption(age, px_func, omega)
    
    formula_str = rf"\ddot{{a}}_{{{age}}}"
    description = f"PV Anuitas Whole Life Due (Asumsi: {assumption_desc}), Usia {age}"
        
    return ActuarialResult(value, formula_str, description)


def survival_probability_from_assumption(
    age: int,
    period: float, 
    interest_rate: float, # Secara teknis tidak selalu dipakai untuk p_x murni, tapi untuk ActuarialCalculator
    assumption_type: Literal['constant_qx', 'constant_px', 'de_moivre', 'constant_mu_cfm'],
    param1: float
) -> ActuarialResult:
    """
    Menghitung probabilitas hidup _{n}p_{x} untuk periode (bisa non-bulat) n
    berdasarkan asumsi distribusi murni.

    Args:
        age (int): Usia awal.
        period (float): Jumlah tahun periode (bisa fraksional).
        interest_rate (float): Diperlukan untuk inisialisasi ActuarialCalculator.
        assumption_type (Literal['constant_qx', ...]): Tipe asumsi.
        param1 (float): Parameter untuk asumsi (qx, px, omega, atau mu).

    Returns:
        ActuarialResult: Objek hasil yang berisi probabilitas dan formula LaTeX-nya.
    """
    value: float = 0.0
    assumption_description_suffix: str = ""

    if assumption_type == 'de_moivre':
        omega = int(param1)
        if age < 0: raise ValueError("Usia tidak boleh negatif.")
        if omega <= 0: raise ValueError("Omega harus positif.")
        
        if age >= omega: # Usia awal sudah di atau melewati omega
             value = 1.0 if period == 0 else 0.0
        elif age + period >= omega: # Akan melewati omega selama periode
            value = 0.0
        elif period < 0: # Periode tidak boleh negatif
            raise ValueError("Periode tidak boleh negatif.")
        else: # Kasus normal
            value = (omega - age - period) / (omega - age) if (omega - age) != 0 else 0.0
        assumption_description_suffix = f"De Moivre (ω={omega})"
    
    elif assumption_type == 'constant_mu_cfm':
        mu = param1
        if mu < 0:
            raise ValueError("Nilai μ untuk 'constant_mu_cfm' harus non-negatif.")
        if period < 0:
            raise ValueError("Periode tidak boleh negatif.")
        value = math.exp(-mu * period) # _t p_x = e^(-mu*t)
        assumption_description_suffix = f"CFM (μ={mu})"

    elif assumption_type == 'constant_qx' or assumption_type == 'constant_px':
        qx_func, px_func, omega_calc, assumption_desc_short = _create_assumption_functions(assumption_type, param1)
        calc = ActuarialCalculator(interest_rate=interest_rate)
        # Menggunakan metode survival_probability_from_assumption di core_calculator
        # yang sudah bisa menangani periode float dengan asumsi CFM untuk bagian fraksionalnya
        value = calc.survival_probability_from_assumption(age, period, px_func, omega_calc)
        assumption_description_suffix = f"Asumsi {assumption_desc_short}"
    else:
        raise ValueError(f"Tipe asumsi tidak dikenal: {assumption_type}")

    period_str = str(int(period)) if period == int(period) else f"{period:.2f}"
    formula_str = rf"{{}}_{{{period_str}}}p_{{{age}}}"
    description = f"Probabilitas Hidup {period_str} Tahun ({assumption_description_suffix}), Usia {age}"
    
    return ActuarialResult(value, formula_str, description)