# mortapy/core.py

from .tables.base import MortalityTable
from typing import Literal, Optional # Tambahkan Optional

class ActuarialCalculator:
    def __init__(self, 
                 interest_rate: float, 
                 mortality_table: Optional[MortalityTable] = None,
                 base_qx: Optional[float] = None,
                 base_px: Optional[float] = None):
        """
        Inisialisasi kalkulator.

        Args:
            interest_rate (float): Tingkat suku bunga.
            mortality_table (Optional[MortalityTable]): Objek tabel mortalita.
            base_qx (Optional[float]): Nilai qx dasar jika tidak menggunakan tabel.
            base_px (Optional[float]): Nilai px dasar jika tidak menggunakan tabel.
                                       Jika base_qx diberikan, base_px akan diabaikan.
        """
        self.interest_rate = interest_rate
        self.v = 1 / (1 + interest_rate)
        self.mortality_table = mortality_table
        self.base_qx = base_qx
        self.base_px = base_px

        if self.mortality_table is None and self.base_qx is None and self.base_px is None:
            raise ValueError("Harus menyediakan mortality_table, base_qx, atau base_px.")
        
        if self.base_qx is not None and (self.base_qx < 0 or self.base_qx > 1):
            raise ValueError("base_qx harus antara 0 dan 1.")
        
        if self.base_px is not None and self.base_qx is None and (self.base_px < 0 or self.base_px > 1):
            # base_px hanya digunakan jika base_qx tidak ada
            raise ValueError("base_px harus antara 0 dan 1.")

    def _get_qx(self, age: int, gender: Optional[Literal['pria', 'wanita']] = None) -> float:
        """Helper internal untuk mendapatkan qx."""
        if self.base_qx is not None:
            # Jika qx ditetapkan, gender dan tabel diabaikan untuk nilai dasar ini
            # Namun, usia 'age' mungkin tetap relevan jika qx adalah fungsi dari usia
            # Untuk sekarang, kita asumsikan base_qx adalah nilai tunggal jika diberikan.
            # Atau, base_qx bisa berupa fungsi: self.base_qx(age)
            # Untuk kesederhanaan awal, kita anggap base_qx adalah nilai tetap.
            return self.base_qx
        if self.mortality_table:
            if gender is None and (self.mortality_table.table.columns.str.contains('pria').any() or \
                                   self.mortality_table.table.columns.str.contains('wanita').any()):
                raise ValueError("Parameter 'gender' harus diisi jika menggunakan tabel mortalita berbasis gender.")
            return self.mortality_table.qx(age, gender if gender else 'pria') # Default ke pria jika gender None tapi tabel ada kolom gender (meski harusnya error di atas)
        # Jika base_px diberikan (dan base_qx tidak), hitung qx
        if self.base_px is not None:
            return 1.0 - self.base_px
        
        # Seharusnya tidak pernah sampai sini karena __init__ sudah validasi
        raise ValueError("Tidak ada sumber untuk qx (tabel, base_qx, atau base_px).")


    def _get_px(self, age: int, gender: Optional[Literal['pria', 'wanita']] = None) -> float:
        """Helper internal untuk mendapatkan px."""
        if self.base_px is not None and self.base_qx is None:
            # Jika px ditetapkan dan qx tidak, gender dan tabel diabaikan
            return self.base_px
        # Jika base_qx ada atau tabel ada, hitung dari qx
        return 1.0 - self._get_qx(age, gender)

    # --- Ubah semua metode yang menggunakan self.table.qx atau self.table.px ---
    # --- untuk menggunakan self._get_qx atau self._get_px ---

    def p(self, age: int, n: int, gender: Optional[Literal['pria', 'wanita']] = None) -> float:
        """Menghitung _n_p_x."""
        if n == 0:
            return 1.0
        prob = 1.0
        for i in range(n):
            prob *= self._get_px(age + i, gender) # Gunakan helper
        return prob
    
    # Di dalam kelas ActuarialCalculator di mortapy/core.py

    def p_frac(self, age: int, n: float, gender: Optional[Literal['pria', 'wanita']] = None, assumption: Literal['udd', 'cfm'] = 'udd') -> float:
        """
        Menghitung probabilitas hidup untuk periode non-bulat (_n_p_x)
        dengan asumsi UDD atau CFM.
        """
        if n < 0:
            return 0.0

        integer_part = int(n)
        fractional_part = n - integer_part

        prob_integer = self.p(age, integer_part, gender) # Menggunakan metode p() yang sudah ada

        if fractional_part == 0:
            return prob_integer

        age_after_integer_part = age + integer_part
        prob_fractional = 0.0

        if assumption == 'udd':
            # Formula UDD: _t_p_x = 1 - t * q_x
            # Di sini qx diambil dari usia setelah bagian bulat
            qx_frac = self._get_qx(age_after_integer_part, gender)
            prob_fractional = 1.0 - fractional_part * qx_frac

        elif assumption == 'cfm':
            # Formula CFM: _t_p_x = (p_x)^t
            # Di sini px diambil dari usia setelah bagian bulat
            px_frac = self._get_px(age_after_integer_part, gender)
            prob_fractional = px_frac ** fractional_part

        else:
            raise ValueError("Asumsi tidak valid. Harap pilih 'udd' atau 'cfm'.")

        return prob_integer * prob_fractional

    def Ax(self, age: int, gender: Optional[Literal['pria', 'wanita']] = None) -> float:
        """Menghitung A_x."""
        total_pv = 0
        # Batas loop mungkin perlu penyesuaian jika tidak pakai tabel (misal, hingga usia 120)
        # Untuk saat ini, kita asumsikan jika tidak ada tabel, base_qx berlaku universal
        # atau kita perlu cara lain untuk menentukan omega.
        # Demi kesederhanaan, kita batasi loop hingga usia tertentu jika tidak ada tabel
        max_calculation_age = self.mortality_table.max_age if self.mortality_table else 120 

        for k in range(max_calculation_age - age + 1):
            prob_survival_k_years = self.p(age, k, gender) # Ini sudah menggunakan _get_px
            prob_death_next_year = self._get_qx(age + k, gender) # Gunakan helper
            
            present_value = (self.v ** (k + 1)) * prob_survival_k_years * prob_death_next_year
            total_pv += present_value
        return total_pv

    def a_due_x(self, age: int, gender: Optional[Literal['pria', 'wanita']] = None) -> float:
        """Menghitung a_due_x."""
        total_pv = 0
        max_calculation_age = self.mortality_table.max_age if self.mortality_table else 120

        for k in range(max_calculation_age - age + 1):
            prob_survival_k_years = self.p(age, k, gender) # Ini sudah menggunakan _get_px
            present_value = (self.v ** k) * prob_survival_k_years
            total_pv += present_value
        return total_pv
        
    # Fungsi p_frac untuk usia non-bulat akan Anda kerjakan nanti di branch lain.
    # Jika Anda menyentuhnya sekarang, pastikan ia juga menggunakan _get_qx/_get_px.