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
    
    formula_actsymbol_str = rf"\ax**{{{age}}}" # Menggunakan makro actuarialsymbol
    
    return ActuarialResult(value, formula_actsymbol_str)

def calculate_survival_prob(
    age: int,
    period: float,
    interest_rate: float, 
    gender: Literal['pria', 'wanita'] = 'pria',
    assumption: Literal['udd', 'cfm'] = 'udd',
    mortality_table: MortalityTable = None # type: ignore
) -> ActuarialResult: # Diubah untuk mengembalikan ActuarialResult
    """
    Fungsi high-level untuk menghitung probabilitas bertahan hidup (_n_p_x)
    untuk periode non-bulat.
    """
    if mortality_table is None:
        mortality_table = load_default_table()
    
    calc = ActuarialCalculator(mortality_table, interest_rate)
    value = calc.p_frac(age, period, gender, assumption)

    # Membuat formula LaTeX sederhana untuk probabilitas hidup
    # _n p_x
    # Anda bisa membuat ini lebih kompleks jika ingin menampilkan formula UDD/CFM
    # secara eksplisit, tapi untuk awal cukup simbolnya saja.
    # Jika 'period' adalah integer, kita bisa hilangkan desimalnya.
    n_str = str(int(period)) if period == int(period) else str(period)
    formula_actsymbol_str = rf"{{}}_{{{n_str}}}p_{{{age}}}"
    if assumption == 'udd':
        formula_actsymbol_str += r"^{{(UDD)}}"
    elif assumption == 'cfm':
        formula_actsymbol_str += r"^{{(CFM)}}"
        
    return ActuarialResult(value, formula_actsymbol_str)