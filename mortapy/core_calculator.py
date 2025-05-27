# mortapy/core_calculator.py
from typing import Literal, Optional, Callable
from .tables.base import MortalityTable
import math

class ActuarialCalculator:
    """
    Kelas inti yang melakukan perhitungan aktuaria berdasarkan suku bunga
    dan sumber data mortalita yang diberikan (tabel atau fungsi asumsi).
    """
    def __init__(self, interest_rate: float):
        """
        Inisialisasi kalkulator dengan suku bunga.

        Args:
            interest_rate (float): Tingkat suku bunga efektif per periode (misal: 0.05 untuk 5%).
        """
        self.interest_rate: float = interest_rate
        self.v: float = 1 / (1 + self.interest_rate)

    # === Metode yang menggunakan MortalityTable ===
    def _get_qx_from_table(self, age: int, gender: Literal['pria', 'wanita'], table: MortalityTable) -> float:
        """Mengambil q_x dari objek MortalityTable, menangani batas usia tabel."""
        if age < 0:
            return 1.0 
        return table.qx(age, gender)

    def _get_px_from_table(self, age: int, gender: Literal['pria', 'wanita'], table: MortalityTable) -> float:
        """Mengambil p_x dari objek MortalityTable, menangani batas usia tabel."""
        if age < 0:
            return 0.0
        return table.px(age, gender)

    def survival_probability_from_table(self, age: int, n_years: int, gender: Literal['pria', 'wanita'], table: MortalityTable) -> float:
        """
        Menghitung probabilitas _n p_x menggunakan MortalityTable untuk periode bulat.
        """
        if n_years < 0:
            raise ValueError("Jumlah tahun (n_years) tidak boleh negatif.")
        if n_years == 0:
            return 1.0
        
        current_survival_prob: float = 1.0
        for i in range(n_years):
            current_age: int = age + i
            if current_survival_prob == 0.0:
                break 
            current_survival_prob *= self._get_px_from_table(current_age, gender, table)
        return current_survival_prob
    
    def death_probability_from_table(self, age: int, n_years: int, gender: Literal['pria', 'wanita'], table: MortalityTable) -> float:
        """Menghitung _n q_x menggunakan MortalityTable (untuk periode bulat n)."""
        return 1.0 - self.survival_probability_from_table(age, n_years, gender, table)

    def deferred_death_probability_from_table(self, age: int, deferral_period: int, n_years_death: int, gender: Literal['pria', 'wanita'], table: MortalityTable) -> float:
        """Menghitung _{deferral_period}|{n_years_death} q_x menggunakan MortalityTable (untuk periode bulat)."""
        prob_survive_deferral = self.survival_probability_from_table(age, deferral_period, gender, table)
        prob_die_within_n_after_deferral = self.death_probability_from_table(age + deferral_period, n_years_death, gender, table)
        return prob_survive_deferral * prob_die_within_n_after_deferral

    def nsp_whole_life_from_table(self, age: int, gender: Literal['pria', 'wanita'], table: MortalityTable) -> float:
        """Menghitung A_x menggunakan MortalityTable."""
        present_value_sum: float = 0.0
        for k in range(table.max_age - age): 
            age_at_k: int = age + k
            
            prob_survive_k_years: float = self.survival_probability_from_table(age, k, gender, table)
            if prob_survive_k_years == 0.0 and k > 0:
                break
            prob_die_next_year: float = self._get_qx_from_table(age_at_k, gender, table)
            
            discounted_benefit: float = (self.v ** (k + 1)) * prob_survive_k_years * prob_die_next_year
            present_value_sum += discounted_benefit
        return present_value_sum

    def pv_annuity_due_whole_life_from_table(self, age: int, gender: Literal['pria', 'wanita'], table: MortalityTable) -> float:
        """Menghitung ä_x menggunakan MortalityTable."""
        present_value_sum: float = 0.0
        for k in range(table.max_age - age + 1):
            prob_survive_k_years: float = self.survival_probability_from_table(age, k, gender, table)
            if prob_survive_k_years == 0.0 and k > 0:
                break
            discounted_payment: float = (self.v ** k) * prob_survive_k_years
            present_value_sum += discounted_payment
        return present_value_sum

    # === Metode untuk Asumsi Distribusi Murni ===
    def survival_probability_from_assumption(
        self, 
        age: int, 
        n_years: float, # Periode bisa float
        px_function_yearly: Callable[[int], float], 
        omega: int,
        assumption_type_for_fractional: Optional[Literal['udd', 'cfm']] = 'cfm'
    ) -> float:
        """
        Menghitung probabilitas _t p_x menggunakan fungsi p_x(usia_bulat) dari asumsi.
        Menggunakan UDD atau CFM untuk bagian fraksional jika n_years adalah float.
        """
        if n_years < 0:
            raise ValueError("Jumlah tahun (n_years) tidak boleh negatif.")
        if n_years == 0:
            return 1.0

        integer_part = int(n_years)
        fractional_part = n_years - integer_part
        
        current_survival_prob: float = 1.0
        for i in range(integer_part):
            current_age_loop: int = age + i
            if current_age_loop >= omega:
                current_survival_prob = 0.0
                break
            current_survival_prob *= px_function_yearly(current_age_loop)
        
        if fractional_part > 0 and current_survival_prob > 0.0:
            age_after_integer_part: int = age + integer_part
            if age_after_integer_part >= omega:
                current_survival_prob = 0.0
            else:
                px_for_fractional_base = px_function_yearly(age_after_integer_part)
                if assumption_type_for_fractional == 'cfm':
                    current_survival_prob *= (px_for_fractional_base ** fractional_part)
                elif assumption_type_for_fractional == 'udd':
                    qx_for_fractional_base = 1.0 - px_for_fractional_base
                    current_survival_prob *= (1.0 - fractional_part * qx_for_fractional_base)
                else:
                    raise ValueError("Asumsi fraksional tidak valid. Pilih 'udd' atau 'cfm'.")
        return current_survival_prob

    def death_probability_from_assumption(
        self, 
        age: int, 
        n_years: float, 
        px_function_yearly: Callable[[int], float], 
        omega: int, 
        assumption_type_for_fractional: Optional[Literal['udd', 'cfm']] = 'cfm'
    ) -> float:
        """Menghitung _n q_x menggunakan fungsi p_x dari asumsi."""
        return 1.0 - self.survival_probability_from_assumption(age, n_years, px_function_yearly, omega, assumption_type_for_fractional)

    def deferred_death_probability_from_assumption(
        self, 
        age: int, 
        deferral_period: float, 
        n_years_death: float, 
        px_function_yearly: Callable[[int], float], 
        omega: int, 
        assumption_type_for_fractional: Optional[Literal['udd', 'cfm']] = 'cfm'
    ) -> float:
        """Menghitung _{deferral_period}|{n_years_death} q_x menggunakan fungsi p_x dari asumsi."""
        prob_survive_deferral = self.survival_probability_from_assumption(
            age, deferral_period, px_function_yearly, omega, assumption_type_for_fractional
        )
        
        # Untuk q_{x+t} selama u tahun, kita perlu p_{x+t} selama u tahun.
        # Ini berarti survival_probability_from_assumption(age + deferral_period, n_years_death, ...)
        # Namun, jika deferral_period adalah float, age + deferral_period akan menjadi float.
        # Metode survival_probability_from_assumption mengharapkan 'age' integer (usia bulat awal).
        # Ini memerlukan penanganan usia awal non-bulat yang lebih canggih atau kita asumsikan
        # bahwa px_function_yearly bisa diinterpretasikan pada usia bulat terdekat.
        # UNTUK SEKARANG, ASUMSIKAN DEFERRAL_PERIOD ADALAH INTEGER UNTUK KESEDERHANAAN
        # ATAU px_function menangani usia non-bulat secara implisit (misal, jika dari mu kontinu).
        
        # Jika px_function hanya untuk usia bulat dan deferral_period adalah float:
        # Kita perlu menghitung survival dari usia bulat (age + int(deferral_period))
        # untuk sisa deferral_period (deferral_period - int(deferral_period)) dan
        # kemudian untuk n_years_death. Ini menjadi lebih kompleks.
        
        # SOLUSI SEMENTARA: Gunakan formula _tp_x - _{t+u}p_x
        prob_survive_total_period = self.survival_probability_from_assumption(
            age, deferral_period + n_years_death, px_function_yearly, omega, assumption_type_for_fractional
        )
        return prob_survive_deferral - prob_survive_total_period


    def nsp_whole_life_from_assumption(self, age: int, qx_function: Callable[[int], float], px_function: Callable[[int], float], omega: int) -> float:
        """Menghitung A_x menggunakan fungsi q_x dan p_x tahunan dari asumsi."""
        present_value_sum: float = 0.0
        for k in range(omega - age): 
            age_at_k: int = age + k
            
            prob_survive_k_years: float = self.survival_probability_from_assumption(age, float(k), px_function, omega, 'cfm') # Periode k adalah integer
            if prob_survive_k_years == 0.0 and k > 0:
                break
            prob_die_next_year: float = qx_function(age_at_k)
            
            discounted_benefit: float = (self.v ** (k + 1)) * prob_survive_k_years * prob_die_next_year
            present_value_sum += discounted_benefit
        return present_value_sum

    def pv_annuity_due_whole_life_from_assumption(self, age: int, px_function: Callable[[int], float], omega: int) -> float:
        """Menghitung ä_x menggunakan fungsi p_x tahunan dari asumsi."""
        present_value_sum: float = 0.0
        for k in range(omega - age + 1):
            prob_survive_k_years: float = self.survival_probability_from_assumption(age, float(k), px_function, omega, 'cfm') # Periode k adalah integer
            if prob_survive_k_years == 0.0 and k > 0:
                break
            discounted_payment: float = (self.v ** k) * prob_survive_k_years
            present_value_sum += discounted_payment
        return present_value_sum