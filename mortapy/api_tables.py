# mortapy/api_tables.py
import os
import math
from typing import Literal, Optional, Any, Callable # Any ditambahkan
from .tables.base import MortalityTable
from .core_calculator import ActuarialCalculator
from .result import ActuarialResult

# (Logika path DEFAULT_TABLE_PATH dan fungsi _get_default_table, load_default_table, _validate_table_and_gender, _build_latex_subscript tetap sama)
CURRENT_MODULE_DIR = os.path.dirname(__file__)
PATH_CANDIDATES = [
    os.path.join(CURRENT_MODULE_DIR, 'tables', 'tabel_mortalita_penduduk_indonesia_2023.csv'),
    os.path.join(os.path.dirname(CURRENT_MODULE_DIR), "tables", "tabel_mortalita_penduduk_indonesia_2023.csv"),
    os.path.join("mortapy", "tables", "tabel_mortalita_penduduk_indonesia_2023.csv")
]
DEFAULT_TABLE_PATH = None
for path_candidate in PATH_CANDIDATES:
    if os.path.exists(path_candidate):
        DEFAULT_TABLE_PATH = path_candidate
        break
if DEFAULT_TABLE_PATH is None:
    DEFAULT_TABLE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(CURRENT_MODULE_DIR))), 'mortapy', 'tables', 'tabel_mortalita_penduduk_indonesia_2023.csv')
    if not os.path.exists(DEFAULT_TABLE_PATH) :
        DEFAULT_TABLE_PATH = "mortapy/tables/tabel_mortalita_penduduk_indonesia_2023.csv"

_DEFAULT_TABLE_INSTANCE: Optional[MortalityTable] = None

def _get_default_table() -> MortalityTable:
    global _DEFAULT_TABLE_INSTANCE
    if _DEFAULT_TABLE_INSTANCE is None:
        path_to_load = DEFAULT_TABLE_PATH
        if not os.path.exists(path_to_load):
            alt_path_project_root = os.path.join("mortapy", "tables", "tabel_mortalita_penduduk_indonesia_2023.csv")
            if os.path.exists(alt_path_project_root):
                 _DEFAULT_TABLE_INSTANCE = MortalityTable(alt_path_project_root)
            else:
                raise FileNotFoundError(
                    f"Tabel mortalita default tidak ditemukan. Path utama: '{DEFAULT_TABLE_PATH}', Path alternatif: '{alt_path_project_root}'"
                )
        else:
            _DEFAULT_TABLE_INSTANCE = MortalityTable(path_to_load)
    return _DEFAULT_TABLE_INSTANCE

def load_default_table() -> MortalityTable:
    return _get_default_table()

def _validate_table_and_gender(table: MortalityTable, gender: Optional[Literal['pria', 'wanita']]) -> Literal['pria', 'wanita']:
    if table.has_gender_columns:
        if gender not in ['pria', 'wanita']:
            raise ValueError("Parameter 'gender' ('pria' atau 'wanita') wajib untuk tabel berbasis gender ini.")
        return gender
    elif table.is_unisex_table:
        return 'pria'
    else:
        raise ValueError("Tabel mortalita tidak memiliki kolom gender yang valid atau kolom 'qx' unisex.")

def _build_latex_subscript(base_val: Any, gender_val: Optional[str] = None, is_gender_table: bool = False, n_temp: Optional[int] = None) -> str:
    subscript = str(base_val)
    if n_temp is not None:
        subscript += rf":\overline{{{n_temp}}}|"
    if is_gender_table and gender_val:
        subscript += rf"; \text{{{gender_val.lower()}}}"
    return subscript

def nsp_whole_life_from_table(
    age: int, interest_rate: float, gender: Literal['pria', 'wanita'], 
    mortality_table: Optional[MortalityTable] = None
) -> ActuarialResult:
    table_to_use = mortality_table if mortality_table else _get_default_table()
    effective_gender = _validate_table_and_gender(table_to_use, gender)
    calc = ActuarialCalculator(interest_rate=interest_rate)
    value = calc.nsp_whole_life_from_table(age, effective_gender, table_to_use)
    subscript = _build_latex_subscript(age, effective_gender, table_to_use.has_gender_columns)
    formula_str = rf"A_{{{subscript}}}"
    description = f"NSP Asuransi Jiwa Seumur Hidup (Tabel), Usia {age}"
    if table_to_use.has_gender_columns: description += f", Gender {effective_gender.capitalize()}"
    return ActuarialResult(value, formula_str, description)

def pv_annuity_due_whole_life_from_table(
    age: int, interest_rate: float, gender: Literal['pria', 'wanita'], 
    mortality_table: Optional[MortalityTable] = None
) -> ActuarialResult:
    table_to_use = mortality_table if mortality_table else _get_default_table()
    effective_gender = _validate_table_and_gender(table_to_use, gender)
    calc = ActuarialCalculator(interest_rate=interest_rate)
    value = calc.pv_annuity_due_whole_life_from_table(age, effective_gender, table_to_use)
    subscript = _build_latex_subscript(age, effective_gender, table_to_use.has_gender_columns)
    formula_str = rf"\ddot{{a}}_{{{subscript}}}"
    description = f"PV Anuitas Jiwa Seumur Hidup Awal Tahun (Tabel), Usia {age}"
    if table_to_use.has_gender_columns: description += f", Gender {effective_gender.capitalize()}"
    return ActuarialResult(value, formula_str, description)

def survival_probability_from_table(
    age: int, n_years: int, interest_rate: float, 
    gender: Literal['pria', 'wanita'], mortality_table: Optional[MortalityTable] = None
) -> ActuarialResult:
    if not isinstance(n_years, int) or n_years < 0: raise ValueError("Parameter 'n_years' harus integer non-negatif.")
    table_to_use = mortality_table if mortality_table else _get_default_table()
    effective_gender = _validate_table_and_gender(table_to_use, gender)
    calc = ActuarialCalculator(interest_rate=interest_rate)
    value = calc.survival_probability_from_table(age, n_years, effective_gender, table_to_use)
    subscript = _build_latex_subscript(age, effective_gender, table_to_use.has_gender_columns)
    formula_str = rf"{{}}_{{{n_years}}}p_{{{subscript}}}"
    description = f"Probabilitas Hidup {n_years} Tahun (Tabel), Usia {age}"
    if table_to_use.has_gender_columns: description += f", Gender {effective_gender.capitalize()}"
    return ActuarialResult(value, formula_str, description)

def death_probability_from_table(
    age: int, n_years: int, interest_rate: float, 
    gender: Literal['pria', 'wanita'], mortality_table: Optional[MortalityTable] = None
) -> ActuarialResult:
    if not isinstance(n_years, int) or n_years < 0: raise ValueError("Parameter 'n_years' harus integer non-negatif.")
    table_to_use = mortality_table if mortality_table else _get_default_table()
    effective_gender = _validate_table_and_gender(table_to_use, gender)
    calc = ActuarialCalculator(interest_rate=interest_rate)
    value = calc.death_probability_from_table(age, n_years, effective_gender, table_to_use)
    subscript = _build_latex_subscript(age, effective_gender, table_to_use.has_gender_columns)
    formula_str = rf"{{}}_{{{n_years}}}q_{{{subscript}}}"
    description = f"Probabilitas Kematian {n_years} Tahun (Tabel), Usia {age}"
    if table_to_use.has_gender_columns: description += f", Gender {effective_gender.capitalize()}"
    return ActuarialResult(value, formula_str, description)

def deferred_death_probability_from_table(
    age: int, deferral_period: int, n_years_death: int, interest_rate: float, 
    gender: Literal['pria', 'wanita'], mortality_table: Optional[MortalityTable] = None
) -> ActuarialResult:
    if not isinstance(deferral_period, int) or deferral_period < 0: raise ValueError("Parameter 'deferral_period' harus integer non-negatif.")
    if not isinstance(n_years_death, int) or n_years_death <= 0: raise ValueError("Parameter 'n_years_death' harus integer positif.")
    table_to_use = mortality_table if mortality_table else _get_default_table()
    effective_gender = _validate_table_and_gender(table_to_use, gender)
    calc = ActuarialCalculator(interest_rate=interest_rate)
    value = calc.deferred_death_probability_from_table(age, deferral_period, n_years_death, effective_gender, table_to_use)
    subscript = _build_latex_subscript(age, effective_gender, table_to_use.has_gender_columns)
    formula_str = rf"{{}}_{{{deferral_period}|{n_years_death}}}q_{{{subscript}}}"
    description = f"Probabilitas Kematian Ditunda {deferral_period}|{n_years_death} (Tabel), Usia {age}"
    if table_to_use.has_gender_columns: description += f", Gender {effective_gender.capitalize()}"
    return ActuarialResult(value, formula_str, description)

def force_of_mortality_from_table(
    age: int, t_offset: float, interest_rate: float, 
    gender: Literal['pria', 'wanita'], mortality_table: Optional[MortalityTable] = None, 
    assumption_fractional: Literal['udd', 'cfm'] = 'cfm'
) -> ActuarialResult:
    if not (0 <= t_offset < 1): raise ValueError("t_offset harus antara 0 (inklusif) dan 1 (eksklusif).")
    table_to_use = mortality_table if mortality_table else _get_default_table()
    effective_gender = _validate_table_and_gender(table_to_use, gender)
    calc = ActuarialCalculator(interest_rate=interest_rate)
    value = calc.force_of_mortality_from_table(age, t_offset, effective_gender, table_to_use, assumption_fractional)
    age_display_raw = age + t_offset
    age_display_str = f"{age_display_raw:.2f}".rstrip('0').rstrip('.') if t_offset > 0 else str(age)
    subscript = _build_latex_subscript(age_display_str, effective_gender, table_to_use.has_gender_columns)
    formula_str = rf"\mu_{{{subscript}}}"
    description = f"Force of Mortality (Tabel, Interpolasi {assumption_fractional.upper()}), Usia Tepat {age_display_str}"
    if table_to_use.has_gender_columns: description += f", Gender {effective_gender.capitalize()}"
    return ActuarialResult(value, formula_str, description)

def pdf_death_from_table(
    age: int, t_period: float, interest_rate: float, 
    gender: Literal['pria', 'wanita'], mortality_table: Optional[MortalityTable] = None, 
    assumption_fractional: Literal['udd', 'cfm'] = 'cfm'
) -> ActuarialResult:
    if t_period < 0: raise ValueError("t_period tidak boleh negatif.")
    table_to_use = mortality_table if mortality_table else _get_default_table()
    effective_gender = _validate_table_and_gender(table_to_use, gender)
    calc = ActuarialCalculator(interest_rate=interest_rate)
    value = calc.pdf_death_from_table(age, t_period, effective_gender, table_to_use, assumption_fractional)
    
    period_str_for_tpx = f"{t_period:.2f}".rstrip('0').rstrip('.')
    if t_period == int(t_period): period_str_for_tpx = str(int(t_period))
    subscript_tpx = _build_latex_subscript(age, effective_gender, table_to_use.has_gender_columns)
    tpx_formula_part = rf"{{}}_{{{period_str_for_tpx}}}p_{{{subscript_tpx}}}"
    
    integer_part_t = int(t_period)
    fractional_part_t = t_period - integer_part_t
    fom_res_obj = force_of_mortality_from_table(
        age=(age + integer_part_t), t_offset=fractional_part_t, interest_rate=interest_rate, 
        gender=effective_gender, mortality_table=table_to_use, assumption_fractional=assumption_fractional
    )
    mu_formula_part = fom_res_obj.formula_latex
    formula_str = rf"{tpx_formula_part} \cdot {mu_formula_part}"
    
    age_display_for_desc_raw = age + t_period
    age_display_for_desc = f"{age_display_for_desc_raw:.2f}".rstrip('0').rstrip('.') if t_period > 0 else str(age)
    description = f"PDF Kematian pada Usia Tepat {age_display_for_desc} (Tabel, Interpolasi {assumption_fractional.upper()})"
    if table_to_use.has_gender_columns: description += f", Gender {effective_gender.capitalize()}"
    return ActuarialResult(value, formula_str, description)

# --- FUNGSI MOMEN CURTATE BERBASIS TABEL ---
def expected_curtate_future_lifetime_from_table(
    age: int, interest_rate: float, gender: Literal['pria', 'wanita'],
    mortality_table: Optional[MortalityTable] = None, n_temp: Optional[int] = None
) -> ActuarialResult:
    table_to_use = mortality_table if mortality_table else _get_default_table()
    effective_gender = _validate_table_and_gender(table_to_use, gender)
    calc = ActuarialCalculator(interest_rate=interest_rate)
    value = calc.ex_curtate_from_table(age, effective_gender, table_to_use, n_temp)
    subscript_content = _build_latex_subscript(age, effective_gender, table_to_use.has_gender_columns, n_temp=n_temp)
    formula_str = rf"e_{{{subscript_content}}}"
    term_desc = f"{n_temp}-tahun temporary " if n_temp is not None else ""
    description = f"Ekspektasi Curtate Future Lifetime {term_desc}(Tabel), Usia {age}"
    if table_to_use.has_gender_columns: description += f", Gender {effective_gender.capitalize()}"
    return ActuarialResult(value, formula_str, description)

def second_moment_curtate_future_lifetime_from_table(
    age: int, interest_rate: float, gender: Literal['pria', 'wanita'],
    mortality_table: Optional[MortalityTable] = None, n_temp: Optional[int] = None
) -> ActuarialResult:
    table_to_use = mortality_table if mortality_table else _get_default_table()
    effective_gender = _validate_table_and_gender(table_to_use, gender)
    calc = ActuarialCalculator(interest_rate=interest_rate)
    value = calc.e_sq_curtate_from_table(age, effective_gender, table_to_use, n_temp)
    subscript_content = _build_latex_subscript(age, effective_gender, table_to_use.has_gender_columns, n_temp=n_temp)
    formula_str = rf"E[K_{{{subscript_content}}}^2]"
    term_desc = f"{n_temp}-tahun temporary " if n_temp is not None else ""
    description = f"Momen Kedua Curtate Future Lifetime {term_desc}(Tabel), Usia {age}"
    if table_to_use.has_gender_columns: description += f", Gender {effective_gender.capitalize()}"
    return ActuarialResult(value, formula_str, description)

def variance_curtate_future_lifetime_from_table(
    age: int, interest_rate: float, gender: Literal['pria', 'wanita'],
    mortality_table: Optional[MortalityTable] = None, n_temp: Optional[int] = None
) -> ActuarialResult:
    table_to_use = mortality_table if mortality_table else _get_default_table()
    effective_gender = _validate_table_and_gender(table_to_use, gender)
    ex_result_obj = expected_curtate_future_lifetime_from_table(age, interest_rate, effective_gender, mortality_table, n_temp)
    e_sq_result_obj = second_moment_curtate_future_lifetime_from_table(age, interest_rate, effective_gender, mortality_table, n_temp)
    value = e_sq_result_obj.value - (ex_result_obj.value ** 2)
    subscript_content = _build_latex_subscript(age, effective_gender, table_to_use.has_gender_columns, n_temp=n_temp)
    formula_str = rf"Var[K_{{{subscript_content}}}]"
    term_desc = f"{n_temp}-tahun temporary " if n_temp is not None else ""
    description = f"Variansi Curtate Future Lifetime {term_desc}(Tabel), Usia {age}"
    if table_to_use.has_gender_columns: description += f", Gender {effective_gender.capitalize()}"
    return ActuarialResult(value, formula_str, description)

# --- FUNGSI BARU UNTUK MOMEN COMPLETE BERBASIS TABEL ---
def expected_complete_future_lifetime_from_table(
    age: int, interest_rate: float, gender: Literal['pria', 'wanita'],
    mortality_table: Optional[MortalityTable] = None, n_temp: Optional[int] = None,
    assumption_fractional: Literal['udd', 'cfm'] = 'udd'
) -> ActuarialResult:
    table_to_use = mortality_table if mortality_table else _get_default_table()
    effective_gender = _validate_table_and_gender(table_to_use, gender)
    calc = ActuarialCalculator(interest_rate=interest_rate)
    value = calc.ex_complete_from_table(age, effective_gender, table_to_use, n_temp, assumption_fractional)
    subscript_content = _build_latex_subscript(age, effective_gender, table_to_use.has_gender_columns, n_temp=n_temp)
    formula_str = rf"\mathring{{e}}_{{{subscript_content}}}"
    term_desc = f"{n_temp}-tahun temporary " if n_temp is not None else ""
    description = f"Ekspektasi Complete Future Lifetime {term_desc}(Tabel, Frac: {assumption_fractional.upper()}), Usia {age}"
    if table_to_use.has_gender_columns: description += f", Gender {effective_gender.capitalize()}"
    return ActuarialResult(value, formula_str, description)

def second_moment_complete_future_lifetime_from_table(
    age: int, interest_rate: float, gender: Literal['pria', 'wanita'],
    mortality_table: Optional[MortalityTable] = None, n_temp: Optional[int] = None,
    assumption_fractional: Literal['udd', 'cfm'] = 'udd'
) -> ActuarialResult:
    table_to_use = mortality_table if mortality_table else _get_default_table()
    effective_gender = _validate_table_and_gender(table_to_use, gender)
    calc = ActuarialCalculator(interest_rate=interest_rate)
    value = calc.e_sq_complete_from_table(age, effective_gender, table_to_use, n_temp, assumption_fractional)
    subscript_content = _build_latex_subscript(age, effective_gender, table_to_use.has_gender_columns, n_temp=n_temp)
    formula_str = rf"E[T_{{{subscript_content}}}^2]"
    term_desc = f"{n_temp}-tahun temporary " if n_temp is not None else ""
    description = f"Momen Kedua Complete Future Lifetime {term_desc}(Tabel, Frac: {assumption_fractional.upper()}), Usia {age}"
    if table_to_use.has_gender_columns: description += f", Gender {effective_gender.capitalize()}"
    return ActuarialResult(value, formula_str, description)

def variance_complete_future_lifetime_from_table(
    age: int, interest_rate: float, gender: Literal['pria', 'wanita'],
    mortality_table: Optional[MortalityTable] = None, n_temp: Optional[int] = None,
    assumption_fractional: Literal['udd', 'cfm'] = 'udd'
) -> ActuarialResult:
    table_to_use = mortality_table if mortality_table else _get_default_table()
    effective_gender = _validate_table_and_gender(table_to_use, gender)
    ex_circ_result_obj = expected_complete_future_lifetime_from_table(age, interest_rate, effective_gender, mortality_table, n_temp, assumption_fractional)
    e_sq_circ_result_obj = second_moment_complete_future_lifetime_from_table(age, interest_rate, effective_gender, mortality_table, n_temp, assumption_fractional)
    value = e_sq_circ_result_obj.value - (ex_circ_result_obj.value ** 2)
    subscript_content = _build_latex_subscript(age, effective_gender, table_to_use.has_gender_columns, n_temp=n_temp)
    formula_str = rf"Var[T_{{{subscript_content}}}]"
    term_desc = f"{n_temp}-tahun temporary " if n_temp is not None else ""
    description = f"Variansi Complete Future Lifetime {term_desc}(Tabel, Frac: {assumption_fractional.upper()}), Usia {age}"
    if table_to_use.has_gender_columns: description += f", Gender {effective_gender.capitalize()}"
    return ActuarialResult(value, formula_str, description)