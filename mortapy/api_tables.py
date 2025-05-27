# mortapy/api_tables.py
import os
import math # Pastikan math diimpor
from typing import Literal, Optional
from .tables.base import MortalityTable
from .core_calculator import ActuarialCalculator
from .result import ActuarialResult

# Logika path untuk DEFAULT_TABLE_PATH
# Mencoba beberapa kandidat path agar lebih robust
CURRENT_DIR_OF_API_TABLES = os.path.dirname(__file__) # Direktori tempat api_tables.py berada
PATH_CANDIDATES = [
    os.path.join(CURRENT_DIR_OF_API_TABLES, 'tables', 'tabel_mortalita_penduduk_indonesia_2023.csv'),
    os.path.join(os.path.dirname(CURRENT_DIR_OF_API_TABLES), "tables", "tabel_mortalita_penduduk_indonesia_2023.csv"), # Jika tables adalah saudara dari paket mortapy
    os.path.join("mortapy", "tables", "tabel_mortalita_penduduk_indonesia_2023.csv") # Jika dijalankan dari root proyek
]
DEFAULT_TABLE_PATH = None
for path_candidate in PATH_CANDIDATES:
    if os.path.exists(path_candidate):
        DEFAULT_TABLE_PATH = path_candidate
        break
if DEFAULT_TABLE_PATH is None:
    # Fallback jika semua path di atas tidak ditemukan (misalnya, struktur sangat berbeda)
    # Ini mungkin akan error saat _get_default_table() dipanggil jika path ini juga salah.
    DEFAULT_TABLE_PATH = "mortapy/tables/tabel_mortalita_penduduk_indonesia_2023.csv"


_DEFAULT_TABLE_INSTANCE: Optional[MortalityTable] = None

def _get_default_table() -> MortalityTable:
    """Memuat tabel mortalita default hanya sekali (lazy loading)."""
    global _DEFAULT_TABLE_INSTANCE
    if _DEFAULT_TABLE_INSTANCE is None:
        if not os.path.exists(DEFAULT_TABLE_PATH):
             # Jika path default utama tidak ditemukan, coba path alternatif yang mungkin saat testing
             # Ini adalah path relatif dari root proyek jika 'pytest' dijalankan dari sana
            alt_path = os.path.join("mortapy", "tables", "tabel_mortalita_penduduk_indonesia_2023.csv")
            if os.path.exists(alt_path):
                 _DEFAULT_TABLE_INSTANCE = MortalityTable(alt_path)
            else:
                raise FileNotFoundError(
                    f"Tabel mortalita default tidak ditemukan. Path utama yang dicek: '{DEFAULT_TABLE_PATH}', Path alternatif: '{alt_path}'"
                )
        else:
            _DEFAULT_TABLE_INSTANCE = MortalityTable(DEFAULT_TABLE_PATH)
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
        # Untuk tabel unisex, gender yang diberikan (jika ada) akan diabaikan oleh metode qx/px di MortalityTable.
        # Kita bisa default ke 'pria' sebagai placeholder, tapi itu tidak akan digunakan jika tabelnya unisex.
        return 'pria' 
    else:
        # Ini seharusnya tidak terjadi jika konstruktor MortalityTable sudah benar
        raise ValueError("Tabel mortalita tidak memiliki kolom gender yang valid atau kolom 'qx' unisex.")

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
    
    formula_str = rf"A_{{{age}"
    if table_to_use.has_gender_columns:
        formula_str += rf"; \text{{{effective_gender.lower()}}}" # DENGAN SPASI SETELAH ;
    formula_str += r"}"
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
        
    formula_str = rf"\ddot{{a}}_{{{age}"
    if table_to_use.has_gender_columns:
        formula_str += rf"; \text{{{effective_gender.lower()}}}" # DENGAN SPASI SETELAH ;
    formula_str += r"}"
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
    
    formula_str = rf"{{}}_{{{n_years}}}p_{{{age}"
    if table_to_use.has_gender_columns:
        formula_str += rf"; \text{{{effective_gender.lower()}}}" # DENGAN SPASI SETELAH ;
    formula_str += r"}"
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
    
    formula_str = rf"{{}}_{{{n_years}}}q_{{{age}"
    if table_to_use.has_gender_columns:
        formula_str += rf"; \text{{{effective_gender.lower()}}}" # DENGAN SPASI SETELAH ;
    formula_str += r"}"
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
    
    formula_str = rf"{{}}_{{{deferral_period}|{n_years_death}}}q_{{{age}"
    if table_to_use.has_gender_columns:
        formula_str += rf"; \text{{{effective_gender.lower()}}}" # DENGAN SPASI SETELAH ;
    formula_str += r"}"
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

    age_display = f"{age}"
    if t_offset > 0:
      age_display += f"+{t_offset:.2f}".rstrip('0').rstrip('.')

    formula_str = rf"\mu_{{{age_display}"
    if table_to_use.has_gender_columns:
        formula_str += rf"; \text{{{effective_gender.lower()}}}" # DENGAN SPASI SETELAH ;
    formula_str += r"}}" # Dua kurung kurawal penutup
    description = f"Force of Mortality (Tabel, Interpolasi {assumption_desc_detail}), Usia Tepat {age_display}"
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
    
    integer_part_t = int(t_period)
    fractional_part_t = t_period - integer_part_t
    
    # Hitung _t p_x (tpx_value)
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

    # Dapatkan objek ActuarialResult untuk μ_{age+t_period}
    # Usia bulat untuk mu adalah 'age + integer_part_t'
    # dan t_offset untuk mu adalah 'fractional_part_t'
    fom_res_obj = force_of_mortality_from_table(
        age=(age + integer_part_t),
        t_offset=fractional_part_t,
        interest_rate=interest_rate, 
        gender=effective_gender,
        mortality_table=table_to_use,
        assumption_fractional=assumption_fractional
    )
    mu_value_at_time_t = fom_res_obj.value
    mu_formula_part = fom_res_obj.formula_latex # Ambil formula LaTeX untuk mu

    value = tpx_value * mu_value_at_time_t
    
    # Buat formula LaTeX untuk _t p_x
    period_str_for_tpx = f"{t_period:.2f}" # Selalu .2f untuk konsistensi
    tpx_formula_part = rf"{{}}_{{{period_str_for_tpx}}}p_{{{age}"
    if table_to_use.has_gender_columns: 
        tpx_formula_part += rf"; \text{{{effective_gender.lower()}}}" # DENGAN SPASI
    tpx_formula_part += r"}"
    
    formula_str = rf"{tpx_formula_part} \cdot {mu_formula_part}"
    
    # Untuk deskripsi
    age_display_for_desc = f"{age}"
    if t_period > 0:
        temp_period_str_desc = f"{t_period:.2f}".rstrip('0').rstrip('.')
        age_display_for_desc += f"+{temp_period_str_desc}"
        
    description = f"PDF Kematian pada Usia Tepat {age_display_for_desc} (Tabel, Interpolasi {assumption_fractional})"
    if table_to_use.has_gender_columns:
        description += f", Gender {effective_gender.capitalize()}"
    return ActuarialResult(value, formula_str, description)