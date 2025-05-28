# mortapy/api_tables.py
import os  
import math
from typing import Literal, Optional, Any, Callable
from .tables.base import MortalityTable
from .core_calculator import ActuarialCalculator
from .result import ActuarialResult

_DEFAULT_TABLE_INSTANCE: Optional[MortalityTable] = None

def _get_default_table() -> MortalityTable:
    """
    Memuat tabel mortalita default hanya sekali (lazy loading).
    Logika path dipusatkan di sini untuk memastikan 'os' terdefinisi.
    """
    global _DEFAULT_TABLE_INSTANCE
    if _DEFAULT_TABLE_INSTANCE is None:
        # Definisikan kandidat path di dalam fungsi agar 'os' pasti sudah terimpor
        current_module_dir = os.path.dirname(__file__)
        
        # Kandidat path berdasarkan lokasi modul ini
        path_in_package = os.path.join(current_module_dir, 'tables', 'tabel_mortalita_penduduk_indonesia_2023.csv')
        
        # Kandidat path jika skrip dijalankan dari root proyek (misal: E:\mortapy)
        # dan struktur paketnya adalah mortapy/tables/...
        path_from_project_root_standard = os.path.join("mortapy", "tables", "tabel_mortalita_penduduk_indonesia_2023.csv")
        
        # Kandidat path jika CWD adalah root proyek (lebih eksplisit)
        path_from_cwd_as_project_root = os.path.join(os.getcwd(), "mortapy", "tables", "tabel_mortalita_penduduk_indonesia_2023.csv")

        # Kandidat path jika CWD adalah paket mortapy/mortapy (misal: E:\mortapy\mortapy)
        path_from_cwd_as_package_root = os.path.join(os.getcwd(), "tables", "tabel_mortalita_penduduk_indonesia_2023.csv")

        # Path untuk GitHub Actions
        path_github_actions = ""
        if "GITHUB_WORKSPACE" in os.environ:
            path_github_actions = os.path.join(os.environ["GITHUB_WORKSPACE"], "mortapy", "tables", "tabel_mortalita_penduduk_indonesia_2023.csv")

        paths_to_try = [
            path_in_package,
            path_from_project_root_standard, # Seringkali sama dengan path_from_cwd_as_project_root
            path_from_cwd_as_project_root,
            path_from_cwd_as_package_root,
            path_github_actions
        ]
        
        path_to_load = None
        for p_try in paths_to_try:
            if p_try and os.path.exists(p_try): # Cek p_try tidak kosong sebelum os.path.exists
                path_to_load = p_try
                break
        
        if path_to_load is None:
            # Fallback jika semua path di atas tidak ditemukan
            fallback_path = "mortapy/tables/tabel_mortalita_penduduk_indonesia_2023.csv" # Ini asumsi CWD = root proyek
            if not os.path.exists(fallback_path):
                 # Path absolut jika dijalankan dari folder examples (../mortapy/tables/...)
                fallback_path_from_examples = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(current_module_dir)), 'examples', '..', 'mortapy', 'tables', 'tabel_mortalita_penduduk_indonesia_2023.csv'))
                if os.path.exists(fallback_path_from_examples):
                    path_to_load = fallback_path_from_examples
                else:
                    checked_paths = "\n - ".join(filter(None, paths_to_try + [fallback_path, fallback_path_from_examples]))
                    raise FileNotFoundError(
                        f"Tabel mortalita default tidak ditemukan. Path yang sudah dicek:\n - {checked_paths}"
                    )
            else:
                path_to_load = fallback_path

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
        if gender is not None:
            pass 
        return 'pria' 
    else:
        raise ValueError("Tabel mortalita tidak memiliki kolom gender yang valid atau kolom 'qx' unisex.")

def _build_latex_subscript(base_val: Any, gender_val: Optional[str] = None, is_gender_table: bool = False, n_temp: Optional[int] = None) -> str:
    """Helper untuk membangun subscript LaTeX yang konsisten."""
    subscript = str(base_val)
    if n_temp is not None:
        subscript += rf":\overline{{{n_temp}}}|" 
    if is_gender_table and gender_val:
        subscript += rf"; \text{{{gender_val.lower()}}}" 
    return subscript

def nsp_whole_life_from_table(
    age: int,
    interest_rate: float,
    gender: Literal['pria', 'wanita'],
    mortality_table: Optional[MortalityTable] = None
) -> ActuarialResult:
    """
    Menghitung Premi Tunggal Bersih (A_x) untuk asuransi jiwa seumur hidup
    berdasarkan tabel mortalita.
    """
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
    """
    Menghitung nilai sekarang dari anuitas jiwa seumur hidup awal tahun (ä_x)
    berdasarkan tabel mortalita.
    """
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
    """
    Menghitung probabilitas hidup _{n}p_{x} untuk periode bulat n tahun
    berdasarkan tabel mortalita.
    """
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
    """
    Menghitung probabilitas kematian _{n}q_{x} untuk periode bulat n tahun
    berdasarkan tabel mortalita.
    """
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
    """
    Menghitung probabilitas kematian ditunda _{t|u}q_x untuk periode bulat
    berdasarkan tabel mortalita.
    """
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
    """
    Menghitung force of mortality (μ_{age+t_offset}) berdasarkan tabel mortalita
    dengan asumsi UDD atau CFM untuk interpolasi dalam setahun.
    """
    if not (0 <= t_offset < 1):
        raise ValueError("t_offset harus antara 0 (inklusif) dan 1 (eksklusif).")
    table_to_use = mortality_table if mortality_table else _get_default_table()
    effective_gender = _validate_table_and_gender(table_to_use, gender)
    calc = ActuarialCalculator(interest_rate=interest_rate)
    value = calc.force_of_mortality_from_table(age, t_offset, effective_gender, table_to_use, assumption_fractional)
    
    age_display_raw = age + t_offset
    age_display_str = f"{age_display_raw:.2f}".rstrip('0').rstrip('.') if t_offset > 0 else str(age)
    subscript = _build_latex_subscript(age_display_str, effective_gender, table_to_use.has_gender_columns)
    formula_str = rf"\mu_{{{subscript}}}"
    description = f"Force of Mortality (Tabel, Interpolasi {assumption_fractional.upper()}), Usia Tepat {age_display_str}"
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
    """
    Menghitung PDF kematian f_X(age+t_period) = _{t_period}p_{age} * μ_{age+t_period}
    berdasarkan tabel mortalita dan asumsi interpolasi.
    """
    if t_period < 0:
        raise ValueError("t_period tidak boleh negatif.")
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
    if table_to_use.has_gender_columns:
        description += f", Gender {effective_gender.capitalize()}"
    return ActuarialResult(value, formula_str, description)

def expected_curtate_future_lifetime_from_table(
    age: int,
    interest_rate: float, 
    gender: Literal['pria', 'wanita'],
    mortality_table: Optional[MortalityTable] = None,
    n_temp: Optional[int] = None 
) -> ActuarialResult:
    table_to_use = mortality_table if mortality_table else _get_default_table()
    effective_gender = _validate_table_and_gender(table_to_use, gender)
    calc = ActuarialCalculator(interest_rate=interest_rate)
    value = calc.ex_curtate_from_table(age, effective_gender, table_to_use, n_temp)
    subscript_content = _build_latex_subscript(age, effective_gender, table_to_use.has_gender_columns, n_temp=n_temp)
    formula_str = rf"e_{{{subscript_content}}}"
    term_desc = f"{n_temp}-tahun temporary " if n_temp is not None else ""
    description = f"Ekspektasi Curtate Future Lifetime {term_desc}(Tabel), Usia {age}"
    if table_to_use.has_gender_columns:
        description += f", Gender {effective_gender.capitalize()}"
    return ActuarialResult(value, formula_str, description)

def second_moment_curtate_future_lifetime_from_table(
    age: int,
    interest_rate: float, 
    gender: Literal['pria', 'wanita'],
    mortality_table: Optional[MortalityTable] = None,
    n_temp: Optional[int] = None 
) -> ActuarialResult:
    table_to_use = mortality_table if mortality_table else _get_default_table()
    effective_gender = _validate_table_and_gender(table_to_use, gender)
    calc = ActuarialCalculator(interest_rate=interest_rate)
    value = calc.e_sq_curtate_from_table(age, effective_gender, table_to_use, n_temp)
    subscript_content = _build_latex_subscript(age, effective_gender, table_to_use.has_gender_columns, n_temp=n_temp)
    formula_str = rf"E[K_{{{subscript_content}}}^2]"
    term_desc = f"{n_temp}-tahun temporary " if n_temp is not None else ""
    description = f"Momen Kedua Curtate Future Lifetime {term_desc}(Tabel), Usia {age}"
    if table_to_use.has_gender_columns:
        description += f", Gender {effective_gender.capitalize()}"
    return ActuarialResult(value, formula_str, description)

def variance_curtate_future_lifetime_from_table(
    age: int,
    interest_rate: float,
    gender: Literal['pria', 'wanita'],
    mortality_table: Optional[MortalityTable] = None,
    n_temp: Optional[int] = None
) -> ActuarialResult:
    table_to_use = mortality_table if mortality_table else _get_default_table() 
    effective_gender = _validate_table_and_gender(table_to_use, gender)
    ex_result = expected_curtate_future_lifetime_from_table(age, interest_rate, effective_gender, mortality_table, n_temp)
    e_sq_result = second_moment_curtate_future_lifetime_from_table(age, interest_rate, effective_gender, mortality_table, n_temp)
    value = e_sq_result.value - (ex_result.value ** 2)
    subscript_content = _build_latex_subscript(age, effective_gender, table_to_use.has_gender_columns, n_temp=n_temp)
    formula_str = rf"Var[K_{{{subscript_content}}}]"
    term_desc = f"{n_temp}-tahun temporary " if n_temp is not None else ""
    description = f"Variansi Curtate Future Lifetime {term_desc}(Tabel), Usia {age}"
    if table_to_use.has_gender_columns:
        description += f", Gender {effective_gender.capitalize()}"
    return ActuarialResult(value, formula_str, description)