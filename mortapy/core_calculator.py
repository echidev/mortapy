# mortapy/core_calculator.py
from typing import Literal, Optional, Callable, List 
from .tables.base import MortalityTable
import math 

class ActuarialCalculator:
    """
    Kelas inti yang menyediakan metode untuk melakukan berbagai perhitungan aktuaria.
    Perhitungan dapat didasarkan pada objek MortalityTable atau fungsi-fungsi
    probabilitas dari asumsi distribusi murni.

    Attributes:
        interest_rate (float): Tingkat suku bunga efektif per periode.
        v (float): Faktor diskon, dihitung sebagai 1 / (1 + interest_rate).
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
        """Helper internal untuk mengambil q_x dari objek MortalityTable."""
        if age < 0: return 1.0 # Konsisten dengan MortalityTable.qx
        return table.qx(age, gender)

    def _get_px_from_table(self, age: int, gender: Literal['pria', 'wanita'], table: MortalityTable) -> float:
        """Helper internal untuk mengambil p_x dari objek MortalityTable."""
        if age < 0: return 0.0 # Konsisten dengan MortalityTable.px
        return table.px(age, gender)

    def survival_probability_from_table(self, age: int, n_years: int, gender: Literal['pria', 'wanita'], table: MortalityTable) -> float:
        """
        Menghitung probabilitas _{n_years}p_{age} menggunakan MortalityTable untuk periode bulat.

        Args:
            age (int): Usia awal.
            n_years (int): Jumlah tahun periode.
            gender (Literal['pria', 'wanita']): Jenis kelamin.
            table (MortalityTable): Objek tabel mortalita.

        Returns:
            float: Probabilitas _{n_years}p_{age}.
        
        Raises:
            ValueError: Jika n_years negatif.
        """
        if n_years < 0: raise ValueError("Jumlah tahun (n_years) tidak boleh negatif.")
        if n_years == 0: return 1.0
        
        current_survival_prob: float = 1.0
        for i in range(n_years):
            current_age: int = age + i
            # Jika probabilitas hidup sudah 0, tidak perlu lanjut
            if current_survival_prob == 0.0: break 
            current_survival_prob *= self._get_px_from_table(current_age, gender, table)
        return current_survival_prob
    
    def death_probability_from_table(self, age: int, n_years: int, gender: Literal['pria', 'wanita'], table: MortalityTable) -> float:
        """
        Menghitung probabilitas _{n_years}q_{age} menggunakan MortalityTable (untuk periode bulat n).

        Args:
            Args sama seperti survival_probability_from_table.

        Returns:
            float: Probabilitas _{n_years}q_{age}.
        """
        return 1.0 - self.survival_probability_from_table(age, n_years, gender, table)

    def deferred_death_probability_from_table(self, age: int, deferral_period: int, n_years_death: int, gender: Literal['pria', 'wanita'], table: MortalityTable) -> float:
        """
        Menghitung probabilitas kematian ditunda _{deferral_period}|{n_years_death} q_x 
        menggunakan MortalityTable (untuk periode bulat) dengan formula perkalian.

        Args:
            age (int): Usia awal.
            deferral_period (int): Periode penundaan (t).
            n_years_death (int): Periode kematian setelah penundaan (u).
            gender (Literal['pria', 'wanita']): Jenis kelamin.
            table (MortalityTable): Objek tabel mortalita.

        Returns:
            float: Probabilitas _{deferral_period}|{n_years_death}q_{age}.
        """
        prob_survive_deferral = self.survival_probability_from_table(age, deferral_period, gender, table)
        if abs(prob_survive_deferral) < 1e-12: # Jika probabilitas hidup sangat kecil/nol
            return 0.0
        
        prob_die_within_n_after_deferral = self.death_probability_from_table(age + deferral_period, n_years_death, gender, table)
        return prob_survive_deferral * prob_die_within_n_after_deferral

    def force_of_mortality_from_table(self, age: int, t_offset: float, gender: Literal['pria', 'wanita'], table: MortalityTable, assumption_fractional: Literal['udd', 'cfm']) -> float:
        """
        Menghitung force of mortality μ_{age+t_offset} berdasarkan q_x dari tabel,
        dengan asumsi UDD atau CFM untuk interpolasi dalam interval satu tahun.

        Args:
            age (int): Usia bulat awal interval [age, age+1).
            t_offset (float): Fraksi tahun dari usia bulat `age` (0 <= t_offset < 1).
            gender (Literal['pria', 'wanita']): Jenis kelamin.
            table (MortalityTable): Objek tabel mortalita.
            assumption_fractional (Literal['udd', 'cfm']): Asumsi distribusi kematian dalam setahun.

        Returns:
            float: Nilai μ_{age+t_offset}.
        
        Raises:
            ValueError: Jika t_offset di luar rentang [0, 1) atau asumsi tidak valid.
        """
        if not (0 <= t_offset < 1): raise ValueError("t_offset harus antara 0 (inklusif) dan 1 (eksklusif).")
        
        # qx dan px di sini adalah q_age dan p_age dari tabel
        qx_at_age = table.qx(age, gender) 
        px_at_age = 1.0 - qx_at_age

        if assumption_fractional == 'udd':
            # Formula μ_{x+s} = q_x / (1 - s * q_x)
            denominator_udd = (1.0 - t_offset * qx_at_age)
            return qx_at_age / denominator_udd if denominator_udd > 1e-12 else float('inf')
        elif assumption_fractional == 'cfm':
            # Formula μ_{x+s} = -ln(p_x) (konstan sepanjang interval [x, x+1))
            return -math.log(px_at_age) if px_at_age > 1e-12 else float('inf')
        else:
            raise ValueError("Asumsi fraksional tidak valid. Pilih 'udd' atau 'cfm'.")

    def pdf_death_from_table(self, age: int, t_period: float, gender: Literal['pria', 'wanita'], table: MortalityTable, assumption_fractional: Literal['udd', 'cfm']) -> float:
        """
        Menghitung PDF kematian f_X(age+t_period) = _{t_period}p_{age} * μ_{age+t_period}
        berdasarkan tabel mortalita dan asumsi interpolasi fraksional.

        Args:
            age (int): Usia awal bulat.
            t_period (float): Periode waktu dari 'age' hingga titik kematian (bisa non-bulat).
            gender (Literal['pria', 'wanita']): Jenis kelamin.
            table (MortalityTable): Objek tabel mortalita.
            assumption_fractional (Literal['udd', 'cfm']): Asumsi untuk interpolasi _t_p_x dan μ.

        Returns:
            float: Nilai PDF kematian pada usia tepat age + t_period.
        
        Raises:
            ValueError: Jika t_period negatif.
        """
        if t_period < 0: raise ValueError("t_period tidak boleh negatif.")
        
        integer_part_t = int(t_period)
        fractional_part_t = t_period - integer_part_t
        
        # Hitung _{integer_part_t}p_age dari tabel
        tpx_integer_part = self.survival_probability_from_table(age, integer_part_t, gender, table)
        
        tpx_final_value = tpx_integer_part
        # Interpolasi bagian fraksional untuk _{fractional_part_t}p_{age+integer_part_t}
        if fractional_part_t > 0 and tpx_integer_part > 0:
            age_after_integer = age + integer_part_t
            if age_after_integer <= table.max_age : 
                qx_base_frac = table.qx(age_after_integer, gender)
                px_base_frac = 1.0 - qx_base_frac
                if assumption_fractional == 'udd':
                    tpx_final_value *= (1.0 - fractional_part_t * qx_base_frac)
                elif assumption_fractional == 'cfm':
                    tpx_final_value *= (px_base_frac ** fractional_part_t)
                else: # Tidak akan terjadi jika validasi di API benar
                    raise ValueError("Asumsi fraksional tidak valid.")
            else: # Usia sudah melewati batas tabel
                tpx_final_value = 0.0 
        elif tpx_integer_part == 0.0 and fractional_part_t > 0 : # Jika sudah mati di bagian integer
             tpx_final_value = 0.0
        
        # Hitung mu_{age+t_period}
        # Usia bulat untuk mu adalah age + integer_part_t
        # Offset untuk mu adalah fractional_part_t
        mu_value_at_time_t = self.force_of_mortality_from_table(
            age=(age + integer_part_t), 
            t_offset=fractional_part_t, 
            gender=gender, 
            table=table, 
            assumption_fractional=assumption_fractional
        )
        return tpx_final_value * mu_value_at_time_t

    def nsp_whole_life_from_table(self, age: int, gender: Literal['pria', 'wanita'], table: MortalityTable) -> float:
        """Menghitung A_x menggunakan MortalityTable."""
        present_value_sum: float = 0.0
        # Loop hingga usia sebelum usia maksimum di tabel (karena q_x dipakai)
        for k in range(table.max_age - age): 
            age_at_k: int = age + k
            prob_survive_k_years: float = self.survival_probability_from_table(age, k, gender, table)
            if prob_survive_k_years == 0.0 and k > 0: break
            prob_die_next_year: float = self._get_qx_from_table(age_at_k, gender, table)
            discounted_benefit: float = (self.v ** (k + 1)) * prob_survive_k_years * prob_die_next_year
            present_value_sum += discounted_benefit
        return present_value_sum

    def pv_annuity_due_whole_life_from_table(self, age: int, gender: Literal['pria', 'wanita'], table: MortalityTable) -> float:
        """Menghitung ä_x menggunakan MortalityTable."""
        present_value_sum: float = 0.0
        # Loop hingga usia maksimum di tabel (inklusif, untuk pembayaran di usia max_age jika masih hidup)
        for k in range(table.max_age - age + 1):
            prob_survive_k_years: float = self.survival_probability_from_table(age, k, gender, table)
            if prob_survive_k_years == 0.0 and k > 0: break
            discounted_payment: float = (self.v ** k) * prob_survive_k_years
            present_value_sum += discounted_payment
        return present_value_sum

    # --- Metode Curtate Future Lifetime Moments Berbasis Tabel ---
    def ex_curtate_from_table(self, age: int, gender: Literal['pria', 'wanita'], table: MortalityTable, n_temp: Optional[int] = None) -> float:
        """
        Menghitung ekspektasi curtate future lifetime (e_x atau e_{x:n|}) 
        menggunakan MortalityTable.
        e_x = sum_{k=1}^{omega-x} _k p_x
        e_{x:n|} = sum_{k=1}^{n} _k p_x

        Args:
            age (int): Usia awal.
            gender (Literal['pria', 'wanita']): Jenis kelamin.
            table (MortalityTable): Objek tabel mortalita.
            n_temp (Optional[int]): Periode temporary n. Jika None, dihitung seumur hidup.

        Returns:
            float: Nilai e_x atau e_{x:n|}.
        """
        expectation: float = 0.0
        # Batas atas loop adalah n jika temporary, atau omega-x jika whole life
        limit_k = n_temp if n_temp is not None else (table.max_age - age)
        
        for k in range(1, limit_k + 1): # k dari 1 hingga limit_k
            expectation += self.survival_probability_from_table(age, k, gender, table) # _k p_x
        return expectation

    def e_sq_curtate_from_table(self, age: int, gender: Literal['pria', 'wanita'], table: MortalityTable, n_temp: Optional[int] = None) -> float:
        """
        Menghitung momen kedua dari curtate future lifetime (E[K_x^2] atau E[(K_{x:n|})^2])
        menggunakan MortalityTable.
        E[K^2] = sum_{j=0}^{limit-1} (2j+1) * _{j+1}p_x

        Args:
            age (int): Usia awal.
            gender (Literal['pria', 'wanita']): Jenis kelamin.
            table (MortalityTable): Objek tabel mortalita.
            n_temp (Optional[int]): Periode temporary n. Jika None, dihitung seumur hidup.

        Returns:
            float: Nilai E[K_x^2] atau E[(K_{x:n|})^2].
        """
        expectation_sq: float = 0.0
        # Batas atas K adalah n-1 jika temporary, atau omega-x-1 jika whole life
        # Batas atas loop j adalah limit-1
        limit_j = n_temp if n_temp is not None else (table.max_age - age)

        for j in range(limit_j): # j dari 0 hingga limit_j - 1
            expectation_sq += (2 * j + 1) * self.survival_probability_from_table(age, j + 1, gender, table)
        return expectation_sq

    # === Metode untuk Asumsi Distribusi Murni ===
    def survival_probability_from_assumption(
        self, 
        age: int, 
        n_years: float, 
        px_function_yearly: Callable[[int], float], # p_x tahunan dari asumsi
        omega: int,
        assumption_type_for_fractional: Optional[Literal['udd', 'cfm']] = 'cfm' # Asumsi untuk bagian fraksional
    ) -> float:
        """
        Menghitung probabilitas _t p_x menggunakan fungsi p_x(usia_bulat) dari asumsi.
        Menggunakan UDD atau CFM untuk bagian fraksional jika n_years adalah float.
        """
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
        px_function_yearly: Callable[[int], float], # Diubah dari qx_func
        omega: int, 
        assumption_type_for_fractional: Optional[Literal['udd', 'cfm']] = 'cfm'
    ) -> float:
        """Menghitung _n q_x menggunakan fungsi p_x tahunan dari asumsi."""
        return 1.0 - self.survival_probability_from_assumption(age, n_years, px_function_yearly, omega, assumption_type_for_fractional)

    def deferred_death_probability_from_assumption(
        self, 
        age: int, 
        deferral_period: float, 
        n_years_death: float, 
        px_function_yearly: Callable[[int], float], 
        omega: int, 
        assumption_type_for_fractional: Optional[Literal['udd', 'cfm']] = 'cfm',
        px_function_continuous: Optional[Callable[[int, float], float]] = None # Ditambahkan untuk asumsi kontinu
    ) -> float:
        """Menghitung _{t}|_u q_x dari asumsi (formula perkalian)."""
        prob_survive_deferral: float
        prob_die_within_n_after_deferral: float

        if px_function_continuous: # Jika fungsi survival kontinu tersedia
            prob_survive_deferral = px_function_continuous(age, deferral_period)
            if abs(prob_survive_deferral) < 1e-12: return 0.0
            
            # _u q_{x+t} = 1 - _u p_{x+t}
            # _u p_{x+t} dapat dihitung sebagai px_function_continuous(usia_awal_baru, periode_baru)
            # di mana usia_awal_baru adalah age + deferral_period, dan periode_baru adalah n_years_death
            # Namun, px_function_continuous kita menerima (usia_awal_global, total_periode_dari_awal_global)
            # Jadi, _u p_{x+t} =  _t+u p_x / _t p_x
            prob_survive_total_period = px_function_continuous(age, deferral_period + n_years_death)
            u_px_plus_t = prob_survive_total_period / prob_survive_deferral if prob_survive_deferral > 1e-12 else 0.0
            prob_die_within_n_after_deferral = 1.0 - u_px_plus_t

        else: # Gunakan pendekatan tahunan + interpolasi
            prob_survive_deferral = self.survival_probability_from_assumption(
                age, deferral_period, px_function_yearly, omega, assumption_type_for_fractional
            )
            if abs(prob_survive_deferral) < 1e-12: return 0.0

            # Untuk _u q_{x+t} (atau 1 - _u p_{x+t}) dengan px_function_yearly
            # Asumsikan age + deferral_period dibulatkan untuk memulai interval baru
            # Ini adalah penyederhanaan jika deferral_period adalah float
            age_after_deferral_rounded = age + int(deferral_period)
            remaining_deferral_frac = deferral_period - int(deferral_period)
            
            # Jika ada sisa fraksional dari deferral, kita perlu _(1-s) p_{x+k} * _u q_{x+k+1-s}
            # Ini menjadi kompleks. Paling mudah, jika tidak ada fungsi kontinu,
            # kita terapkan formula pengurangan: _t p_x - _{t+u} p_x
            prob_survive_total_period = self.survival_probability_from_assumption(
                age, deferral_period + n_years_death, px_function_yearly, omega, assumption_type_for_fractional
            )
            return prob_survive_deferral - prob_survive_total_period # Kembali ke pengurangan untuk kasus diskrit+fraksional
            
        return prob_survive_deferral * prob_die_within_n_after_deferral

    # Metode nsp_whole_life_from_assumption dan pv_annuity_due_whole_life_from_assumption
    # tetap sama, menggunakan survival_probability_from_assumption dengan periode integer (float(k))
    def nsp_whole_life_from_assumption(self, age: int, qx_function: Callable[[int], float], px_function: Callable[[int], float], omega: int) -> float:
        present_value_sum: float = 0.0
        for k in range(omega - age): 
            age_at_k: int = age + k
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

    # --- Metode Curtate Future Lifetime Moments Berbasis Asumsi ---
    def ex_curtate_from_assumption(self, age: int, px_function_yearly: Callable[[int], float], omega: int, n_temp: Optional[int] = None) -> float:
        """
        Menghitung e_x atau e_{x:n|} (curtate) menggunakan fungsi px_function_yearly dari asumsi.
        """
        expectation: float = 0.0
        limit_k = n_temp if n_temp is not None else (omega - age)
        
        for k in range(1, limit_k + 1):
            # Periode k adalah integer
            expectation += self.survival_probability_from_assumption(age, float(k), px_function_yearly, omega)
        return expectation

    def e_sq_curtate_from_assumption(self, age: int, px_function_yearly: Callable[[int], float], omega: int, n_temp: Optional[int] = None) -> float:
        """
        Menghitung E[K_x^2] atau E[(K_{x:n|})^2] (curtate) menggunakan fungsi px_function_yearly.
        """
        expectation_sq: float = 0.0
        limit_j = n_temp if n_temp is not None else (omega - age)

        for j in range(limit_j): 
            # Periode j+1 adalah integer
            expectation_sq += (2 * j + 1) * self.survival_probability_from_assumption(age, float(j + 1), px_function_yearly, omega)
        return expectation_sq