# mortapy/tables/base.py

import pandas as pd
from typing import Literal

class MortalityTable:
    """
    Kelas untuk memuat dan mengelola data dari tabel mortalita.
    Tabel ini berbasis probabilitas kematian (qx).
    """
    def __init__(self, file_path: str):
        """
        Inisialisasi tabel mortalita dari sebuah file CSV.

        Args:
            file_path (str): Path lengkap menuju file .csv.
                               CSV harus memiliki kolom 'x', 'qx_pria', dan 'qx_wanita'.
        """
        try:
            self.table = pd.read_csv(file_path)
            self.table.set_index('x', inplace=True)
            self.max_age = self.table.index.max()
        except FileNotFoundError:
            raise FileNotFoundError(f"File tabel mortalita tidak ditemukan di: {file_path}")
        except KeyError:
            raise KeyError("CSV harus memiliki kolom 'x', 'qx_pria', dan 'qx_wanita'.")

    def __repr__(self) -> str:
        """Representasi string dari objek ini."""
        return f"<MortalityTable max_age={self.max_age}>"

    def qx(self, age: int, gender: Literal['pria', 'wanita'] = 'pria') -> float:
        """
        Mengembalikan probabilitas kematian (qx) pada usia dan gender tertentu.

        Args:
            age (int): Usia.
            gender (Literal['pria', 'wanita']): Jenis kelamin. Default 'pria'.

        Returns:
            float: Nilai qx. Mengembalikan 1.0 jika usia di luar batas tabel.
        """
        if age > self.max_age or age < 0:
            return 1.0
        
        column = 'qx_pria' if gender == 'pria' else 'qx_wanita'
        return self.table.loc[age, column]

    def px(self, age: int, gender: Literal['pria', 'wanita'] = 'pria') -> float:
        """
        Mengembalikan probabilitas bertahan hidup (px) pada usia dan gender tertentu.
        Dihitung sebagai 1 - qx.

        Args:
            age (int): Usia.
            gender (Literal['pria', 'wanita']): Jenis kelamin. Default 'pria'.

        Returns:
            float: Nilai px.
        """
        return 1.0 - self.qx(age, gender)