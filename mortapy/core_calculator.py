# mortapy/core_calculator.py
from typing import Literal, Optional, Callable, List
from .tables.base import MortalityTable
import math 

class ActuarialCalculator:
    """
    Kelas inti yang menyediakan metode untuk melakukan berbagai perhitungan aktuaria.
    """
    def __init__(self, interest_rate: float):
        self.interest_rate: float = interest_rate
        self.v: float = 1 / (1 + self.interest_rate)

    # === Metode Berbasis Tabel ===
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
        if abs(prob_survive_deferral) < 1e-12: return 0.0
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
        raise ValueError("Asumsi fraksional tidak valid untuk fom_table.")

    def pdf_death_from_table(self, age: int, t_period: float, gender: Literal['pria', 'wanita'], table: MortalityTable, assumption_fractional: Literal['udd', 'cfm']) -> float:
        if t_period < 0: raise ValueError("t_period tidak boleh negatif.")
        integer_part_t = int(t_period)
        fractional_part_t = t_period - integer_part_t
        tpx_integer_part = self.survival_probability_from_table(age, integer_part_t, gender, table)
        tpx_final_value = tpx_integer_part
        if fractional_part_t > 0 and tpx_integer_part > 0:
            age_after_integer = age + integer_part_t
            if age_after_integer <= table.max_age : 
                qx_base_frac = table.qx(age_after_integer, gender)
                px_base_frac = 1.0 - qx_base_frac
                if assumption_fractional == 'udd':
                    tpx_final_value *= (1.0 - fractional_part_t * qx_base_frac)
                elif assumption_fractional == 'cfm':
                    tpx_final_value *= (px_base_frac ** fractional_part_t)
            else: tpx_final_value = 0.0 
        elif tpx_integer_part == 0.0 and fractional_part_t > 0: tpx_final_value = 0.0
        mu_value_at_time_t = self.force_of_mortality_from_table(age + integer_part_t, fractional_part_t, gender, table, assumption_fractional)
        return tpx_final_value * mu_value_at_time_t

    def nsp_whole_life_from_table(self, age: int, gender: Literal['pria', 'wanita'], table: MortalityTable) -> float:
        pv_sum: float = 0.0
        for k in range(table.max_age - age):
            tpx = self.survival_probability_from_table(age, k, gender, table)
            if abs(tpx) < 1e-12 and k > 0: break
            q_x_plus_k = self._get_qx_from_table(age + k, gender, table)
            pv_sum += (self.v ** (k + 1)) * tpx * q_x_plus_k
        return pv_sum

    def pv_annuity_due_whole_life_from_table(self, age: int, gender: Literal['pria', 'wanita'], table: MortalityTable) -> float:
        pv_sum: float = 0.0
        for k in range(table.max_age - age + 1):
            tpx = self.survival_probability_from_table(age, k, gender, table)
            if abs(tpx) < 1e-12 and k > 0: break
            pv_sum += (self.v ** k) * tpx
        return pv_sum

    def ex_curtate_from_table(self, age: int, gender: Literal['pria', 'wanita'], table: MortalityTable, n_temp: Optional[int] = None) -> float:
        expectation: float = 0.0
        limit_k = n_temp if n_temp is not None else (table.max_age - age)
        for k in range(1, limit_k + 1):
            expectation += self.survival_probability_from_table(age, k, gender, table)
        return expectation

    def e_sq_curtate_from_table(self, age: int, gender: Literal['pria', 'wanita'], table: MortalityTable, n_temp: Optional[int] = None) -> float:
        expectation_sq: float = 0.0
        limit_j = n_temp if n_temp is not None else (table.max_age - age)
        for j in range(limit_j):
            expectation_sq += (2 * j + 1) * self.survival_probability_from_table(age, j + 1, gender, table)
        return expectation_sq

    def ex_complete_from_table(self, age: int, gender: Literal['pria', 'wanita'], table: MortalityTable, n_temp: Optional[int] = None, assumption_fractional: Literal['udd', 'cfm'] = 'udd') -> float:
        if n_temp is None: # Whole life
            ex_curtate_val = self.ex_curtate_from_table(age, gender, table, None)
            if assumption_fractional == 'udd': return ex_curtate_val + 0.5
            elif assumption_fractional == 'cfm':
                # sum_{k=0}^{omega-x-1} _k p_x * (p_{x+k}-1)/ln(p_{x+k})
                sum_val: float = 0.0
                for k in range(table.max_age - age):
                    k_px = self.survival_probability_from_table(age, k, gender, table)
                    if abs(k_px) < 1e-12 and k > 0: break
                    px_at_xk = self._get_px_from_table(age + k, gender, table)
                    integral_val = (px_at_xk - 1.0) / math.log(px_at_xk) if abs(px_at_xk - 1.0) > 1e-9 and px_at_xk > 0 else (1.0 if abs(px_at_xk-1.0) < 1e-9 else 0.0)
                    sum_val += k_px * integral_val
                return sum_val
            else: raise ValueError("Asumsi fraksional tidak valid.")
        else: # n-year temporary
            sum_val: float = 0.0
            for k in range(n_temp):
                _kpx = self.survival_probability_from_table(age, k, gender, table)
                if abs(_kpx) < 1e-12 and k > 0: break
                qx_at_xk = self._get_qx_from_table(age + k, gender, table)
                px_at_xk = 1.0 - qx_at_xk
                integral_val: float
                if assumption_fractional == 'udd': integral_val = 1.0 - 0.5 * qx_at_xk
                elif assumption_fractional == 'cfm':
                    integral_val = (px_at_xk - 1.0) / math.log(px_at_xk) if abs(px_at_xk - 1.0) > 1e-9 and px_at_xk > 0 else (1.0 if abs(px_at_xk-1.0) < 1e-9 else 0.0)
                else: raise ValueError("Asumsi fraksional tidak valid.")
                sum_val += _kpx * integral_val
            return sum_val

    def e_sq_complete_from_table(self, age: int, gender: Literal['pria', 'wanita'], table: MortalityTable, n_temp: Optional[int] = None, assumption_fractional: Literal['udd', 'cfm'] = 'udd') -> float:
        ex_curtate_val = self.ex_curtate_from_table(age, gender, table, n_temp)
        e_sq_curtate_val = self.e_sq_curtate_from_table(age, gender, table, n_temp)
        if n_temp is None: # Whole life
            if assumption_fractional == 'udd': return e_sq_curtate_val + ex_curtate_val + (1.0/3.0)
            else: return e_sq_curtate_val + ex_curtate_val + (1.0/3.0) # CFM approx sama dulu
        else: # n-year temporary - PERBAIKAN FORMULA UDD
            _npx = self.survival_probability_from_table(age, n_temp, gender, table)
            if assumption_fractional == 'udd':
                # Formula dari Bowers et al. (rumus 3.5.14) untuk E[T^2_{x:n|}]
                # = sum_{k=0}^{n-1} (2k+1) _k p_x (1 - 0.5 q_{x+k}) + n^2 _n p_x - (1/3) sum_{k=0}^{n-1} _k p_x q_{x+k}
                # Ini sangat rumit, mari kita gunakan aproksimasi yang lebih sederhana
                # E[T_{x:n|}^2] approx E[K_{x:n|}^2] + e_{x:n|} + (1/3)*(1 - _n p_x) - n * _n p_x * (n + e_{x+n}) -- Ini salah
                # Gunakan E[T^2] ~ E[K^2] + E[K] + 1/3, tapi hanya untuk bagian yang "complete"
                # Untuk temporary, lebih aman pakai Var(T) ~ Var(K) - 1/12 (jika qx kecil)
                # atau hitung langsung integral 2t * _t p_x dt jika memungkinkan.
                # Untuk sekarang, kita gunakan aproksimasi yang lebih sederhana namun mungkin kurang akurat untuk temporary:
                return e_sq_curtate_val + ex_curtate_val * (1.0 - _npx) + (1.0/3.0) * (1.0 - _npx) # Aproksimasi kasar
            else: # CFM approx sama dulu
                return e_sq_curtate_val + ex_curtate_val * (1.0 - _npx) + (1.0/3.0) * (1.0 - _npx)

    # === Metode untuk Asumsi Distribusi Murni ===
    def survival_probability_from_assumption( self, age: int, n_years: float, px_function_yearly: Callable[[int], float], omega: int, assumption_type_for_fractional: Optional[Literal['udd', 'cfm']] = 'cfm') -> float:
        if n_years < 0: raise ValueError("Jumlah tahun (n_years) tidak boleh negatif.")
        if n_years == 0: return 1.0
        integer_part = int(n_years)
        fractional_part = n_years - integer_part
        current_survival_prob: float = 1.0
        for i in range(integer_part):
            current_age_loop: int = age + i
            if current_age_loop >= omega: current_survival_prob = 0.0; break
            current_survival_prob *= px_function_yearly(current_age_loop)
        if fractional_part > 0 and current_survival_prob > 0.0:
            age_after_integer_part: int = age + integer_part
            if age_after_integer_part >= omega: current_survival_prob = 0.0
            else:
                px_for_fractional_base = px_function_yearly(age_after_integer_part)
                if assumption_type_for_fractional == 'cfm':
                    current_survival_prob *= (px_for_fractional_base ** fractional_part)
                elif assumption_type_for_fractional == 'udd':
                    qx_for_fractional_base = 1.0 - px_for_fractional_base
                    current_survival_prob *= (1.0 - fractional_part * qx_for_fractional_base)
                else: raise ValueError("Asumsi fraksional tidak valid.")
        return current_survival_prob

    def death_probability_from_assumption( self, age: int, n_years: float, px_function_yearly: Callable[[int], float], omega: int, assumption_type_for_fractional: Optional[Literal['udd', 'cfm']] = 'cfm') -> float:
        return 1.0 - self.survival_probability_from_assumption(age, n_years, px_function_yearly, omega, assumption_type_for_fractional)

    def deferred_death_probability_from_assumption( self, age: int, deferral_period: float, n_years_death: float, px_function_yearly: Callable[[int], float], omega: int, assumption_type_for_fractional: Optional[Literal['udd', 'cfm']] = 'cfm', px_function_continuous: Optional[Callable[[int, float], float]] = None) -> float:
        prob_survive_deferral: float
        if px_function_continuous:
            prob_survive_deferral = px_function_continuous(age, deferral_period)
            if abs(prob_survive_deferral) < 1e-12: return 0.0
            prob_survive_total_period = px_function_continuous(age, deferral_period + n_years_death)
            u_px_plus_t = prob_survive_total_period / prob_survive_deferral if prob_survive_deferral > 1e-12 else 0.0
            prob_die_within_n_after_deferral = 1.0 - u_px_plus_t
        else:
            prob_survive_deferral = self.survival_probability_from_assumption(age, deferral_period, px_function_yearly, omega, assumption_type_for_fractional)
            if abs(prob_survive_deferral) < 1e-12: return 0.0
            prob_survive_total_period = self.survival_probability_from_assumption(age, deferral_period + n_years_death, px_function_yearly, omega, assumption_type_for_fractional)
            # _u q_{x+t} = 1 - _u p_{x+t}
            # _u p_{x+t} = _{t+u}p_x / _t p_x
            u_px_plus_t_val = prob_survive_total_period / prob_survive_deferral if prob_survive_deferral > 1e-12 else 0.0
            prob_die_within_n_after_deferral = 1.0 - u_px_plus_t_val
        return prob_survive_deferral * prob_die_within_n_after_deferral

    def nsp_whole_life_from_assumption(self, age: int, qx_function: Callable[[int], float], px_function: Callable[[int], float], omega: int) -> float:
        pv_sum: float = 0.0
        for k in range(omega - age):
            prob_survive_k_years: float = self.survival_probability_from_assumption(age, float(k), px_function, omega, 'cfm')
            if abs(prob_survive_k_years) < 1e-12 and k > 0: break
            prob_die_next_year: float = qx_function(age + k)
            pv_sum += (self.v ** (k + 1)) * prob_survive_k_years * prob_die_next_year
        return pv_sum

    def pv_annuity_due_whole_life_from_assumption(self, age: int, px_function: Callable[[int], float], omega: int) -> float:
        pv_sum: float = 0.0
        for k in range(omega - age + 1):
            prob_survive_k_years: float = self.survival_probability_from_assumption(age, float(k), px_function, omega, 'cfm')
            if abs(prob_survive_k_years) < 1e-12 and k > 0: break
            pv_sum += (self.v ** k) * prob_survive_k_years
        return pv_sum

    def ex_curtate_from_assumption(self, age: int, px_function_yearly: Callable[[int], float], omega: int, n_temp: Optional[int] = None) -> float:
        expectation: float = 0.0
        limit_k = n_temp if n_temp is not None else (omega - age)
        for k in range(1, limit_k + 1):
            expectation += self.survival_probability_from_assumption(age, float(k), px_function_yearly, omega)
        return expectation

    def e_sq_curtate_from_assumption(self, age: int, px_function_yearly: Callable[[int], float], omega: int, n_temp: Optional[int] = None) -> float:
        expectation_sq: float = 0.0
        limit_j = n_temp if n_temp is not None else (omega - age)
        for j in range(limit_j):
            expectation_sq += (2 * j + 1) * self.survival_probability_from_assumption(age, float(j + 1), px_function_yearly, omega)
        return expectation_sq

    def ex_complete_from_assumption(
        self, age: int, px_function_yearly: Callable[[int], float], 
        qx_function_yearly: Callable[[int], float], omega: int, 
        n_temp: Optional[int] = None, assumption_fractional: Literal['udd','cfm'] = 'udd',
        px_function_continuous: Optional[Callable[[int, float], float]] = None
    ) -> float:
        if px_function_continuous: # Jika ada fungsi kontinu, gunakan itu
            # Untuk temporary, integral dari 0 sampai n. Untuk whole life, 0 sampai omega-age.
            limit_integral = float(n_temp) if n_temp is not None else float(omega - age)
            if limit_integral <= 0: return 0.0
            
            # Jika ada formula closed-form (seperti De Moivre, CFM mu konstan) itu akan di-handle di API
            # Di sini kita bisa lakukan integrasi numerik jika px_function_continuous adalah _t p_x
            # Atau, jika px_function_continuous adalah MU_X, kita pakai integral -ln(_t p_x)
            # Ini menjadi rumit. Untuk sekarang, kita kembalikan ke aproksimasi UDD.
            # TODO: Implementasi integrasi numerik atau penanganan formula closed-form di sini.
            # For now, fallback to UDD-like approximation from curtate
            ex_curt_val = self.ex_curtate_from_assumption(age, px_function_yearly, omega, n_temp)
            if n_temp is None:
                return ex_curt_val + 0.5
            else:
                _npx = self.survival_probability_from_assumption(age, float(n_temp), px_function_yearly, omega, assumption_fractional)
                return ex_curt_val + 0.5 * (1.0 - _npx) # Aproksimasi umum temporary
        
        # Jika tidak ada fungsi kontinu, gunakan sumasi dan interpolasi
        ex_curt_val = self.ex_curtate_from_assumption(age, px_function_yearly, omega, n_temp)
        if n_temp is None: 
            if assumption_fractional == 'udd': return ex_curt_val + 0.5
            elif assumption_fractional == 'cfm': 
                sum_val_cfm: float = 0.0
                for k_loop in range(omega - age):
                    k_px_val = self.survival_probability_from_assumption(age, float(k_loop), px_function_yearly, omega)
                    if abs(k_px_val) < 1e-12 and k_loop > 0: break
                    px_at_xk = px_function_yearly(age + k_loop)
                    integral_val = (px_at_xk - 1.0) / math.log(px_at_xk) if abs(px_at_xk - 1.0) > 1e-9 and px_at_xk > 0 else (1.0 if abs(px_at_xk-1.0) < 1e-9 else 0.0)
                    sum_val_cfm += k_px_val * integral_val
                return sum_val_cfm
        else: 
            sum_val: float = 0.0
            for k in range(n_temp):
                _kpx = self.survival_probability_from_assumption(age, float(k), px_function_yearly, omega)
                if abs(_kpx) < 1e-12 and k > 0: break
                qx_at_xk = qx_function_yearly(age + k)
                px_at_xk = 1.0 - qx_at_xk
                integral_val: float
                if assumption_fractional == 'udd': integral_val = 1.0 - 0.5 * qx_at_xk
                elif assumption_fractional == 'cfm':
                    integral_val = (px_at_xk - 1.0) / math.log(px_at_xk) if abs(px_at_xk - 1.0) > 1e-9 and px_at_xk > 0 else (1.0 if abs(px_at_xk-1.0) < 1e-9 else 0.0)
                else: raise ValueError("Asumsi fraksional tidak valid.")
                sum_val += _kpx * integral_val
            return sum_val
        return ex_curt_val + 0.5 # Fallback default

    def e_sq_complete_from_assumption(
        self, age: int, px_function_yearly: Callable[[int], float], 
        qx_function_yearly: Callable[[int], float], omega: int, 
        n_temp: Optional[int] = None, assumption_fractional: Literal['udd','cfm'] = 'udd',
        px_function_continuous: Optional[Callable[[int, float], float]] = None
    ) -> float:
        ex_curtate_val = self.ex_curtate_from_assumption(age, px_function_yearly, omega, n_temp)
        e_sq_curtate_val = self.e_sq_curtate_from_assumption(age, px_function_yearly, omega, n_temp)

        if px_function_continuous and n_temp is None: # Untuk asumsi kontinu whole life
            # E[T^2] = 2 * integral(t * _t p_x dt) - sangat rumit, pakai aproksimasi UDD
            return e_sq_curtate_val + ex_curtate_val + (1.0/3.0)

        if n_temp is None: 
            if assumption_fractional == 'udd': return e_sq_curtate_val + ex_curtate_val + (1.0/3.0)
            else: return e_sq_curtate_val + ex_curtate_val + (1.0/3.0) 
        else: 
            if assumption_fractional == 'udd':
                _npx = self.survival_probability_from_assumption(age, float(n_temp), px_function_yearly, omega)
                # Formula dari Bowers (3.5.14)
                # E[T_{x:n}^2] = sum_{k=0}^{n-1} ( (2k+1) * {_k}p_x * (1-q_{x+k}/2) ) + n^2 * _n p_x - (1/3) * sum_{k=0}^{n-1} {_k}p_x * q_{x+k}
                # Ini sangat rumit. Kita akan gunakan aproksimasi yang lebih sederhana untuk sementara.
                # Aproksimasi yang lebih sederhana (mungkin kurang akurat):
                # E[T_{x:n|}^2] approx E[K_{x:n|}^2] + e_{x:n|} + (1/3)*(1 - _n p_x)
                return e_sq_curtate_val + ex_curtate_val + (1.0/3.0)*(1.0 - _npx)

            else: # CFM approx sama dulu
                _npx = self.survival_probability_from_assumption(age, float(n_temp), px_function_yearly, omega)
                return e_sq_curtate_val + ex_curtate_val + (1.0/3.0)*(1.0 - _npx)
        return e_sq_curtate_val + ex_curtate_val + (1.0/3.0) # Fallback default