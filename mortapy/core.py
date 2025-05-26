# mortapy/core.py

from .tables.base import MortalityTable
from typing import Literal

class ActuarialCalculator:
    """
    Kelas yang berisi logika inti untuk perhitungan aktuaria
    berdasarkan tabel mortalita dan suku bunga.
    """
    def __init__(self, mortality_table: MortalityTable, interest_rate: float):
        """
        Inisialisasi kalkulator.

        Args:
            mortality_table (MortalityTable): Objek tabel mortalita yang sudah dimuat.
            interest_rate (float): Tingkat suku bunga, misal: 0.05 untuk 5%.
        """
        self.table = mortality_table
        self.interest_rate = interest_rate
        self.v = 1 / (1 + interest_rate)  # Faktor diskon

    def p(self, age: int, n: int, gender: Literal['pria', 'wanita'] = 'pria') -> float:
        """
        Menghitung probabilitas seseorang berusia (age) akan bertahan hidup n tahun ke depan (_n_p_x).
        """
        if n == 0:
            return 1.0
        
        prob = 1.0
        for i in range(n):
            prob *= self.table.px(age + i, gender)
        return prob

    def Ax(self, age: int, gender: Literal['pria', 'wanita'] = 'pria') -> float:
        """
        Menghitung Premi Tunggal Bersih (Net Single Premium) untuk asuransi jiwa seumur hidup (whole life).
        Dibayarkan pada akhir tahun kematian.

        Formula: A_x = sum(v^(k+1) * k_p_x * q_(x+k))
        """
        total_pv = 0
        # Loop dari usia saat ini hingga usia maksimal di tabel
        for k in range(self.table.max_age - age + 1):
            # Probabilitas meninggal antara usia (age+k) dan (age+k+1)
            prob_meninggal_tahun_k = self.p(age, k, gender) * self.table.qx(age + k, gender)
            
            # Nilai sekarang dari pembayaran 1 di akhir tahun ke-(k+1)
            present_value = (self.v ** (k + 1)) * prob_meninggal_tahun_k
            total_pv += present_value
            
        return total_pv

    def a_due_x(self, age: int, gender: Literal['pria', 'wanita'] = 'pria') -> float:
        """
        Menghitung nilai sekarang dari anuitas jiwa seumur hidup awal tahun (annuity due).
        Pembayaran 1 setiap awal tahun selama tertanggung masih hidup.
        """
        total_pv = 0
        # Loop dari usia saat ini hingga usia maksimal di tabel
        for k in range(self.table.max_age - age + 1):
            # Probabilitas masih hidup pada usia (age+k) untuk menerima pembayaran
            prob_hidup = self.p(age, k, gender)
            
            # Nilai sekarang dari pembayaran 1 di awal tahun ke-k
            present_value = (self.v ** k) * prob_hidup
            total_pv += present_value

        return total_pv