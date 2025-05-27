# mortapy/tables/base.py

import pandas as pd
from typing import Literal, Optional # <<< BARIS INI YANG DITAMBAHKAN/DIPASTIKAN ADA

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
                               CSV harus memiliki kolom 'x', dan setidaknya salah satu
                               dari ('qx_pria', 'qx_wanita') atau 'qx' (untuk tabel unisex).
        
        Raises:
            FileNotFoundError: Jika file tabel mortalita tidak ditemukan.
            KeyError: Jika kolom 'x' tidak ditemukan atau tidak ada kolom qx yang valid.
        """
        try:
            self.table = pd.read_csv(file_path)
            if 'x' not in self.table.columns:
                raise KeyError("Kolom 'x' (usia) tidak ditemukan dalam file CSV.")
            self.table.set_index('x', inplace=True)
            self.max_age = self.table.index.max()

            # Deteksi kolom gender secara otomatis
            self.has_gender_columns = 'qx_pria' in self.table.columns and \
                                      'qx_wanita' in self.table.columns
            self.is_unisex_table = 'qx' in self.table.columns and not self.has_gender_columns

            if not self.has_gender_columns and not self.is_unisex_table:
                raise KeyError("Tidak ditemukan kolom qx yang valid ('qx_pria'/'qx_wanita' atau 'qx').")

        except FileNotFoundError:
            raise FileNotFoundError(f"File tabel mortalita tidak ditemukan di: {file_path}")
        except KeyError as e:
            raise KeyError(f"Kesalahan format kolom di CSV: {e}")

    def __repr__(self) -> str:
        """Representasi string dari objek ini."""
        return f"<MortalityTable max_age={self.max_age}, gender_specific={self.has_gender_columns}, unisex={self.is_unisex_table}>"

    def qx(self, age: int, gender: Optional[Literal['pria', 'wanita']] = None) -> float:
        """
        Mengembalikan probabilitas kematian (qx) pada usia dan gender tertentu.

        Args:
            age (int): Usia.
            gender (Optional[Literal['pria', 'wanita']]): Jenis kelamin. 
                                                        Wajib jika tabel membedakan gender.
                                                        Diabaikan jika tabel unisex.

        Returns:
            float: Nilai qx. Mengembalikan 1.0 jika usia di luar batas tabel atau negatif.
        
        Raises:
            ValueError: Jika gender diperlukan tetapi tidak diberikan, atau gender tidak valid.
        """
        if age < 0 or age > self.max_age : # Usia di luar tabel
            return 1.0
        
        if self.has_gender_columns:
            if gender not in ['pria', 'wanita']:
                raise ValueError("Parameter 'gender' harus 'pria' atau 'wanita' untuk tabel ini.")
            column = 'qx_pria' if gender == 'pria' else 'qx_wanita'
            return self.table.loc[age, column]
        elif self.is_unisex_table:
            # Jika tabel unisex, parameter gender diabaikan
            return self.table.loc[age, 'qx']
        else:
            # Kondisi ini seharusnya tidak tercapai karena __init__ sudah melakukan validasi
            raise LookupError("Struktur kolom qx pada tabel tidak dikenali atau tidak konsisten.")

    def px(self, age: int, gender: Optional[Literal['pria', 'wanita']] = None) -> float:
        """
        Mengembalikan probabilitas bertahan hidup (px) pada usia dan gender tertentu.
        Dihitung sebagai 1 - qx.

        Args:
            Args sama seperti metode qx.

        Returns:
            float: Nilai px.
        """
        return 1.0 - self.qx(age, gender)