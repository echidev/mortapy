# mortapy/tables/base.py

import pandas as pd
from typing import Literal, Optional
import os # <<< TAMBAHKAN BARIS IMPOR INI

class MortalityTable:
    """
    Kelas untuk memuat dan mengelola data dari tabel mortalita.
    Tabel ini berbasis probabilitas kematian (qx).
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
        self.file_path: str = file_path # Simpan file_path sebagai atribut
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
        # Pastikan self.file_path sudah ada sebelum dipanggil oleh os.path.basename
        filename = os.path.basename(self.file_path) if hasattr(self, 'file_path') and self.file_path else "N/A"
        return f"<MortalityTable path='{filename}', max_age={self.max_age}, gender_specific={self.has_gender_columns}, unisex={self.is_unisex_table}>"

    def qx(self, age: int, gender: Optional[Literal['pria', 'wanita']] = None) -> float:
        """
        Mengembalikan probabilitas kematian tahunan (q_x) pada usia dan gender tertentu.

        Args:
            age (int): Usia yang diminta.
            gender (Optional[Literal['pria', 'wanita']], optional): 
                Jenis kelamin ('pria' atau 'wanita'). Wajib jika tabel memiliki kolom
                gender terpisah. Diabaikan jika tabel unisex. Defaults to None.

        Returns:
            float: Nilai q_x. Mengembalikan 1.0 jika usia berada di luar batas
                   atas tabel (age > max_age) atau jika usia negatif.
        
        Raises:
            ValueError: Jika gender diperlukan untuk tabel ini tetapi tidak diberikan
                        atau nilainya tidak valid.
            LookupError: Jika struktur kolom qx pada tabel tidak dikenali.
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
        Dihitung sebagai 1 - q_x.

        Args:
            age (int): Usia yang diminta.
            gender (Optional[Literal['pria', 'wanita']], optional): Jenis kelamin.
                Lihat dokumentasi metode `qx` untuk detail.

        Returns:
            float: Nilai p_x. Mengembalikan 0.0 jika usia di luar batas atas tabel atau negatif.
        """
        return 1.0 - self.qx(age, gender)