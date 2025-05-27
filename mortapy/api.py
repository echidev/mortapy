# mortapy/api.py

import os
from typing import Literal
from .tables.base import MortalityTable
from .core import ActuarialCalculator
from .result import ActuarialResult # Pastikan ini diimpor

# Path default ke tabel bawaan di dalam paket
DEFAULT_TABLE_PATH = os.path.join(os.path.dirname(__file__), 'tables', 'tabel_mortalita_penduduk_indonesia_2023.csv')

def load_default_table() -> MortalityTable:
    """Memuat tabel mortalita default yang disertakan dengan library."""
    return MortalityTable(DEFAULT_TABLE_PATH)

def calculate_whole_life_nsp(
    age: int,
    interest_rate: float,
    gender: Literal['pria', 'wanita'] = 'pria',
    mortality_table: MortalityTable = None # type: ignore
) -> ActuarialResult:
    if mortality_table is None:
        mortality_table = load_default_table()
    
    calc = ActuarialCalculator(mortality_table, interest_rate)
    value = calc.Ax(age, gender)
    
    # Gunakan makro yang akan diparsing oleh latex_renderer.py
    # Misal, kita ingin menggunakan \Ax{x} seperti di PDF
    formula_actsymbol_str = rf"\Ax{{{age}}}" 
    
    return ActuarialResult(value, formula_actsymbol_str)

def calculate_whole_life_annuity_pv(
    age: int,
    interest_rate: float,
    gender: Literal['pria', 'wanita'] = 'pria',
    mortality_table: MortalityTable = None # type: ignore
) -> ActuarialResult:
    if mortality_table is None:
        mortality_table = load_default_table()
        
    calc = ActuarialCalculator(mortality_table, interest_rate)
    value = calc.a_due_x(age, gender)
    
    # Menggunakan makro \ax**{x} (annuity due)
    formula_actsymbol_str = rf"\ax**{{{age}}}"
    
    return ActuarialResult(value, formula_actsymbol_str)

# INI FUNGSI YANG PERLU DIPASTIKAN ADA DAN BENAR
def calculate_survival_prob(
    age: int,
    period: float,
    interest_rate: float, 
    gender: Literal['pria', 'wanita'] = 'pria',
    assumption: Literal['udd', 'cfm'] = 'udd',
    mortality_table: MortalityTable = None # type: ignore
) -> float:
    """
    Fungsi high-level untuk menghitung probabilitas bertahan hidup (_n_p_x)
    untuk periode non-bulat.
    """
    if mortality_table is None:
        mortality_table = load_default_table()
    
    calc = ActuarialCalculator(mortality_table, interest_rate)
    return calc.p_frac(age, period, gender, assumption)