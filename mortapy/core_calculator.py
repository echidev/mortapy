# mortapy/core_calculator.py
from typing import Literal, Optional, Callable, List # <<< TAMBAHKAN 'List' DI SINI
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
        if age < 0: return 1.0 
        return table.qx(age, gender)

    def _get_px_from_table(self, age: int, gender: Literal['pria', 'wanita'], table: MortalityTable) -> float:
        if age < 0: return 0.0
        return table.px(age, gender)

    def survival_probability_from_table(self, age: int, n_years: int, gender: Literal['pria', 'wanita'], table: MortalityTable) -> float:
        if n_years < 0: raise ValueError("Jumlah tahun (n_years) tidak boleh negatif.")
        if n_years == 0: return 1.0
        current_survival_prob: float = 1.0
        for i in range(n_years):
            current_age: int = age + i
            if current_survival_prob == 0.0: break 
            current_survival_prob *= self._get_px_from_table(current_age, gender, table)
        return current_survival_prob
    
    def death_probability_from_table(self, age: int, n_years: int, gender: Literal['pria', 'wanita'], table: MortalityTable) -> float:
        return 1.0 - self.survival_probability_from_table(age, n_years, gender, table)

    def deferred_death_probability_from_table(self, age: int, deferral_period: int, n_years_death: int, gender: Literal['pria', 'wanita'], table: MortalityTable) -> float:
        prob_survive_deferral = self.survival_probability_from_table(age, deferral_period, gender, table)
        if prob_survive_deferral == 0.0: return 0.0
        prob_die_within_n_after_deferral = self.death_probability_from_table(age + deferral_period, n_years_death, gender, table)
        return prob_survive_deferral * prob_die_within_n_after_deferral

    def force_of_mortality_from_table(self, age: int, t_offset: float, gender: Literal['pria', 'wanita'], table: MortalityTable, assumption_fractional: Literal['udd', 'cfm']) -> float:
        if not (0 <= t_offset < 1): raise ValueError("t_offset harus antara 0 (inklusif) dan 1 (eksklusif).")
        qx_at_age = table.qx(age, gender)
        px_at_age = 1.0 - qx_at_age
        if assumption_fractional == 'udd':
            denominator_udd = (1.0 - t_offset * qx_at_age)
            return qx_at_age / denominator_udd if denominator_udd > 1e-12 else float('inf')
        elif assumption_fractional == 'cfm':
            return -math.log(px_at_age) if px_at_age > 1e-12 else float('inf')
        else:
            raise ValueError("Asumsi fraksional tidak valid untuk force_of_mortality_from_table.")

    def pdf_death_from_table(self, age: int, t_period: float, gender: Literal['pria', 'wanita'], table: MortalityTable, assumption_fractional: Literal['udd', 'cfm']) -> float:
        if t_period < 0: raise ValueError("t_period tidak boleh negatif.")
        integer_part_t = int(t_period)
        fractional_part_t = t_period - integer_part_t
        
        tpx_value_integer_part = self.survival_probability_from_table(age, integer_part_t, gender, table)
        
        tpx_value_final = tpx_value_integer_part
        if fractional_part_t > 0 and tpx_value_integer_part > 0:
            age_after_integer = age + integer_part_t
            if age_after_integer <= table.max_age : 
                qx_base_frac = table.qx(age_after_integer, gender)
                px_base_frac = 1.0 - qx_base_frac
                if assumption_fractional == 'udd':
                    tpx_value_final *= (1.0 - fractional_part_t * qx_base_frac)
                elif assumption_fractional == 'cfm':
                    tpx_value_final *= (px_base_frac ** fractional_part_t)
            else:
                tpx_value_final = 0.0 
        elif tpx_value_integer_part == 0.0: 
             tpx_value_final = 0.0
        
        mu_value_at_time_t = self.force_of_mortality_from_table(age + integer_part_t, fractional_part_t, gender, table, assumption_fractional)
        return tpx_value_final * mu_value_at_time_t

    def nsp_whole_life_from_table(self, age: int, gender: Literal['pria', 'wanita'], table: MortalityTable) -> float:
        present_value_sum: float = 0.0
        for k in range(table.max_age - age): 
            prob_survive_k_years: float = self.survival_probability_from_table(age, k, gender, table)
            if prob_survive_k_years == 0.0 and k > 0: break
            prob_die_next_year: float = self._get_qx_from_table(age + k, gender, table)
            discounted_benefit: float = (self.v ** (k + 1)) * prob_survive_k_years * prob_die_next_year
            present_value_sum += discounted_benefit
        return present_value_sum

    def pv_annuity_due_whole_life_from_table(self, age: int, gender: Literal['pria', 'wanita'], table: MortalityTable) -> float:
        present_value_sum: float = 0.0
        for k in range(table.max_age - age + 1):
            prob_survive_k_years: float = self.survival_probability_from_table(age, k, gender, table)
            if prob_survive_k_years == 0.0 and k > 0: break
            discounted_payment: float = (self.v ** k) * prob_survive_k_years
            present_value_sum += discounted_payment
        return present_value_sum

    # === Metode untuk Asumsi Distribusi Murni ===
    def survival_probability_from_assumption(
        self, 
        age: int, 
        n_years: float, 
        px_function_yearly: Callable[[int], float], 
        omega: int,
        assumption_type_for_fractional: Optional[Literal['udd', 'cfm']] = 'cfm'
    ) -> float:
        if n_years < 0: raise ValueError("Jumlah tahun (n_years) tidak boleh negatif.")
        if n_years == 0: return 1.0

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
        return 1.0 - self.survival_probability_from_assumption(age, n_years, px_function_yearly, omega, assumption_type_for_fractional)

    def deferred_death_probability_from_assumption(
        self, 
        age: int, 
        deferral_period: float, 
        n_years_death: float, 
        px_function_yearly: Callable[[int], float], 
        omega: int, 
        assumption_type_for_fractional: Optional[Literal['udd', 'cfm']] = 'cfm',
        assumption_type_main: Optional[str] = None, # Tidak dipakai lagi secara langsung di sini
        params_main: Optional[List[float]] = None   # Tidak dipakai lagi secara langsung di sini
    ) -> float:
        prob_survive_deferral = self.survival_probability_from_assumption(
            age, deferral_period, px_function_yearly, omega, assumption_type_for_fractional
        )
        if prob_survive_deferral == 0.0: return 0.0
        
        prob_survive_total_period = self.survival_probability_from_assumption(
            age, deferral_period + n_years_death, px_function_yearly, omega, assumption_type_for_fractional
        )
        return prob_survive_deferral - prob_survive_total_period


    def nsp_whole_life_from_assumption(self, age: int, qx_function: Callable[[int], float], px_function: Callable[[int], float], omega: int) -> float:
        present_value_sum: float = 0.0
        for k in range(omega - age): 
            age_at_k: int = age + k
            # Menggunakan px_function tahunan, interpolasi fraksional default CFM jika float(k)
            prob_survive_k_years: float = self.survival_probability_from_assumption(age, float(k), px_function, omega, 'cfm')
            if prob_survive_k_years == 0.0 and k > 0: break
            prob_die_next_year: float = qx_function(age_at_k)
            discounted_benefit: float = (self.v ** (k + 1)) * prob_survive_k_years * prob_die_next_year
            present_value_sum += discounted_benefit
        return present_value_sum

    def pv_annuity_due_whole_life_from_assumption(self, age: int, px_function: Callable[[int], float], omega: int) -> float:
        present_value_sum: float = 0.0
        for k in range(omega - age + 1):
            prob_survive_k_years: float = self.survival_probability_from_assumption(age, float(k), px_function, omega, 'cfm')
            if prob_survive_k_years == 0.0 and k > 0: break
            discounted_payment: float = (self.v ** k) * prob_survive_k_years
            present_value_sum += discounted_payment
        return present_value_sum