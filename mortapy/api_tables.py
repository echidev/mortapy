# mortapy/api_tables.py
import os
import math
from typing import Literal, Optional, Any # <<< TAMBAHKAN 'Any' DI SINI
from .tables.base import MortalityTable
from .core_calculator import ActuarialCalculator
from .result import ActuarialResult

# (Sisa kode di file ini tetap sama seperti versi terakhir yang sudah kita perbaiki untuk spasi LaTeX)
# Logika path untuk DEFAULT_TABLE_PATH
CURRENT_PACKAGE_DIR = os.path.dirname(__file__)
DEFAULT_TABLE_PATH_PRIMARY = os.path.join(CURRENT_PACKAGE_DIR, 'tables', 'tabel_mortalita_penduduk_indonesia_2023.csv')
DEFAULT_TABLE_PATH_FOR_TESTS_FROM_ROOT = os.path.join("mortapy", "tables", "tabel_mortalita_penduduk_indonesia_2023.csv")
DEFAULT_TABLE_PATH_FOR_EXAMPLES_FROM_ROOT = os.path.join("mortapy", "tables", "tabel_mortalita_penduduk_indonesia_2023.csv")


DEFAULT_TABLE_PATH = DEFAULT_TABLE_PATH_PRIMARY
if not os.path.exists(DEFAULT_TABLE_PATH):
    if "GITHUB_WORKSPACE" in os.environ:
        DEFAULT_TABLE_PATH = os.path.join(os.environ["GITHUB_WORKSPACE"], "mortapy", "tables", "tabel_mortalita_penduduk_indonesia_2023.csv")
    elif os.path.exists(DEFAULT_TABLE_PATH_FOR_TESTS_FROM_ROOT) and "tests" in os.getcwd(): # Asumsi folder 'tests' ada di root
        DEFAULT_TABLE_PATH = DEFAULT_TABLE_PATH_FOR_TESTS_FROM_ROOT
    elif os.path.exists(DEFAULT_TABLE_PATH_FOR_EXAMPLES_FROM_ROOT) and "examples" in os.getcwd(): # Asumsi folder 'examples' ada di root
        DEFAULT_TABLE_PATH = DEFAULT_TABLE_PATH_FOR_EXAMPLES_FROM_ROOT
    else:
        # Fallback jika dijalankan dari struktur lain, misal root proyek
        alt_path_from_project_root = os.path.join(os.path.dirname(CURRENT_PACKAGE_DIR), "mortapy", "tables", "tabel_mortalita_penduduk_indonesia_2023.csv")
        if os.path.exists(alt_path_from_project_root):
            DEFAULT_TABLE_PATH = alt_path_from_project_root
        else:
            DEFAULT_TABLE_PATH = "mortapy/tables/tabel_mortalita_penduduk_indonesia_2023.csv"


_DEFAULT_TABLE_INSTANCE: Optional[MortalityTable] = None

def _get_default_table() -> MortalityTable:
    """Memuat tabel mortalita default hanya sekali (lazy loading)."""
    global _DEFAULT_TABLE_INSTANCE
    if _DEFAULT_TABLE_INSTANCE is None:
        path_to_load = DEFAULT_TABLE_PATH
        if not os.path.exists(path_to_load):
            # Coba path alternatif jika dijalankan dari root proyek (misal saat testing atau examples)
            alt_path_project_root = os.path.join("mortapy", "tables", "tabel_mortalita_penduduk_indonesia_2023.csv")
            if os.path.exists(alt_path_project_root):
                 _DEFAULT_TABLE_INSTANCE = MortalityTable(alt_path_project_root)
            else:
                raise FileNotFoundError(
                    f"Tabel mortalita default tidak ditemukan. Path utama yang dicek: '{DEFAULT_TABLE_PATH}', Path alternatif dari root: '{alt_path_project_root}'"
                )
        else:
            _DEFAULT_TABLE_INSTANCE = MortalityTable(path_to_load)
    return _DEFAULT_TABLE_INSTANCE

def load_default_table() -> MortalityTable:
    """
    Memuat dan mengembalikan instance tabel mortalita default Indonesia.
    Fungsi ini adalah wrapper publik untuk _get_default_table.
    """
    return _get_default_table()

def _validate_table_and_gender(table: MortalityTable, gender: Optional[Literal['pria', 'wanita']]) -> Literal['pria', 'wanita']:
    """Validasi tabel dan gender, mengembalikan gender efektif atau error."""
    if table.has_gender_columns:
        if gender not in ['pria', 'wanita']:
            raise ValueError("Parameter 'gender' ('pria' atau 'wanita') wajib untuk tabel berbasis gender ini.")
        return gender
    elif table.is_unisex_table:
        return 'pria'
    else:
        raise ValueError("Tabel mortalita tidak memiliki kolom gender yang valid atau kolom 'qx' unisex.")

def _build_latex_subscript(base_val: Any, gender_val: Optional[str] = None, is_gender_table: bool = False) -> str:
    """Helper untuk membangun subscript LaTeX yang konsisten."""
    subscript = str(base_val)
    if is_gender_table and gender_val:
        subscript += rf"; \text{{{gender_val.lower()}}}" # Dengan spasi
    return subscript

def nsp_whole_life_from_table(
    age: int,
    interest_rate: float,
    gender: Literal['pria', 'wanita'],
    mortality_table: Optional[MortalityTable] = None
) -> ActuarialResult:
    table_to_use = mortality_table if mortality_table else _get_default_table()
    effective_gender = _validate_table_and_gender(table_to_use, gender)
    calc = ActuarialCalculator(interest_rate=interest_rate)
    value = calc.nsp_whole_life_from_table(age, effective_gender, table_to_use)
    
    subscript = _build_latex_subscript(age, effective_gender, table_to_use.has_gender_columns)
    formula_str = rf"A_{{{subscript}}}"
    
    description = f"NSP Asuransi Jiwa Seumur Hidup (Tabel), Usia {age}"
    if table_to_use.has_gender_columns:
         description += f", Gender {effective_gender.capitalize()}"
    return ActuarialResult(value, formula_str, description)

def pv_annuity_due_whole_life_from_table(
    age: int,
    interest_rate: float,
    gender: Literal['pria', 'wanita'],
    mortality_table: Optional[MortalityTable] = None
) -> ActuarialResult:
    table_to_use = mortality_table if mortality_table else _get_default_table()
    effective_gender = _validate_table_and_gender(table_to_use, gender)
    calc = ActuarialCalculator(interest_rate=interest_rate)
    value = calc.pv_annuity_due_whole_life_from_table(age, effective_gender, table_to_use)
        
    subscript = _build_latex_subscript(age, effective_gender, table_to_use.has_gender_columns)
    formula_str = rf"\ddot{{a}}_{{{subscript}}}"
    
    description = f"PV Anuitas Jiwa Seumur Hidup Awal Tahun (Tabel), Usia {age}"
    if table_to_use.has_gender_columns:
        description += f", Gender {effective_gender.capitalize()}"
    return ActuarialResult(value, formula_str, description)

def survival_probability_from_table(
    age: int,
    n_years: int,
    interest_rate: float,
    gender: Literal['pria', 'wanita'],
    mortality_table: Optional[MortalityTable] = None
) -> ActuarialResult:
    if not isinstance(n_years, int) or n_years < 0:
        raise ValueError("Parameter 'n_years' harus integer non-negatif untuk fungsi ini.")
    table_to_use = mortality_table if mortality_table else _get_default_table()
    effective_gender = _validate_table_and_gender(table_to_use, gender)
    calc = ActuarialCalculator(interest_rate=interest_rate)
    value = calc.survival_probability_from_table(age, n_years, effective_gender, table_to_use)
    
    subscript = _build_latex_subscript(age, effective_gender, table_to_use.has_gender_columns)
    formula_str = rf"{{}}_{{{n_years}}}p_{{{subscript}}}"
    
    description = f"Probabilitas Hidup {n_years} Tahun (Tabel), Usia {age}"
    if table_to_use.has_gender_columns:
        description += f", Gender {effective_gender.capitalize()}"
    return ActuarialResult(value, formula_str, description)

def death_probability_from_table(
    age: int,
    n_years: int,
    interest_rate: float,
    gender: Literal['pria', 'wanita'],
    mortality_table: Optional[MortalityTable] = None
) -> ActuarialResult:
    if not isinstance(n_years, int) or n_years < 0:
        raise ValueError("Parameter 'n_years' harus integer non-negatif.")
    table_to_use = mortality_table if mortality_table else _get_default_table()
    effective_gender = _validate_table_and_gender(table_to_use, gender)
    calc = ActuarialCalculator(interest_rate=interest_rate)
    value = calc.death_probability_from_table(age, n_years, effective_gender, table_to_use)
    
    subscript = _build_latex_subscript(age, effective_gender, table_to_use.has_gender_columns)
    formula_str = rf"{{}}_{{{n_years}}}q_{{{subscript}}}"
    
    description = f"Probabilitas Kematian {n_years} Tahun (Tabel), Usia {age}"
    if table_to_use.has_gender_columns:
        description += f", Gender {effective_gender.capitalize()}"
    return ActuarialResult(value, formula_str, description)

def deferred_death_probability_from_table(
    age: int,
    deferral_period: int,
    n_years_death: int,
    interest_rate: float,
    gender: Literal['pria', 'wanita'],
    mortality_table: Optional[MortalityTable] = None
) -> ActuarialResult:
    if not isinstance(deferral_period, int) or deferral_period < 0:
        raise ValueError("Parameter 'deferral_period' harus integer non-negatif.")
    if not isinstance(n_years_death, int) or n_years_death <= 0:
        raise ValueError("Parameter 'n_years_death' harus integer positif.")
    table_to_use = mortality_table if mortality_table else _get_default_table()
    effective_gender = _validate_table_and_gender(table_to_use, gender)
    calc = ActuarialCalculator(interest_rate=interest_rate)
    value = calc.deferred_death_probability_from_table(age, deferral_period, n_years_death, effective_gender, table_to_use)
    
    subscript = _build_latex_subscript(age, effective_gender, table_to_use.has_gender_columns)
    formula_str = rf"{{}}_{{{deferral_period}|{n_years_death}}}q_{{{subscript}}}"
    
    description = f"Probabilitas Kematian Ditunda {deferral_period}|{n_years_death} (Tabel), Usia {age}"
    if table_to_use.has_gender_columns:
        description += f", Gender {effective_gender.capitalize()}"
    return ActuarialResult(value, formula_str, description)

def force_of_mortality_from_table(
    age: int,
    t_offset: float,
    interest_rate: float,
    gender: Literal['pria', 'wanita'],
    mortality_table: Optional[MortalityTable] = None,
    assumption_fractional: Literal['udd', 'cfm'] = 'cfm'
) -> ActuarialResult:
    if not (0 <= t_offset < 1):
        raise ValueError("t_offset harus antara 0 (inklusif) dan 1 (eksklusif).")
    table_to_use = mortality_table if mortality_table else _get_default_table()
    effective_gender = _validate_table_and_gender(table_to_use, gender)
    qx_at_age = table_to_use.qx(age, effective_gender)
    px_at_age = 1.0 - qx_at_age
    value: float = 0.0
    if assumption_fractional == 'udd':
        denominator_udd = (1.0 - t_offset * qx_at_age)
        value = qx_at_age / denominator_udd if denominator_udd > 1e-12 else float('inf')
        assumption_desc_detail = "UDD"
    elif assumption_fractional == 'cfm':
        value = -math.log(px_at_age) if px_at_age > 1e-12 else float('inf')
        assumption_desc_detail = "CFM"
    else:
        raise ValueError("Asumsi fraksional tidak valid.")

    age_display_raw = age + t_offset
    age_display_str = f"{age_display_raw:.2f}".rstrip('0').rstrip('.') if t_offset > 0 else str(age)
    
    subscript = _build_latex_subscript(age_display_str, effective_gender, table_to_use.has_gender_columns)
    formula_str = rf"\mu_{{{subscript}}}"
    
    description = f"Force of Mortality (Tabel, Interpolasi {assumption_desc_detail}), Usia Tepat {age_display_str}"
    if table_to_use.has_gender_columns:
        description += f", Gender {effective_gender.capitalize()}"
    return ActuarialResult(value, formula_str, description)

def pdf_death_from_table(
    age: int,
    t_period: float,
    interest_rate: float,
    gender: Literal['pria', 'wanita'],
    mortality_table: Optional[MortalityTable] = None,
    assumption_fractional: Literal['udd', 'cfm'] = 'cfm'
) -> ActuarialResult:
    if t_period < 0:
        raise ValueError("t_period tidak boleh negatif.")
    table_to_use = mortality_table if mortality_table else _get_default_table()
    effective_gender = _validate_table_and_gender(table_to_use, gender)
    calc = ActuarialCalculator(interest_rate=interest_rate)
    
    integer_part_t = int(t_period)
    fractional_part_t = t_period - integer_part_t
    
    tpx_value = calc.survival_probability_from_table(age, integer_part_t, effective_gender, table_to_use)
    
    if fractional_part_t > 0 and tpx_value > 0:
        age_after_integer = age + integer_part_t
        if age_after_integer <= table_to_use.max_age :
            qx_base_frac = table_to_use.qx(age_after_integer, effective_gender)
            px_base_frac = 1.0 - qx_base_frac
            if assumption_fractional == 'udd':
                tpx_value *= (1.0 - fractional_part_t * qx_base_frac)
            elif assumption_fractional == 'cfm':
                tpx_value *= (px_base_frac ** fractional_part_t)
        else:
            tpx_value = 0.0

    fom_res_obj = force_of_mortality_from_table(
        age=(age + integer_part_t),
        t_offset=fractional_part_t,
        interest_rate=interest_rate,
        gender=effective_gender,
        mortality_table=table_to_use,
        assumption_fractional=assumption_fractional
    )
    mu_value_at_time_t = fom_res_obj.value
    mu_formula_part = fom_res_obj.formula_latex

    value = tpx_value * mu_value_at_time_t
    
    period_str_for_tpx = f"{t_period:.2f}".rstrip('0').rstrip('.')
    if t_period == int(t_period): period_str_for_tpx = str(int(t_period))

    subscript_tpx = _build_latex_subscript(age, effective_gender, table_to_use.has_gender_columns)
    tpx_formula_part = rf"{{}}_{{{period_str_for_tpx}}}p_{{{subscript_tpx}}}"
    
    formula_str = rf"{tpx_formula_part} \cdot {mu_formula_part}"
    
    age_display_for_desc_raw = age + t_period
    age_display_for_desc = f"{age_display_for_desc_raw:.2f}".rstrip('0').rstrip('.') if t_period > 0 else str(age)
            
    description = f"PDF Kematian pada Usia Tepat {age_display_for_desc} (Tabel, Interpolasi {assumption_fractional})"
    if table_to_use.has_gender_columns:
        description += f", Gender {effective_gender.capitalize()}"
    return ActuarialResult(value, formula_str, description)