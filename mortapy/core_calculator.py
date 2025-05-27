# mortapy/core_calculator.py
from typing import Literal, Optional, Callable
from .tables.base import MortalityTable

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
            return 1.0 # Probabilitas mati adalah 1 untuk usia negatif (tidak logis)
        # Metode qx di MortalityTable akan mengembalikan 1.0 jika age >= table.max_age
        return table.qx(age, gender)

    def _get_px_from_table(self, age: int, gender: Literal['pria', 'wanita'], table: MortalityTable) -> float:
        """Mengambil p_x dari objek MortalityTable, menangani batas usia tabel."""
        if age < 0:
            return 0.0 # Probabilitas hidup 0 untuk usia negatif
        return table.px(age, gender)

    def survival_probability_from_table(self, age: int, n_years: int, gender: Literal['pria', 'wanita'], table: MortalityTable) -> float:
        """
        Menghitung probabilitas _n p_x menggunakan MortalityTable.

        Args:
            age (int): Usia awal.
            n_years (int): Jumlah tahun periode.
            gender (Literal['pria', 'wanita']): Jenis kelamin.
            table (MortalityTable): Objek tabel mortalita.

        Returns:
            float: Probabilitas _{n_years}p_{age}.
        """
        if n_years < 0:
            raise ValueError("Jumlah tahun (n_years) tidak boleh negatif.")
        if n_years == 0:
            return 1.0
        
        current_survival_prob: float = 1.0
        for i in range(n_years):
            current_age: int = age + i
            # Pemeriksaan batas dilakukan di dalam _get_px_from_table
            # Jika probabilitas hidup menjadi 0, hasil perkalian selanjutnya akan tetap 0
            if current_survival_prob == 0.0:
                break 
            current_survival_prob *= self._get_px_from_table(current_age, gender, table)
        return current_survival_prob

    def nsp_whole_life_from_table(self, age: int, gender: Literal['pria', 'wanita'], table: MortalityTable) -> float:
        """
        Menghitung Premi Tunggal Bersih (A_x) untuk asuransi jiwa seumur hidup
        menggunakan MortalityTable. Pembayaran benefit di akhir tahun kematian.

        Args:
            age (int): Usia tertanggung.
            gender (Literal['pria', 'wanita']): Jenis kelamin.
            table (MortalityTable): Objek tabel mortalita.

        Returns:
            float: Nilai A_x.
        """
        present_value_sum: float = 0.0
        # Loop hingga usia sebelum usia maksimum di tabel
        for k in range(table.max_age - age): 
            age_at_k: int = age + k
            
            prob_survive_k_years: float = self.survival_probability_from_table(age, k, gender, table)
            if prob_survive_k_years == 0.0 and k > 0: # Optimasi
                break
            prob_die_next_year: float = self._get_qx_from_table(age_at_k, gender, table)
            
            discounted_benefit: float = (self.v ** (k + 1)) * prob_survive_k_years * prob_die_next_year
            present_value_sum += discounted_benefit
        return present_value_sum

    def pv_annuity_due_whole_life_from_table(self, age: int, gender: Literal['pria', 'wanita'], table: MortalityTable) -> float:
        """
        Menghitung nilai sekarang dari anuitas jiwa seumur hidup awal tahun (ä_x)
        menggunakan MortalityTable. Pembayaran 1 setiap awal tahun.

        Args:
            age (int): Usia anuitan.
            gender (Literal['pria', 'wanita']): Jenis kelamin.
            table (MortalityTable): Objek tabel mortalita.

        Returns:
            float: Nilai ä_x.
        """
        present_value_sum: float = 0.0
        # Loop hingga usia maksimum di tabel (inklusif, untuk pembayaran di usia max_age jika masih hidup)
        for k in range(table.max_age - age + 1):
            prob_survive_k_years: float = self.survival_probability_from_table(age, k, gender, table)
            if prob_survive_k_years == 0.0 and k > 0: # Optimasi
                break
            discounted_payment: float = (self.v ** k) * prob_survive_k_years
            present_value_sum += discounted_payment
        return present_value_sum

    # === Metode untuk Asumsi Distribusi Murni ===
    # px_function: sebuah fungsi yang menerima usia (int) dan mengembalikan p_x (float)
    # qx_function: sebuah fungsi yang menerima usia (int) dan mengembalikan q_x (float)
    # omega: usia maksimum absolut untuk asumsi ini

    def survival_probability_from_assumption(self, age: int, n_years: float, px_function: Callable[[int], float], omega: int) -> float:
        """
        Menghitung probabilitas _t p_x menggunakan fungsi p_x(usia_bulat) dari asumsi,
        dan menggunakan asumsi CFM untuk bagian fraksionalnya jika n_years adalah float.

        Args:
            age (int): Usia awal bulat.
            n_years (float): Jumlah tahun periode (bisa fraksional).
            px_function (Callable[[int], float]): Fungsi yang mengembalikan p_x tahunan untuk usia bulat tertentu.
            omega (int): Usia maksimum di bawah asumsi ini.

        Returns:
            float: Probabilitas _{n_years}p_{age}.
        """
        if n_years < 0:
            raise ValueError("Jumlah tahun (n_years) tidak boleh negatif.")
        if n_years == 0:
            return 1.0

        integer_part = int(n_years)
        fractional_part = n_years - integer_part
        
        current_survival_prob: float = 1.0
        # Hitung bagian integer
        for i in range(integer_part):
            current_age_loop: int = age + i
            if current_age_loop >= omega:
                current_survival_prob = 0.0
                break
            current_survival_prob *= px_function(current_age_loop)
        
        # Hitung bagian fraksional menggunakan CFM di atas p_x dari asumsi
        if fractional_part > 0 and current_survival_prob > 0.0:
            age_after_integer_part: int = age + integer_part
            if age_after_integer_part >= omega:
                current_survival_prob = 0.0 # Tidak bisa hidup melewati omega
            else:
                px_for_fractional = px_function(age_after_integer_part)
                current_survival_prob *= (px_for_fractional ** fractional_part) # Asumsi CFM
        
        return current_survival_prob


    def nsp_whole_life_from_assumption(self, age: int, qx_function: Callable[[int], float], px_function: Callable[[int], float], omega: int) -> float:
        present_value_sum: float = 0.0
        for k in range(omega - age): # Loop dari k=0 hingga omega-age-1
            age_at_k: int = age + k
            
            prob_survive_k_years: float = self.survival_probability_from_assumption(age, k, px_function, omega)
            if prob_survive_k_years == 0.0 and k > 0: # Optimasi
                break
            prob_die_next_year: float = qx_function(age_at_k) # q_{x+k}
            
            discounted_benefit: float = (self.v ** (k + 1)) * prob_survive_k_years * prob_die_next_year
            present_value_sum += discounted_benefit
        return present_value_sum

    def pv_annuity_due_whole_life_from_assumption(self, age: int, px_function: Callable[[int], float], omega: int) -> float:
        """Menghitung ä_x menggunakan fungsi p_x dari asumsi."""
        present_value_sum: float = 0.0
        for k in range(omega - age + 1):
            prob_survive_k_years: float = self.survival_probability_from_assumption(age, k, px_function, omega)
            if prob_survive_k_years == 0.0 and k > 0:
                break
            discounted_payment: float = (self.v ** k) * prob_survive_k_years
            present_value_sum += discounted_payment
        return present_value_sum