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
    def _get_qx_from_table_select(self,
                                  attained_age: int,
                                  gender: Literal['pria', 'wanita'],
                                  table: MortalityTable,
                                  age_at_selection: Optional[int],
                                  current_duration_selected: Optional[int]) -> float:
        if attained_age < 0: return 1.0
        return table.get_qx(attained_age, gender, age_at_selection, current_duration_selected)

    def _get_px_from_table_select(self,
                                  attained_age: int,
                                  gender: Literal['pria', 'wanita'],
                                  table: MortalityTable,
                                  age_at_selection: Optional[int],
                                  current_duration_selected: Optional[int]) -> float:
        if attained_age < 0: return 0.0
        return table.get_px(attained_age, gender, age_at_selection, current_duration_selected)

    def survival_probability_from_table(self,
                                        attained_age_start: int,
                                        n_years: int,
                                        gender: Literal['pria', 'wanita'],
                                        table: MortalityTable,
                                        age_at_selection: Optional[int] = None,
                                        initial_duration_selected: int = 0
                                        ) -> float:
        if n_years < 0: raise ValueError("Jumlah tahun (n_years) tidak boleh negatif.")
        if n_years == 0: return 1.0
        current_survival_prob: float = 1.0
        for i in range(n_years):
            current_attained_age: int = attained_age_start + i
            current_duration_for_px: Optional[int] = None
            if age_at_selection is not None:
                current_duration_for_px = initial_duration_selected + i
            if abs(current_survival_prob) < 1e-12: break
            current_survival_prob *= self._get_px_from_table_select(
                current_attained_age, gender, table,
                age_at_selection, current_duration_for_px
            )
        return current_survival_prob

    def death_probability_from_table(self,
                                     attained_age_start: int, n_years: int,
                                     gender: Literal['pria', 'wanita'], table: MortalityTable,
                                     age_at_selection: Optional[int] = None,
                                     initial_duration_selected: int = 0
                                     ) -> float:
        return 1.0 - self.survival_probability_from_table(
            attained_age_start, n_years, gender, table,
            age_at_selection, initial_duration_selected
        )

    def deferred_death_probability_from_table(self,
                                              attained_age_start: int, deferral_period: int, n_years_death: int,
                                              gender: Literal['pria', 'wanita'], table: MortalityTable,
                                              age_at_selection: Optional[int] = None,
                                              initial_duration_selected: int = 0
                                              ) -> float:
        prob_survive_deferral = self.survival_probability_from_table(
            attained_age_start, deferral_period, gender, table,
            age_at_selection, initial_duration_selected
        )
        if abs(prob_survive_deferral) < 1e-12: return 0.0
        age_after_deferral = attained_age_start + deferral_period
        duration_after_deferral = initial_duration_selected + deferral_period if age_at_selection is not None else 0
        prob_die_within_n_after_deferral = self.death_probability_from_table(
            age_after_deferral, n_years_death, gender, table,
            age_at_selection, duration_after_deferral
        )
        return prob_survive_deferral * prob_die_within_n_after_deferral

    def force_of_mortality_from_table(self,
                                      attained_age_at_start_of_year: int,
                                      t_offset: float,
                                      gender: Literal['pria', 'wanita'],
                                      table: MortalityTable,
                                      assumption_fractional: Literal['udd', 'cfm'],
                                      age_at_selection: Optional[int] = None,
                                      duration_at_start_of_year: Optional[int] = None
                                      ) -> float:
        if not (0 <= t_offset < 1): raise ValueError("t_offset harus antara 0 (inklusif) dan 1 (eksklusif).")
        qx_at_age = table.get_qx(attained_age_at_start_of_year, gender, age_at_selection, duration_at_start_of_year)
        px_at_age = 1.0 - qx_at_age
        if assumption_fractional == 'udd':
            denominator_udd = (1.0 - t_offset * qx_at_age)
            return qx_at_age / denominator_udd if denominator_udd > 1e-12 else float('inf')
        elif assumption_fractional == 'cfm':
            return -math.log(px_at_age) if px_at_age > 1e-12 else float('inf')
        raise ValueError("Asumsi fraksional tidak valid untuk fom_table.")

    def pdf_death_from_table(self,
                             attained_age_start: int, t_period: float,
                             gender: Literal['pria', 'wanita'], table: MortalityTable,
                             assumption_fractional: Literal['udd', 'cfm'],
                             age_at_selection: Optional[int] = None,
                             initial_duration_selected: int = 0
                             ) -> float:
        if t_period < 0: raise ValueError("t_period tidak boleh negatif.")
        integer_part_t = int(t_period)
        fractional_part_t = t_period - integer_part_t
        tpx_integer_part = self.survival_probability_from_table(
            attained_age_start, integer_part_t, gender, table,
            age_at_selection, initial_duration_selected
        )
        tpx_final_value = tpx_integer_part
        if fractional_part_t > 0 and tpx_integer_part > 0:
            age_after_integer = attained_age_start + integer_part_t
            duration_after_integer = initial_duration_selected + integer_part_t if age_at_selection is not None else 0 # type: ignore
            if age_after_integer <= table.max_age_ultimate:
                qx_base_frac = table.get_qx(age_after_integer, gender, age_at_selection, duration_after_integer)
                px_base_frac = 1.0 - qx_base_frac
                if assumption_fractional == 'udd':
                    tpx_final_value *= (1.0 - fractional_part_t * qx_base_frac)
                elif assumption_fractional == 'cfm':
                    tpx_final_value *= (px_base_frac ** fractional_part_t)
            else: tpx_final_value = 0.0
        elif tpx_integer_part == 0.0 and fractional_part_t > 0 : tpx_final_value = 0.0
        
        duration_at_start_of_year_for_mu = initial_duration_selected + integer_part_t if age_at_selection is not None else None
        mu_value_at_time_t = self.force_of_mortality_from_table(
            attained_age_at_start_of_year=(attained_age_start + integer_part_t),
            t_offset=fractional_part_t, gender=gender, table=table,
            assumption_fractional=assumption_fractional,
            age_at_selection=age_at_selection,
            duration_at_start_of_year=duration_at_start_of_year_for_mu
        )
        return tpx_final_value * mu_value_at_time_t

    def nsp_whole_life_from_table(self,
                                  attained_age_start: int, gender: Literal['pria', 'wanita'], table: MortalityTable,
                                  age_at_selection: Optional[int] = None, initial_duration_selected: int = 0
                                  ) -> float:
        present_value_sum: float = 0.0
        limit_k = table.max_age_ultimate - attained_age_start
        for k in range(limit_k):
            prob_survive_k_years: float = self.survival_probability_from_table(
                attained_age_start, k, gender, table, age_at_selection, initial_duration_selected
            )
            if abs(prob_survive_k_years) < 1e-12 and k > 0: break
            current_duration_for_qx = initial_duration_selected + k if age_at_selection is not None else None
            prob_die_next_year: float = self._get_qx_from_table_select(
                attained_age_start + k, gender, table, age_at_selection, current_duration_for_qx
            )
            discounted_benefit: float = (self.v ** (k + 1)) * prob_survive_k_years * prob_die_next_year
            present_value_sum += discounted_benefit
        return present_value_sum

    def pv_annuity_due_whole_life_from_table(self,
                                             attained_age_start: int, gender: Literal['pria', 'wanita'], table: MortalityTable,
                                             age_at_selection: Optional[int] = None, initial_duration_selected: int = 0
                                             ) -> float:
        present_value_sum: float = 0.0
        limit_k = table.max_age_ultimate - attained_age_start + 1
        for k in range(limit_k):
            prob_survive_k_years: float = self.survival_probability_from_table(
                attained_age_start, k, gender, table, age_at_selection, initial_duration_selected
            )
            if abs(prob_survive_k_years) < 1e-12 and k > 0: break
            discounted_payment: float = (self.v ** k) * prob_survive_k_years
            present_value_sum += discounted_payment
        return present_value_sum

    def ex_curtate_from_table(self,
                              attained_age_start: int, gender: Literal['pria', 'wanita'], table: MortalityTable,
                              n_temp: Optional[int] = None,
                              age_at_selection: Optional[int] = None, initial_duration_selected: int = 0
                              ) -> float:
        expectation: float = 0.0
        limit_k = n_temp if n_temp is not None else (table.max_age_ultimate - attained_age_start)
        for k in range(1, limit_k + 1):
            expectation += self.survival_probability_from_table(
                attained_age_start, k, gender, table, age_at_selection, initial_duration_selected
            )
        return expectation

    def e_sq_curtate_from_table(self,
                                attained_age_start: int, gender: Literal['pria', 'wanita'], table: MortalityTable,
                                n_temp: Optional[int] = None,
                                age_at_selection: Optional[int] = None, initial_duration_selected: int = 0
                                ) -> float:
        expectation_sq: float = 0.0
        limit_j = n_temp if n_temp is not None else (table.max_age_ultimate - attained_age_start)
        for j in range(limit_j):
            expectation_sq += (2 * j + 1) * self.survival_probability_from_table(
                attained_age_start, j + 1, gender, table, age_at_selection, initial_duration_selected
            )
        return expectation_sq

    def ex_complete_from_table(self,
                               attained_age_start: int, gender: Literal['pria', 'wanita'], table: MortalityTable,
                               n_temp: Optional[int] = None, assumption_fractional: Literal['udd', 'cfm'] = 'udd',
                               age_at_selection: Optional[int] = None, initial_duration_selected: int = 0
                               ) -> float:
        limit_loop = n_temp if n_temp is not None else (table.max_age_ultimate - attained_age_start)
        sum_val: float = 0.0
        for k in range(limit_loop): # k from 0 to limit_loop-1
            k_px = self.survival_probability_from_table(
                attained_age_start, k, gender, table, age_at_selection, initial_duration_selected
            )
            if abs(k_px) < 1e-12 and k > 0: break

            current_age_for_q_or_p = attained_age_start + k
            current_duration_for_q_or_p = initial_duration_selected + k if age_at_selection is not None else None

            integral_val: float
            if assumption_fractional == 'udd':
                qx_at_xk = self._get_qx_from_table_select(current_age_for_q_or_p, gender, table, age_at_selection, current_duration_for_q_or_p)
                integral_val = 1.0 - 0.5 * qx_at_xk
            elif assumption_fractional == 'cfm':
                px_at_xk = self._get_px_from_table_select(current_age_for_q_or_p, gender, table, age_at_selection, current_duration_for_q_or_p)
                integral_val = (px_at_xk - 1.0) / math.log(px_at_xk) if abs(px_at_xk - 1.0) > 1e-9 and px_at_xk > 0 else (1.0 if abs(px_at_xk-1.0) < 1e-9 else 0.0)
            else:
                raise ValueError("Asumsi fraksional tidak valid untuk ex_complete_from_table.")
            sum_val += k_px * integral_val
        return sum_val

    def e_sq_complete_from_table(self,
                                 attained_age_start: int, gender: Literal['pria', 'wanita'], table: MortalityTable,
                                 n_temp: Optional[int] = None, assumption_fractional: Literal['udd', 'cfm'] = 'udd',
                                 age_at_selection: Optional[int] = None, initial_duration_selected: int = 0
                                 ) -> float:
        # Menggunakan aproksimasi umum dari momen curtate, karena formula integral langsungnya rumit
        ex_curtate_val = self.ex_curtate_from_table(attained_age_start, gender, table, n_temp, age_at_selection, initial_duration_selected)
        e_sq_curtate_val = self.e_sq_curtate_from_table(attained_age_start, gender, table, n_temp, age_at_selection, initial_duration_selected)

        if n_temp is None: # Whole life
            if assumption_fractional == 'udd':
                # E[T_x^2] approx E[K_x^2] + e_x + 1/3
                return e_sq_curtate_val + ex_curtate_val + (1.0/3.0)
            elif assumption_fractional == 'cfm':
                # Untuk CFM, aproksimasi bisa lebih rumit, gunakan UDD untuk sementara
                # E[T_x^2] = 2 * e_circ_x / mu - (e_circ_x)^2 (jika mu konstan, tidak berlaku umum)
                # Alternatif: Var(Tx) ~ Var(Kx) - 1/12, lalu E[T^2] = Var(T) + (e_circ)^2
                # e_circ_x untuk CFM adalah sum_val_cfm dari ex_complete_from_table
                ex_complete_cfm = self.ex_complete_from_table(attained_age_start, gender, table, None, 'cfm', age_at_selection, initial_duration_selected)
                var_k = e_sq_curtate_val - ex_curtate_val**2
                var_t_approx_cfm = var_k # Sebagai aproksimasi sangat kasar
                return var_t_approx_cfm + ex_complete_cfm**2
            else:
                raise ValueError("Asumsi fraksional tidak valid.")
        else: # n-year temporary
            _npx = self.survival_probability_from_table(attained_age_start, n_temp, gender, table, age_at_selection, initial_duration_selected)
            if assumption_fractional == 'udd':
                # Aproksimasi E[T_{x:n|}^2] approx E[K_{x:n|}^2] + e_{x:n|} + (1/3)*(1 - _n p_x) (lebih sederhana)
                return e_sq_curtate_val + ex_curtate_val + (1.0/3.0)*(1.0 - _npx)
            elif assumption_fractional == 'cfm':
                 # Aproksimasi untuk CFM, bisa disamakan dengan UDD untuk temporary
                return e_sq_curtate_val + ex_curtate_val + (1.0/3.0)*(1.0 - _npx)
            else:
                raise ValueError("Asumsi fraksional tidak valid.")


    # === Metode Berbasis Asumsi (tidak berubah dari versi terakhir yang berhasil) ===
    # (Salin semua metode berbasis asumsi dari versi terakhir Anda yang sudah benar)
    def survival_probability_from_assumption( self, age: int, n_years: float, px_function_yearly: Callable[[int], float], omega: int, assumption_type_for_fractional: Optional[Literal['udd', 'cfm']] = 'cfm') -> float:
        if n_years < 0: raise ValueError("Jumlah tahun (n_years) tidak boleh negatif.")
        if n_years == 0: return 1.0
        integer_part = int(n_years); fractional_part = n_years - integer_part
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
                if assumption_type_for_fractional == 'cfm': current_survival_prob *= (px_for_fractional_base ** fractional_part)
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
        if px_function_continuous: # Jika API memberikan fungsi kontinu
            limit_integral = float(n_temp) if n_temp is not None else float(omega - age)
            if limit_integral <= 0: return 0.0
            # TODO: Implementasi integrasi numerik jika tidak ada formula closed-form
            # Untuk sekarang, kita bisa menggunakan pendekatan yang sama seperti _from_table
            # atau jika API sudah menghitungnya (misal untuk De Moivre), biarkan saja.
            # Kita akan tetap gunakan pendekatan sumasi + interpolasi di sini untuk kesederhanaan
            # karena API yang akan memutuskan apakah memanggil ini atau menghitung langsung.
        
        # Fallback ke sumasi + interpolasi jika tidak ada px_function_continuous yang dihandle API
        if n_temp is None: # Whole life
            ex_curtate_val = self.ex_curtate_from_assumption(age, px_function_yearly, omega, None)
            if assumption_fractional == 'udd': return ex_curtate_val + 0.5
            elif assumption_fractional == 'cfm':
                sum_val_cfm: float = 0.0
                for k_loop in range(omega - age):
                    k_px_val = self.survival_probability_from_assumption(age, float(k_loop), px_function_yearly, omega)
                    if abs(k_px_val) < 1e-12 and k_loop > 0: break
                    px_at_xk = px_function_yearly(age + k_loop)
                    integral_val = (px_at_xk - 1.0) / math.log(px_at_xk) if abs(px_at_xk - 1.0) > 1e-9 and px_at_xk > 0 else (1.0 if abs(px_at_xk-1.0) < 1e-9 else 0.0)
                    sum_val_cfm += k_px_val * integral_val
                return sum_val_cfm
        else: # n-year temporary
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
        # Fallback jika logika tidak tercakup (seharusnya tidak terjadi)
        ex_curt_val_fallback = self.ex_curtate_from_assumption(age, px_function_yearly, omega, n_temp)
        return ex_curt_val_fallback + 0.5


    def e_sq_complete_from_assumption(
        self, age: int, px_function_yearly: Callable[[int], float],
        qx_function_yearly: Callable[[int], float], omega: int,
        n_temp: Optional[int] = None, assumption_fractional: Literal['udd','cfm'] = 'udd',
        px_function_continuous: Optional[Callable[[int, float], float]] = None
    ) -> float:
        ex_curtate_val = self.ex_curtate_from_assumption(age, px_function_yearly, omega, n_temp)
        e_sq_curtate_val = self.e_sq_curtate_from_assumption(age, px_function_yearly, omega, n_temp)

        if px_function_continuous and n_temp is None: # Untuk asumsi kontinu murni, API akan handle
            # Fallback ke aproksimasi UDD
            return e_sq_curtate_val + ex_curtate_val + (1.0/3.0)

        if n_temp is None: # Whole life
            if assumption_fractional == 'udd': return e_sq_curtate_val + ex_curtate_val + (1.0/3.0)
            else: # CFM (aproksimasi sama dengan UDD untuk sekarang)
                return e_sq_curtate_val + ex_curtate_val + (1.0/3.0)
        else: # n-year temporary
            _npx = self.survival_probability_from_assumption(age, float(n_temp), px_function_yearly, omega)
            if assumption_fractional == 'udd':
                # Aproksimasi yang disederhanakan untuk E[T_{x:n|}^2]
                return e_sq_curtate_val + ex_curtate_val + (1.0/3.0)*(1.0 - _npx)
            else: # CFM (aproksimasi sama dengan UDD untuk sekarang)
                return e_sq_curtate_val + ex_curtate_val + (1.0/3.0)*(1.0 - _npx)
        return e_sq_curtate_val + ex_curtate_val + (1.0/3.0) # Fallback