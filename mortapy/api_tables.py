# mortapy/api_tables.py
import os
import math
from typing import Literal, Optional, Any, Callable
from .tables.base import MortalityTable
from .core_calculator import ActuarialCalculator
from .result import ActuarialResult

# --- Logika Path untuk DEFAULT_TABLE_PATH ---
CURRENT_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TABLE_PATH_IN_PACKAGE = os.path.join(CURRENT_MODULE_DIR, 'tables', 'tabel_mortalita_penduduk_indonesia_2023.csv')
DEFAULT_TABLE_PATH_FROM_ROOT = os.path.join(os.getcwd(), "mortapy", "tables", "tabel_mortalita_penduduk_indonesia_2023.csv")

DEFAULT_TABLE_PATH = DEFAULT_TABLE_PATH_IN_PACKAGE
if not os.path.exists(DEFAULT_TABLE_PATH):
    if os.path.exists(DEFAULT_TABLE_PATH_FROM_ROOT):
        DEFAULT_TABLE_PATH = DEFAULT_TABLE_PATH_FROM_ROOT

_DEFAULT_TABLE_INSTANCE: Optional[MortalityTable] = None

def _get_default_table() -> MortalityTable:
    """
    Memuat tabel mortalita default hanya sekali (lazy loading).
    """
    global _DEFAULT_TABLE_INSTANCE
    if _DEFAULT_TABLE_INSTANCE is None:
        path_to_load = DEFAULT_TABLE_PATH
        if not os.path.exists(path_to_load):
            # Upaya fallback jika path awal tidak ditemukan
            alt_paths = [
                os.path.join("mortapy", "tables", "tabel_mortalita_penduduk_indonesia_2023.csv"),
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mortapy", "tables", "tabel_mortalita_penduduk_indonesia_2023.csv")
            ]
            path_found = False
            for alt_path in alt_paths:
                if alt_path and os.path.exists(alt_path):
                    path_to_load = alt_path
                    path_found = True
                    break
            if not path_found:
                checked_paths_str = "\n - ".join(filter(None, [DEFAULT_TABLE_PATH] + alt_paths))
                raise FileNotFoundError(
                    f"Tabel mortalita default tidak ditemukan. Path yang sudah dicek:\n - {checked_paths_str}"
                )
        _DEFAULT_TABLE_INSTANCE = MortalityTable(ultimate_file_path=path_to_load)
    return _DEFAULT_TABLE_INSTANCE

def load_default_table() -> MortalityTable:
    """
    Memuat dan mengembalikan instance tabel mortalita default Indonesia.
    """
    return _get_default_table()

def _validate_table_and_gender(table: MortalityTable, gender: Optional[Literal['pria', 'wanita']]) -> Literal['pria', 'wanita']:
    """
    Validasi apakah gender yang diberikan sesuai dengan tipe tabel mortalita.
    """
    if table.has_gender_columns_ultimate:
        if gender not in ['pria', 'wanita']:
            # <<< PERBAIKAN PESAN ERROR DI SINI >>>
            raise ValueError("Parameter 'gender' ('pria' atau 'wanita') wajib untuk tabel berbasis gender ini.")
        return gender
    elif table.is_unisex_ultimate:
        return 'pria'
    else:
        raise ValueError("Tabel mortalita ultima tidak memiliki kolom gender yang valid atau kolom 'qx' unisex.")

def _build_latex_subscript_select(
    age_display: Any,
    gender_val: Optional[str] = None,
    is_gender_table: bool = False,
    n_temp: Optional[int] = None,
    is_select: bool = False,
    age_at_selection_val: Optional[int] = None,
    duration_selected_val: Optional[int] = None,
    is_complete_expectation: bool = False
    ) -> str:
    """Helper untuk membangun subscript LaTeX yang konsisten."""
    subscript = ""
    base_age_part = ""
    if is_select and age_at_selection_val is not None:
        base_age_part = f"[{age_at_selection_val}]"
        if duration_selected_val is not None and duration_selected_val > 0:
            base_age_part += f"+{duration_selected_val}"
    else:
        base_age_part = str(age_display)
    subscript_parts = [base_age_part]
    if n_temp is not None:
        subscript_parts.append(rf":\overline{{{n_temp}}}|")
    if is_gender_table and gender_val:
        if base_age_part or n_temp is not None :
             subscript_parts.append(rf"; \text{{{gender_val.lower()}}}")
        else:
             subscript_parts.append(rf"\text{{{gender_val.lower()}}}")
    return "".join(subscript_parts)

def nsp_whole_life_from_table(
    age: int,
    interest_rate: float,
    gender: Literal['pria', 'wanita'],
    mortality_table: Optional[MortalityTable] = None,
    age_at_selection: Optional[int] = None,
    initial_duration_selected: int = 0
) -> ActuarialResult:
    """
    Menghitung Premi Tunggal Bersih (A) untuk asuransi jiwa seumur hidup
    berdasarkan tabel mortalita (bisa seleksi/ultima).
    """
    table_to_use = mortality_table if mortality_table else _get_default_table()
    effective_gender = _validate_table_and_gender(table_to_use, gender)
    calc = ActuarialCalculator(interest_rate=interest_rate)
    value = calc.nsp_whole_life_from_table(
        age, effective_gender, table_to_use,
        age_at_selection, initial_duration_selected
    )
    is_select_notation = age_at_selection is not None
    base_for_sub = age_at_selection if is_select_notation else age
    duration_for_sub = initial_duration_selected if is_select_notation else None
    subscript = _build_latex_subscript_select(
        base_for_sub, effective_gender, table_to_use.has_gender_columns_ultimate,
        is_select=is_select_notation,
        age_at_selection_val=age_at_selection,
        duration_selected_val=duration_for_sub
    )
    formula_str = rf"A_{{{subscript}}}"
    desc_age_part = f"[{age_at_selection}]" if is_select_notation and age_at_selection is not None else str(age)
    if is_select_notation and initial_duration_selected > 0: desc_age_part += f"+{initial_duration_selected}"
    description = f"NSP Jiwa Seumur Hidup (Tabel), Usia {desc_age_part}"
    if table_to_use.has_gender_columns_ultimate: description += f", Gender {effective_gender.capitalize()}"
    if is_select_notation: description += " (Status Seleksi)"
    return ActuarialResult(value, formula_str, description)

def pv_annuity_due_whole_life_from_table(
    age: int,
    interest_rate: float,
    gender: Literal['pria', 'wanita'],
    mortality_table: Optional[MortalityTable] = None,
    age_at_selection: Optional[int] = None,
    initial_duration_selected: int = 0
) -> ActuarialResult:
    """
    Menghitung PV Anuitas Jiwa Seumur Hidup Awal Tahun (ä)
    berdasarkan tabel mortalita (bisa seleksi/ultima).
    """
    table_to_use = mortality_table if mortality_table else _get_default_table()
    effective_gender = _validate_table_and_gender(table_to_use, gender)
    calc = ActuarialCalculator(interest_rate=interest_rate)
    value = calc.pv_annuity_due_whole_life_from_table(
        age, effective_gender, table_to_use,
        age_at_selection, initial_duration_selected
    )
    is_select_notation = age_at_selection is not None
    base_for_sub = age_at_selection if is_select_notation else age
    duration_for_sub = initial_duration_selected if is_select_notation else None
    subscript = _build_latex_subscript_select(
        base_for_sub, effective_gender, table_to_use.has_gender_columns_ultimate,
        is_select=is_select_notation,
        age_at_selection_val=age_at_selection,
        duration_selected_val=duration_for_sub
    )
    formula_str = rf"\ddot{{a}}_{{{subscript}}}"
    desc_age_part = f"[{age_at_selection}]" if is_select_notation and age_at_selection is not None else str(age)
    if is_select_notation and initial_duration_selected > 0: desc_age_part += f"+{initial_duration_selected}"
    description = f"PV Anuitas Jiwa Seumur Hidup Awal Tahun (Tabel), Usia {desc_age_part}"
    if table_to_use.has_gender_columns_ultimate: description += f", Gender {effective_gender.capitalize()}"
    if is_select_notation: description += " (Status Seleksi)"
    return ActuarialResult(value, formula_str, description)

def survival_probability_from_table(
    age: int,
    n_years: int,
    interest_rate: float,
    gender: Literal['pria', 'wanita'],
    mortality_table: Optional[MortalityTable] = None,
    age_at_selection: Optional[int] = None,
    initial_duration_selected: int = 0
) -> ActuarialResult:
    """
    Menghitung probabilitas hidup _{n}p berdasarkan tabel mortalita.
    """
    if not isinstance(n_years, int) or n_years < 0:
        raise ValueError("Parameter 'n_years' harus integer non-negatif.")
    table_to_use = mortality_table if mortality_table else _get_default_table()
    effective_gender = _validate_table_and_gender(table_to_use, gender)
    calc = ActuarialCalculator(interest_rate=interest_rate)
    value = calc.survival_probability_from_table(
        age, n_years, effective_gender, table_to_use,
        age_at_selection, initial_duration_selected
    )
    is_select_notation = age_at_selection is not None
    base_for_sub = age_at_selection if is_select_notation else age
    duration_for_sub = initial_duration_selected if is_select_notation else None
    subscript = _build_latex_subscript_select(
        base_for_sub, effective_gender, table_to_use.has_gender_columns_ultimate,
        is_select=is_select_notation,
        age_at_selection_val=age_at_selection,
        duration_selected_val=duration_for_sub
    )
    formula_str = rf"{{}}_{{{n_years}}}p_{{{subscript}}}"
    desc_age_part = f"[{age_at_selection}]" if is_select_notation and age_at_selection is not None else str(age)
    if is_select_notation and initial_duration_selected > 0: desc_age_part += f"+{initial_duration_selected}"
    description = f"Probabilitas Hidup {n_years} Tahun (Tabel), Usia Awal {desc_age_part}"
    if table_to_use.has_gender_columns_ultimate: description += f", Gender {effective_gender.capitalize()}"
    if is_select_notation: description += " (Status Seleksi)"
    return ActuarialResult(value, formula_str, description)

def death_probability_from_table(
    age: int,
    n_years: int,
    interest_rate: float,
    gender: Literal['pria', 'wanita'],
    mortality_table: Optional[MortalityTable] = None,
    age_at_selection: Optional[int] = None,
    initial_duration_selected: int = 0
) -> ActuarialResult:
    """
    Menghitung probabilitas kematian _{n}q berdasarkan tabel mortalita.
    """
    if not isinstance(n_years, int) or n_years < 0:
        raise ValueError("Parameter 'n_years' harus integer non-negatif.")
    table_to_use = mortality_table if mortality_table else _get_default_table()
    effective_gender = _validate_table_and_gender(table_to_use, gender)
    calc = ActuarialCalculator(interest_rate=interest_rate)
    value = calc.death_probability_from_table(
        age, n_years, effective_gender, table_to_use,
        age_at_selection, initial_duration_selected
    )
    is_select_notation = age_at_selection is not None
    base_for_sub = age_at_selection if is_select_notation else age
    duration_for_sub = initial_duration_selected if is_select_notation else None
    subscript = _build_latex_subscript_select(
        base_for_sub, effective_gender, table_to_use.has_gender_columns_ultimate,
        is_select=is_select_notation,
        age_at_selection_val=age_at_selection,
        duration_selected_val=duration_for_sub
    )
    formula_str = rf"{{}}_{{{n_years}}}q_{{{subscript}}}"
    desc_age_part = f"[{age_at_selection}]" if is_select_notation and age_at_selection is not None else str(age)
    if is_select_notation and initial_duration_selected > 0: desc_age_part += f"+{initial_duration_selected}"
    description = f"Probabilitas Kematian {n_years} Tahun (Tabel), Usia Awal {desc_age_part}"
    if table_to_use.has_gender_columns_ultimate: description += f", Gender {effective_gender.capitalize()}"
    if is_select_notation: description += " (Status Seleksi)"
    return ActuarialResult(value, formula_str, description)

def deferred_death_probability_from_table(
    age: int,
    deferral_period: int,
    n_years_death: int,
    interest_rate: float,
    gender: Literal['pria', 'wanita'],
    mortality_table: Optional[MortalityTable] = None,
    age_at_selection: Optional[int] = None,
    initial_duration_selected: int = 0
) -> ActuarialResult:
    """
    Menghitung probabilitas kematian ditunda _{t|u}q berdasarkan tabel.
    """
    if not isinstance(deferral_period, int) or deferral_period < 0:
        raise ValueError("Parameter 'deferral_period' harus integer non-negatif.")
    if not isinstance(n_years_death, int) or n_years_death <= 0:
        raise ValueError("Parameter 'n_years_death' harus integer positif.")
    table_to_use = mortality_table if mortality_table else _get_default_table()
    effective_gender = _validate_table_and_gender(table_to_use, gender)
    calc = ActuarialCalculator(interest_rate=interest_rate)
    value = calc.deferred_death_probability_from_table(
        age, deferral_period, n_years_death, effective_gender, table_to_use,
        age_at_selection, initial_duration_selected
    )
    is_select_notation = age_at_selection is not None
    base_for_sub = age_at_selection if is_select_notation else age
    duration_for_sub = initial_duration_selected if is_select_notation else None
    subscript = _build_latex_subscript_select(
        base_for_sub, effective_gender, table_to_use.has_gender_columns_ultimate,
        is_select=is_select_notation,
        age_at_selection_val=age_at_selection,
        duration_selected_val=duration_for_sub
    )
    formula_str = rf"{{}}_{{{deferral_period}|{n_years_death}}}q_{{{subscript}}}"
    desc_age_part = f"[{age_at_selection}]" if is_select_notation and age_at_selection is not None else str(age)
    if is_select_notation and initial_duration_selected > 0: desc_age_part += f"+{initial_duration_selected}"
    description = f"Probabilitas Kematian Ditunda {deferral_period}|{n_years_death} (Tabel), Usia {desc_age_part}"
    if table_to_use.has_gender_columns_ultimate: description += f", Gender {effective_gender.capitalize()}"
    if is_select_notation: description += " (Status Seleksi)"
    return ActuarialResult(value, formula_str, description)

def force_of_mortality_from_table(
    age: int, # Usia bulat awal interval [age, age+1)
    t_offset: float,
    interest_rate: float,
    gender: Literal['pria', 'wanita'],
    mortality_table: Optional[MortalityTable] = None,
    assumption_fractional: Literal['udd', 'cfm'] = 'cfm',
    age_at_selection: Optional[int] = None,
    initial_duration_selected: int = 0 # Durasi seleksi di awal interval 'age'
) -> ActuarialResult:
    """
    Menghitung force of mortality μ_{age+t_offset} dari tabel.
    Parameter `age` adalah usia bulat awal interval, `initial_duration_selected`
    adalah durasi sejak seleksi pada usia `age` tersebut.
    """
    if not (0 <= t_offset < 1):
        raise ValueError("t_offset harus antara 0 (inklusif) dan 1 (eksklusif).")
    table_to_use = mortality_table if mortality_table else _get_default_table()
    effective_gender = _validate_table_and_gender(table_to_use, gender)
    calc = ActuarialCalculator(interest_rate=interest_rate)

    # Parameter duration_at_start_of_year untuk metode core adalah initial_duration_selected
    # karena 'age' di API ini adalah attained_age_at_start_of_year untuk core
    value = calc.force_of_mortality_from_table(
        age, t_offset, effective_gender, table_to_use, assumption_fractional,
        age_at_selection, initial_duration_selected
    )

    # Pembuatan LaTeX untuk μ
    is_select_notation = age_at_selection is not None
    age_display_actual = age + t_offset # Usia aktual dimana FoM dihitung
    
    base_for_mu_sub: str
    if is_select_notation and age_at_selection is not None:
        total_duration_from_selection = initial_duration_selected + t_offset
        base_for_mu_sub = f"[{age_at_selection}]"
        if total_duration_from_selection > 1e-9: # Tampilkan hanya jika ada durasi signifikan
             base_for_mu_sub += f"+{total_duration_from_selection:.2f}".rstrip('0').rstrip('.')
    else:
        base_for_mu_sub = f"{age_display_actual:.2f}".rstrip('0').rstrip('.') if t_offset > 0 else str(age)

    subscript = _build_latex_subscript_select(
        base_for_mu_sub, effective_gender, table_to_use.has_gender_columns_ultimate,
        is_select=False # Notasi [x]+s sudah dihandle di base_for_mu_sub
    )
    formula_str = rf"\mu_{{{subscript}}}"
    
    desc_age_part = f"{age_display_actual:.2f}".rstrip('0').rstrip('.') if t_offset > 0 else str(age)
    description = f"Force of Mortality (Tabel, Interpolasi {assumption_fractional.upper()}), Usia Tepat {desc_age_part}"
    if table_to_use.has_gender_columns_ultimate: description += f", Gender {effective_gender.capitalize()}"
    if is_select_notation: description += f" (Seleksi dari [{age_at_selection}])"
    return ActuarialResult(value, formula_str, description)

def pdf_death_from_table(
    age: int, # Usia awal attained_age_start untuk _t p_x
    t_period: float,
    interest_rate: float,
    gender: Literal['pria', 'wanita'],
    mortality_table: Optional[MortalityTable] = None,
    assumption_fractional: Literal['udd', 'cfm'] = 'cfm',
    age_at_selection: Optional[int] = None,
    initial_duration_selected: int = 0
) -> ActuarialResult:
    """Menghitung PDF kematian f_X(age+t_period) dari tabel."""
    if t_period < 0: raise ValueError("t_period tidak boleh negatif.")
    table_to_use = mortality_table if mortality_table else _get_default_table()
    effective_gender = _validate_table_and_gender(table_to_use, gender)
    calc = ActuarialCalculator(interest_rate=interest_rate)
    value = calc.pdf_death_from_table(
        age, t_period, effective_gender, table_to_use, assumption_fractional,
        age_at_selection, initial_duration_selected
    )

    # _t p_x part
    period_str_tpx = f"{t_period:.2f}".rstrip('0').rstrip('.')
    if t_period == int(t_period): period_str_tpx = str(int(t_period))
    is_select_tpx = age_at_selection is not None
    base_tpx = age_at_selection if is_select_tpx else age
    dur_tpx = initial_duration_selected if is_select_tpx else None
    sub_tpx = _build_latex_subscript_select(
        base_tpx, effective_gender, table_to_use.has_gender_columns_ultimate,
        is_select=is_select_tpx, age_at_selection_val=age_at_selection, duration_selected_val=dur_tpx
    )
    tpx_formula_part = rf"{{}}_{{{period_str_tpx}}}p_{{{sub_tpx}}}"

    # mu_{x+t} part
    age_for_mu_start_of_year = age + int(t_period)
    offset_for_mu = t_period - int(t_period)
    duration_for_mu_start_of_year = initial_duration_selected + int(t_period) if age_at_selection is not None else 0
    
    fom_res = force_of_mortality_from_table(
        age_for_mu_start_of_year, offset_for_mu, interest_rate, effective_gender, table_to_use,
        assumption_fractional, age_at_selection, duration_for_mu_start_of_year
    )
    mu_formula_part = fom_res.formula_latex
    formula_str = rf"{tpx_formula_part} \cdot {mu_formula_part}"

    actual_age_at_death = age + t_period
    desc_age_at_death = f"{actual_age_at_death:.2f}".rstrip('0').rstrip('.') if t_period > 0 or actual_age_at_death != age else str(age)
    desc_age_initial = f"[{age_at_selection}]" if is_select_tpx and age_at_selection is not None else str(age)
    if is_select_tpx and initial_duration_selected > 0: desc_age_initial += f"+{initial_duration_selected}"
    description = f"PDF Kematian Usia Tepat {desc_age_at_death} dari Usia Awal {desc_age_initial} (Tabel, Interpolasi {assumption_fractional.upper()})"
    if table_to_use.has_gender_columns_ultimate: description += f", Gender {effective_gender.capitalize()}"
    if is_select_tpx: description += " (Status Seleksi)"
    return ActuarialResult(value, formula_str, description)


# --- Fungsi Momen Curtate Berbasis Tabel ---
def expected_curtate_future_lifetime_from_table(age: int, interest_rate: float, gender: Literal['pria', 'wanita'], mortality_table: Optional[MortalityTable] = None, n_temp: Optional[int] = None, age_at_selection: Optional[int] = None, initial_duration_selected: int = 0) -> ActuarialResult:
    table_to_use = mortality_table if mortality_table else _get_default_table()
    eff_gender = _validate_table_and_gender(table_to_use, gender); calc = ActuarialCalculator(interest_rate)
    val = calc.ex_curtate_from_table(age, eff_gender, table_to_use, n_temp, age_at_selection, initial_duration_selected)
    is_select = age_at_selection is not None; base_val = age_at_selection if is_select else age
    dur_val = initial_duration_selected if is_select else None
    sub = _build_latex_subscript_select(base_val, eff_gender, table_to_use.has_gender_columns_ultimate, n_temp, is_select, age_at_selection, dur_val)
    f_str = rf"e_{{{sub}}}"; term = f"{n_temp}-tahun temporary " if n_temp else ""
    desc_age = f"[{age_at_selection}]" if is_select and age_at_selection is not None else str(age)
    if is_select and initial_duration_selected > 0: desc_age += f"+{initial_duration_selected}"
    desc = f"Ekspektasi Curtate Future Lifetime {term}(Tabel), Usia {desc_age}"
    if table_to_use.has_gender_columns_ultimate: desc += f", Gender {eff_gender.capitalize()}"
    if is_select: desc += " (Status Seleksi)"
    return ActuarialResult(val, f_str, desc)

def second_moment_curtate_future_lifetime_from_table(age: int, interest_rate: float, gender: Literal['pria', 'wanita'], mortality_table: Optional[MortalityTable] = None, n_temp: Optional[int] = None, age_at_selection: Optional[int] = None, initial_duration_selected: int = 0) -> ActuarialResult:
    table_to_use = mortality_table if mortality_table else _get_default_table()
    eff_gender = _validate_table_and_gender(table_to_use, gender); calc = ActuarialCalculator(interest_rate)
    val = calc.e_sq_curtate_from_table(age, eff_gender, table_to_use, n_temp, age_at_selection, initial_duration_selected)
    is_select = age_at_selection is not None; base_val = age_at_selection if is_select else age
    dur_val = initial_duration_selected if is_select else None
    sub = _build_latex_subscript_select(base_val, eff_gender, table_to_use.has_gender_columns_ultimate, n_temp, is_select, age_at_selection, dur_val)
    f_str = rf"E[K_{{{sub}}}^2]"; term = f"{n_temp}-tahun temporary " if n_temp else ""
    desc_age = f"[{age_at_selection}]" if is_select and age_at_selection is not None else str(age)
    if is_select and initial_duration_selected > 0: desc_age += f"+{initial_duration_selected}"
    desc = f"Momen Kedua Curtate Future Lifetime {term}(Tabel), Usia {desc_age}"
    if table_to_use.has_gender_columns_ultimate: desc += f", Gender {eff_gender.capitalize()}"
    if is_select: desc += " (Status Seleksi)"
    return ActuarialResult(val, f_str, desc)

def variance_curtate_future_lifetime_from_table(age: int, interest_rate: float, gender: Literal['pria', 'wanita'], mortality_table: Optional[MortalityTable] = None, n_temp: Optional[int] = None, age_at_selection: Optional[int] = None, initial_duration_selected: int = 0) -> ActuarialResult:
    table_to_use = mortality_table if mortality_table else _get_default_table()
    eff_gender = _validate_table_and_gender(table_to_use, gender)
    ex_res = expected_curtate_future_lifetime_from_table(age, interest_rate, eff_gender, table_to_use, n_temp, age_at_selection, initial_duration_selected)
    e_sq_res = second_moment_curtate_future_lifetime_from_table(age, interest_rate, eff_gender, table_to_use, n_temp, age_at_selection, initial_duration_selected)
    val = e_sq_res.value - (ex_res.value ** 2)
    is_select = age_at_selection is not None; base_val = age_at_selection if is_select else age
    dur_val = initial_duration_selected if is_select else None
    sub = _build_latex_subscript_select(base_val, eff_gender, table_to_use.has_gender_columns_ultimate, n_temp, is_select, age_at_selection, dur_val)
    f_str = rf"Var[K_{{{sub}}}]"; term = f"{n_temp}-tahun temporary " if n_temp else ""
    desc_age = f"[{age_at_selection}]" if is_select and age_at_selection is not None else str(age)
    if is_select and initial_duration_selected > 0: desc_age += f"+{initial_duration_selected}"
    desc = f"Variansi Curtate Future Lifetime {term}(Tabel), Usia {desc_age}"
    if table_to_use.has_gender_columns_ultimate: desc += f", Gender {eff_gender.capitalize()}"
    if is_select: desc += " (Status Seleksi)"
    return ActuarialResult(val, f_str, desc)

# --- Fungsi Momen Complete Berbasis Tabel ---
def expected_complete_future_lifetime_from_table(age: int, interest_rate: float, gender: Literal['pria', 'wanita'], mortality_table: Optional[MortalityTable] = None, n_temp: Optional[int] = None, assumption_fractional: Literal['udd', 'cfm'] = 'udd', age_at_selection: Optional[int] = None, initial_duration_selected: int = 0) -> ActuarialResult:
    table_to_use = mortality_table if mortality_table else _get_default_table()
    eff_gender = _validate_table_and_gender(table_to_use, gender); calc = ActuarialCalculator(interest_rate)
    val = calc.ex_complete_from_table(age, eff_gender, table_to_use, n_temp, assumption_fractional, age_at_selection, initial_duration_selected)
    is_select = age_at_selection is not None; base_val = age_at_selection if is_select else age
    dur_val = initial_duration_selected if is_select else None
    sub = _build_latex_subscript_select(base_val, eff_gender, table_to_use.has_gender_columns_ultimate, n_temp, is_select, age_at_selection, dur_val, True)
    f_str = rf"\mathring{{e}}_{{{sub}}}"; term = f"{n_temp}-tahun temporary " if n_temp else ""
    desc_age = f"[{age_at_selection}]" if is_select and age_at_selection is not None else str(age)
    if is_select and initial_duration_selected > 0: desc_age += f"+{initial_duration_selected}"
    desc = f"Ekspektasi Complete Future Lifetime {term}(Tabel, Frac: {assumption_fractional.upper()}), Usia {desc_age}"
    if table_to_use.has_gender_columns_ultimate: desc += f", Gender {eff_gender.capitalize()}"
    if is_select: desc += " (Status Seleksi)"
    return ActuarialResult(val, f_str, desc)

def second_moment_complete_future_lifetime_from_table(age: int, interest_rate: float, gender: Literal['pria', 'wanita'], mortality_table: Optional[MortalityTable] = None, n_temp: Optional[int] = None, assumption_fractional: Literal['udd', 'cfm'] = 'udd', age_at_selection: Optional[int] = None, initial_duration_selected: int = 0) -> ActuarialResult:
    table_to_use = mortality_table if mortality_table else _get_default_table()
    eff_gender = _validate_table_and_gender(table_to_use, gender); calc = ActuarialCalculator(interest_rate)
    val = calc.e_sq_complete_from_table(age, eff_gender, table_to_use, n_temp, assumption_fractional, age_at_selection, initial_duration_selected)
    is_select = age_at_selection is not None; base_val = age_at_selection if is_select else age
    dur_val = initial_duration_selected if is_select else None
    sub = _build_latex_subscript_select(base_val, eff_gender, table_to_use.has_gender_columns_ultimate, n_temp, is_select, age_at_selection, dur_val, True)
    f_str = rf"E[T_{{{sub}}}^2]"; term = f"{n_temp}-tahun temporary " if n_temp else ""
    desc_age = f"[{age_at_selection}]" if is_select and age_at_selection is not None else str(age)
    if is_select and initial_duration_selected > 0: desc_age += f"+{initial_duration_selected}"
    desc = f"Momen Kedua Complete Future Lifetime {term}(Tabel, Frac: {assumption_fractional.upper()}), Usia {desc_age}"
    if table_to_use.has_gender_columns_ultimate: desc += f", Gender {eff_gender.capitalize()}"
    if is_select: desc += " (Status Seleksi)"
    return ActuarialResult(val, f_str, desc)

def variance_complete_future_lifetime_from_table(age: int, interest_rate: float, gender: Literal['pria', 'wanita'], mortality_table: Optional[MortalityTable] = None, n_temp: Optional[int] = None, assumption_fractional: Literal['udd', 'cfm'] = 'udd', age_at_selection: Optional[int] = None, initial_duration_selected: int = 0) -> ActuarialResult:
    table_to_use = mortality_table if mortality_table else _get_default_table()
    eff_gender = _validate_table_and_gender(table_to_use, gender)
    ex_circ_res = expected_complete_future_lifetime_from_table(age, interest_rate, eff_gender, table_to_use, n_temp, assumption_fractional, age_at_selection, initial_duration_selected)
    e_sq_circ_res = second_moment_complete_future_lifetime_from_table(age, interest_rate, eff_gender, table_to_use, n_temp, assumption_fractional, age_at_selection, initial_duration_selected)
    val = e_sq_circ_res.value - (ex_circ_res.value ** 2)
    is_select = age_at_selection is not None; base_val = age_at_selection if is_select else age
    dur_val = initial_duration_selected if is_select else None
    sub = _build_latex_subscript_select(base_val, eff_gender, table_to_use.has_gender_columns_ultimate, n_temp, is_select, age_at_selection, dur_val, True)
    f_str = rf"Var[T_{{{sub}}}]"; term = f"{n_temp}-thn temp " if n_temp else ""
    desc_age = f"[{age_at_selection}]" if is_select and age_at_selection is not None else str(age)
    if is_select and initial_duration_selected > 0: desc_age += f"+{initial_duration_selected}"
    desc = f"Variansi Complete Future Lifetime {term}(Tabel, Frac: {assumption_fractional.upper()}), Usia {desc_age}"
    if table_to_use.has_gender_columns_ultimate: desc += f", Gender {eff_gender.capitalize()}"
    if is_select: desc += " (Status Seleksi)"
    return ActuarialResult(val, f_str, desc)