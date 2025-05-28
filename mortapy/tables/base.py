# mortapy/tables/base.py
import pandas as pd
from typing import Literal, Optional
import os # Ditambahkan untuk os.path.basename di __repr__

class MortalityTable:
    """
    Kelas untuk memuat, mengelola, dan menyediakan akses ke data dari tabel mortalita.
    Mendukung tabel mortalita dengan pembedaan gender ('qx_pria', 'qx_wanita')
    atau tabel unisex ('qx').

    Attributes:
        file_path (str): Path ke file CSV tabel mortalita.
        table (pd.DataFrame): DataFrame pandas yang menyimpan data mortalita.
        max_age (int): Usia maksimum yang ada dalam tabel.
        has_gender_columns (bool): True jika tabel memiliki kolom qx terpisah untuk pria dan wanita.
        is_unisex_table (bool): True jika tabel memiliki satu kolom 'qx' dan bukan berbasis gender.
    """
    def __init__(self, file_path: str):
        """
        Inisialisasi dan memuat tabel mortalita dari sebuah file CSV.

        Args:
            file_path (str): Path lengkap menuju file .csv.
                               File CSV harus memiliki kolom 'x' (usia), dan setidaknya
                               salah satu dari ('qx_pria' dan 'qx_wanita') atau hanya 'qx'.

        Raises:
            FileNotFoundError: Jika file tabel mortalita pada `file_path` tidak ditemukan.
            KeyError: Jika kolom 'x' tidak ada, atau jika tidak ada kolom qx yang
                      valid ('qx_pria'/'qx_wanita' atau 'qx').
        """
        self.file_path: str = file_path
        try:
            self.table: pd.DataFrame = pd.read_csv(file_path)
            if 'x' not in self.table.columns:
                raise KeyError("Kolom 'x' (usia) tidak ditemukan dalam file CSV.")
            self.table.set_index('x', inplace=True)
            self.max_age: int = self.table.index.max()

            self.has_gender_columns: bool = 'qx_pria' in self.table.columns and \
                                           'qx_wanita' in self.table.columns
            self.is_unisex_table: bool = 'qx' in self.table.columns and not self.has_gender_columns

            if not self.has_gender_columns and not self.is_unisex_table:
                raise KeyError("Tidak ditemukan kolom qx yang valid dalam CSV ('qx_pria' & 'qx_wanita', atau 'qx').")

        except FileNotFoundError:
            raise FileNotFoundError(f"File tabel mortalita tidak ditemukan di: {self.file_path}")
        except KeyError as e:
            raise KeyError(f"Kesalahan format kolom di CSV '{self.file_path}': {e}")

    def __repr__(self) -> str:
        """
        Representasi string standar objek MortalityTable.

        Returns:
            str: Informasi mengenai tabel mortalita.
        """
        filename = os.path.basename(self.file_path) if hasattr(self, 'file_path') and self.file_path else "N/A"
        return f"<MortalityTable path='{filename}', max_age={self.max_age}, gender_specific={self.has_gender_columns}, unisex={self.is_unisex_table}>"

    def qx(self, age: int, gender: Optional[Literal['pria', 'wanita']] = None) -> float:
        """
        Mengembalikan probabilitas kematian tahunan (q_x) pada usia dan gender tertentu.
        """
        if age < 0 or age > self.max_age :
            return 1.0
        
        if self.has_gender_columns:
            if gender not in ['pria', 'wanita']:
                raise ValueError("Parameter 'gender' harus 'pria' atau 'wanita' untuk tabel berbasis gender ini.")
            column_name = 'qx_pria' if gender == 'pria' else 'qx_wanita'
            return self.table.loc[age, column_name]
        elif self.is_unisex_table:
            return self.table.loc[age, 'qx']
        else:
            raise LookupError("Tabel tidak terdefinisi sebagai gender-specific maupun unisex.")

    def px(self, age: int, gender: Optional[Literal['pria', 'wanita']] = None) -> float:
        """
        Mengembalikan probabilitas bertahan hidup tahunan (p_x) pada usia dan gender tertentu.
        """
        return 1.0 - self.qx(age, gender)