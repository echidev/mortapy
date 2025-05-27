# mortapy/api.py

import os
from typing import Literal, Optional
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
    gender: Optional[Literal['pria', 'wanita']] = None,
    mortality_table: Optional[MortalityTable] = None,
    base_qx: Optional[float] = None,
    base_px: Optional[float] = None
) -> ActuarialResult:
    
    table_to_use = mortality_table
    if mortality_table is None and base_qx is None and base_px is None:
        table_to_use = load_default_table()

    calc = ActuarialCalculator(
        interest_rate=interest_rate, 
        mortality_table=table_to_use, 
        base_qx=base_qx, 
        base_px=base_px
    )
    value = calc.Ax(age, gender)
    
    age_str = str(age)
    formula_str_for_latex = rf"A_{{{age_str}}}" # Contoh simbol LaTeX dasar
    # Jika ingin formula lengkap:
    # formula_str_for_latex = rf"A_{{{age_str}}} = \sum_{{k=0}}^{{\omega-{age_str}-1}} v^{{k+1}} \cdot {{}}_{{k}}p_{{{age_str}}} \cdot q_{{{age_str}+k}}"
    
    return ActuarialResult(value, formula_str_for_latex)

def calculate_whole_life_annuity_pv(
    age: int,
    interest_rate: float,
    gender: Optional[Literal['pria', 'wanita']] = None,
    mortality_table: Optional[MortalityTable] = None,
    base_qx: Optional[float] = None,
    base_px: Optional[float] = None
) -> ActuarialResult:

    table_to_use = mortality_table
    if mortality_table is None and base_qx is None and base_px is None:
        table_to_use = load_default_table()
        
    calc = ActuarialCalculator(
        interest_rate=interest_rate, 
        mortality_table=table_to_use, 
        base_qx=base_qx, 
        base_px=base_px
    )
    value = calc.a_due_x(age, gender)
    
    age_str = str(age)
    formula_str_for_latex = rf"\ddot{{a}}_{{{age_str}}}" # Contoh simbol LaTeX dasar
    # Jika ingin formula lengkap:
    # formula_str_for_latex = rf"\ddot{{a}}_{{{age_str}}} = \sum_{{k=0}}^{{\omega-{age_str}}} v^{{k}} \cdot {{}}_{{k}}p_{{{age_str}}}"
    
    return ActuarialResult(value, formula_str_for_latex)

def calculate_survival_prob_integer(
    age: int,
    period_years: int,
    interest_rate: float, 
    gender: Optional[Literal['pria', 'wanita']] = None,
    mortality_table: Optional[MortalityTable] = None,
    base_qx: Optional[float] = None,
    base_px: Optional[float] = None
) -> ActuarialResult:
    
    table_to_use = mortality_table
    if mortality_table is None and base_qx is None and base_px is None:
        table_to_use = load_default_table()

    if base_qx is not None and period_years > 1:
        print("Peringatan: base_qx tunggal digunakan untuk periode multi-tahun. Asumsi qx konstan.")
    if base_px is not None and period_years > 1:
        print("Peringatan: base_px tunggal digunakan untuk periode multi-tahun. Asumsi px konstan.")

    calc = ActuarialCalculator(
        interest_rate=interest_rate, 
        mortality_table=table_to_use, 
        base_qx=base_qx, 
        base_px=base_px
    )
    value = calc.p(age, period_years, gender)

    n_str = str(period_years)
    age_str = str(age)
    formula_str_for_latex = rf"{{}}_{{{n_str}}}p_{{{age_str}}}"
        
    return ActuarialResult(value, formula_str_for_latex)