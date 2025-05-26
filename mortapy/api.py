# mortapy/api.py

import os
from typing import Literal
from .tables.base import MortalityTable
from .core import ActuarialCalculator

# Path default ke tabel bawaan di dalam paket
DEFAULT_TABLE_PATH = os.path.join(os.path.dirname(__file__), 'tables', 'tabel_mortalita_penduduk_indonesia_2023.csv')

def load_default_table() -> MortalityTable:
    """Memuat tabel mortalita default yang disertakan dengan library."""
    return MortalityTable(DEFAULT_TABLE_PATH)

def calculate_whole_life_nsp(
    age: int,
    interest_rate: float,
    gender: Literal['pria', 'wanita'] = 'pria',
    mortality_table: MortalityTable = None
) -> float:
    """
    Fungsi high-level untuk menghitung Net Single Premium asuransi jiwa seumur hidup.
    """
    if mortality_table is None:
        mortality_table = load_default_table()
    
    calc = ActuarialCalculator(mortality_table, interest_rate)
    return calc.Ax(age, gender)

def calculate_whole_life_annuity_pv(
    age: int,
    interest_rate: float,
    gender: Literal['pria', 'wanita'] = 'pria',
    mortality_table: MortalityTable = None
) -> float:
    """
    Fungsi high-level untuk menghitung PV anuitas jiwa seumur hidup awal tahun.
    """
    if mortality_table is None:
        mortality_table = load_default_table()
        
    calc = ActuarialCalculator(mortality_table, interest_rate)
    return calc.a_due_x(age, gender)

def calculate_survival_prob(
    age: int,
    period: float,
    interest_rate: float,
    gender: Literal['pria', 'wanita'] = 'pria',
    assumption: Literal['udd', 'cfm'] = 'udd',
    mortality_table: MortalityTable = None
) -> float:
    """
    Fungsi high-level untuk menghitung probabilitas bertahan hidup (_n_p_x)
    untuk periode non-bulat.
    """
    if mortality_table is None:
        mortality_table = load_default_table()
    
    calc = ActuarialCalculator(mortality_table, interest_rate)
    return calc.p_frac(age, period, gender, assumption)