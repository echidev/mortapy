# mortapy/api_tables.py
import os
from typing import Literal, Optional
from .tables.base import MortalityTable
from .core_calculator import ActuarialCalculator
from .result import ActuarialResult

# Path default ke tabel bawaan di dalam paket
CURRENT_PACKAGE_DIR = os.path.dirname(__file__)
DEFAULT_TABLE_PATH = os.path.join(CURRENT_PACKAGE_DIR, 'tables', 'tabel_mortalita_penduduk_indonesia_2023.csv')

_DEFAULT_TABLE_INSTANCE: Optional[MortalityTable] = None

def _get_default_table() -> MortalityTable:
    """Memuat tabel mortalita default hanya sekali (lazy loading)."""
    global _DEFAULT_TABLE_INSTANCE
    if _DEFAULT_TABLE_INSTANCE is None:
        if not os.path.exists(DEFAULT_TABLE_PATH):
            alt_path_from_project_root = os.path.join("mortapy", "tables", "tabel_mortalita_penduduk_indonesia_2023.csv")
            if not os.path.exists(alt_path_from_project_root):
                raise FileNotFoundError(
                    f"Tabel mortalita default tidak ditemukan. Sudah dicek: '{DEFAULT_TABLE_PATH}' dan '{alt_path_from_project_root}'"
                )
            _DEFAULT_TABLE_INSTANCE = MortalityTable(alt_path_from_project_root)
        else:
            _DEFAULT_TABLE_INSTANCE = MortalityTable(DEFAULT_TABLE_PATH)
    return _DEFAULT_TABLE_INSTANCE

# PASTIKAN FUNGSI INI ADA DAN BERNAMA PERSIS 'load_default_table'
def load_default_table() -> MortalityTable:
    """
    Memuat dan mengembalikan instance tabel mortalita default Indonesia.
    Fungsi ini adalah wrapper publik untuk _get_default_table.
    """
    return _get_default_table()

def nsp_whole_life(
    age: int,
    interest_rate: float,
    gender: Literal['pria', 'wanita'],
    mortality_table: Optional[MortalityTable] = None
) -> ActuarialResult:
    """
    Menghitung Premi Tunggal Bersih (A_x) untuk asuransi jiwa seumur hidup
    berdasarkan tabel mortalita.

    Args:
        age (int): Usia tertanggung.
        interest_rate (float): Tingkat suku bunga efektif per periode.
        gender (Literal['pria', 'wanita']): Jenis kelamin tertanggung.
        mortality_table (Optional[MortalityTable], optional): 
            Objek tabel mortalita kustom. Jika None, tabel default Indonesia akan digunakan. 
            Defaults to None.

    Returns:
        ActuarialResult: Objek hasil yang berisi nilai NSP dan formula LaTeX-nya.
    """
    table_to_use = mortality_table if mortality_table else _get_default_table()
    
    if table_to_use.has_gender_columns and gender not in ['pria', 'wanita']:
        raise ValueError("Parameter 'gender' ('pria' atau 'wanita') wajib untuk tabel ini.")
    
    effective_gender = gender if table_to_use.has_gender_columns else None

    calc = ActuarialCalculator(interest_rate=interest_rate)
    value = calc.nsp_whole_life_from_table(age, effective_gender if effective_gender else 'pria', table_to_use)
    
    formula_str = rf"A_{{{age}"
    if table_to_use.has_gender_columns and effective_gender:
        formula_str += rf"; \text{{{effective_gender.lower()}}}"
    formula_str += r"}"
    description = f"NSP Asuransi Jiwa Seumur Hidup (Tabel), Usia {age}"
    if table_to_use.has_gender_columns and effective_gender:
         description += f", Gender {effective_gender.capitalize()}"
        
    return ActuarialResult(value, formula_str, description)

def pv_annuity_due_whole_life(
    age: int,
    interest_rate: float,
    gender: Literal['pria', 'wanita'],
    mortality_table: Optional[MortalityTable] = None
) -> ActuarialResult:
    """
    Menghitung nilai sekarang dari anuitas jiwa seumur hidup awal tahun (ä_x)
    berdasarkan tabel mortalita.

    Args:
        age (int): Usia anuitan.
        interest_rate (float): Tingkat suku bunga efektif per periode.
        gender (Literal['pria', 'wanita']): Jenis kelamin anuitan.
        mortality_table (Optional[MortalityTable], optional): 
            Objek tabel mortalita kustom. Jika None, tabel default Indonesia akan digunakan.
            Defaults to None.

    Returns:
        ActuarialResult: Objek hasil yang berisi nilai PV anuitas dan formula LaTeX-nya.
    """
    table_to_use = mortality_table if mortality_table else _get_default_table()
    if table_to_use.has_gender_columns and gender not in ['pria', 'wanita']:
        raise ValueError("Parameter 'gender' ('pria' atau 'wanita') wajib untuk tabel ini.")
    effective_gender = gender if table_to_use.has_gender_columns else None

    calc = ActuarialCalculator(interest_rate=interest_rate)
    value = calc.pv_annuity_due_whole_life_from_table(age, effective_gender if effective_gender else 'pria', table_to_use)
        
    formula_str = rf"\ddot{{a}}_{{{age}"
    if table_to_use.has_gender_columns and effective_gender:
        formula_str += rf"; \text{{{effective_gender.lower()}}}"
    formula_str += r"}"
    description = f"PV Anuitas Jiwa Seumur Hidup Awal Tahun (Tabel), Usia {age}"
    if table_to_use.has_gender_columns and effective_gender:
        description += f", Gender {effective_gender.capitalize()}"
            
    return ActuarialResult(value, formula_str, description)

def survival_probability(
    age: int,
    n_years: int, 
    interest_rate: float, 
    gender: Literal['pria', 'wanita'],
    mortality_table: Optional[MortalityTable] = None
) -> ActuarialResult:
    """
    Menghitung probabilitas hidup _{n}p_{x} untuk periode bulat n tahun
    berdasarkan tabel mortalita.

    Args:
        age (int): Usia awal.
        n_years (int): Jumlah tahun periode (harus bulat).
        interest_rate (float): Tingkat suku bunga (diperlukan untuk konsistensi ActuarialCalculator).
        gender (Literal['pria', 'wanita']): Jenis kelamin.
        mortality_table (Optional[MortalityTable], optional): 
            Objek tabel mortalita kustom. Jika None, tabel default Indonesia akan digunakan.
            Defaults to None.

    Returns:
        ActuarialResult: Objek hasil yang berisi probabilitas dan formula LaTeX-nya.
    """
    if not isinstance(n_years, int) or n_years < 0:
        raise ValueError("Parameter 'n_years' harus integer non-negatif untuk fungsi ini.")

    table_to_use = mortality_table if mortality_table else _get_default_table()
    if table_to_use.has_gender_columns and gender not in ['pria', 'wanita']:
        raise ValueError("Parameter 'gender' ('pria' atau 'wanita') wajib untuk tabel ini.")
    effective_gender = gender if table_to_use.has_gender_columns else None

    calc = ActuarialCalculator(interest_rate=interest_rate)
    value = calc.survival_probability_from_table(age, n_years, effective_gender if effective_gender else 'pria', table_to_use)
    
    formula_str = rf"{{}}_{{{n_years}}}p_{{{age}"
    if table_to_use.has_gender_columns and effective_gender:
        formula_str += rf"; \text{{{effective_gender.lower()}}}"
    formula_str += r"}"
    description = f"Probabilitas Hidup {n_years} Tahun (Tabel), Usia {age}"
    if table_to_use.has_gender_columns and effective_gender:
        description += f", Gender {effective_gender.capitalize()}"
            
    return ActuarialResult(value, formula_str, description)