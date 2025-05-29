# mortapy/tables/base.py
import pandas as pd
from typing import Literal, Optional
import os

class MortalityTable:
    """
    Kelas untuk memuat, mengelola, dan menyediakan akses ke data dari tabel mortalita.
    Mendukung tabel mortalita standar (ultima), dan tabel seleksi & ultima.

    Untuk tabel seleksi, format CSV yang diharapkan memiliki kolom pertama sebagai usia
    saat seleksi (dinamai 'age_select' atau 'x'). Kolom-kolom berikutnya merepresentasikan
    probabilitas kematian q_[x]+t untuk durasi t = 0, 1, ..., select_duration-1.
    Nama kolom durasi diasumsikan 'd0', 'd1', ..., atau jika berbasis gender,
    'd0_pria', 'd0_wanita', 'd1_pria', 'd1_wanita', dst.

    Attributes:
        ultimate_file_path (str): Path ke file CSV tabel mortalita ultima.
        select_file_path (Optional[str]): Path ke file CSV tabel seleksi.
        select_duration (int): Durasi periode seleksi dalam tahun. Bernilai 0 jika bukan tabel seleksi.
        ultimate_table (pd.DataFrame): DataFrame untuk tabel ultima.
        select_table (Optional[pd.DataFrame]): DataFrame untuk tabel seleksi.
        max_age_ultimate (int): Usia maksimum di tabel ultima.
        max_age_select (Optional[int]): Usia maksimum saat seleksi di tabel seleksi.
        min_age_select (Optional[int]): Usia minimum saat seleksi di tabel seleksi.
        has_gender_columns_ultimate (bool): True jika tabel ultima memiliki kolom qx terpisah gender.
        is_unisex_ultimate (bool): True jika tabel ultima adalah unisex.
        has_gender_columns_select (bool): True jika tabel seleksi memiliki kolom qx terpisah gender.
        is_unisex_select (bool): True jika tabel seleksi adalah unisex (berdasarkan nama kolom d0, d1, ...).
        is_select_and_ultimate (bool): True jika tabel ini adalah model seleksi & ultima.
    """
    def __init__(self,
                 ultimate_file_path: str,
                 select_file_path: Optional[str] = None,
                 select_duration: Optional[int] = None):
        """
        Inisialisasi dan memuat tabel mortalita.

        Args:
            ultimate_file_path (str): Path ke file CSV tabel mortalita ultima.
            select_file_path (Optional[str], optional): Path ke file CSV tabel seleksi.
            select_duration (Optional[int], optional): Durasi periode seleksi. Wajib jika select_file_path ada.

        Raises:
            FileNotFoundError, ValueError, KeyError: Sesuai kondisi error.
        """
        self.ultimate_file_path: str = ultimate_file_path
        self.select_file_path: Optional[str] = select_file_path
        self.select_duration: int = select_duration if select_duration is not None else 0
        self.is_select_and_ultimate: bool = bool(select_file_path and self.select_duration > 0)

        if select_file_path and not select_duration:
            raise ValueError("Jika 'select_file_path' diberikan, 'select_duration' (positif) juga harus diberikan.")
        if not select_file_path and select_duration and select_duration > 0:
            raise ValueError("Jika 'select_duration' diberikan, 'select_file_path' juga harus diberikan.")
        if select_duration is not None and select_duration < 0:
            raise ValueError("select_duration tidak boleh negatif.")

        # Load ultimate table
        try:
            self.ultimate_table: pd.DataFrame = pd.read_csv(ultimate_file_path)
            if 'x' not in self.ultimate_table.columns:
                self.ultimate_table.rename(columns={self.ultimate_table.columns[0]: 'x'}, inplace=True) # Asumsi kolom pertama 'x'
            if 'x' not in self.ultimate_table.columns:
                raise KeyError("Kolom 'x' (usia) tidak ditemukan dalam file CSV tabel ultima.")
            self.ultimate_table.set_index('x', inplace=True)
            self.max_age_ultimate: int = self.ultimate_table.index.max()

            self.has_gender_columns_ultimate: bool = 'qx_pria' in self.ultimate_table.columns and \
                                                    'qx_wanita' in self.ultimate_table.columns
            self.is_unisex_ultimate: bool = 'qx' in self.ultimate_table.columns and \
                                           not self.has_gender_columns_ultimate
            if not self.has_gender_columns_ultimate and not self.is_unisex_ultimate:
                raise KeyError("Tabel ultima tidak memiliki kolom qx yang valid.")
        except FileNotFoundError:
            raise FileNotFoundError(f"File tabel ultima tidak ditemukan: {self.ultimate_file_path}")
        except Exception as e:
            raise RuntimeError(f"Error memuat tabel ultima '{self.ultimate_file_path}': {e}")

        # Load select table
        self.select_table: Optional[pd.DataFrame] = None
        self.max_age_select: Optional[int] = None
        self.min_age_select: Optional[int] = None
        self.has_gender_columns_select: bool = False
        self.is_unisex_select: bool = False
        self._select_col_prefix = "d" # Asumsi d0, d1, ... atau d0_gender, d1_gender, ...

        if self.is_select_and_ultimate and self.select_file_path:
            try:
                self.select_table = pd.read_csv(self.select_file_path)
                if self.select_table.columns[0] != 'age_select':
                    self.select_table.rename(columns={self.select_table.columns[0]: 'age_select'}, inplace=True)
                if 'age_select' not in self.select_table.columns:
                    raise KeyError("Kolom 'age_select' tidak ditemukan di tabel seleksi.")
                self.select_table.set_index('age_select', inplace=True)
                self.max_age_select = self.select_table.index.max()
                self.min_age_select = self.select_table.index.min()

                # Deteksi format gender tabel seleksi
                # Cek apakah ada kolom seperti d0_pria atau d0_wanita
                self.has_gender_columns_select = any(f"{self._select_col_prefix}0_pria" in col for col in self.select_table.columns) and \
                                                 any(f"{self._select_col_prefix}0_wanita" in col for col in self.select_table.columns)
                self.is_unisex_select = any(f"{self._select_col_prefix}0" == col for col in self.select_table.columns) and \
                                        not self.has_gender_columns_select
                
                if not self.has_gender_columns_select and not self.is_unisex_select:
                     # Mungkin tabel select hanya punya satu set kolom (misal hanya pria, atau unisex tanpa pembeda)
                     # Untuk sementara, asumsikan unisex jika tidak ada _pria/_wanita
                     if not any("_pria" in col or "_wanita" in col for col in self.select_table.columns):
                         self.is_unisex_select = True 
                     else: # Jika ada _pria tapi tidak _wanita, atau sebaliknya, ini masalah
                         raise KeyError("Format kolom gender di tabel seleksi tidak konsisten atau tidak lengkap.")

            except FileNotFoundError:
                raise FileNotFoundError(f"File tabel seleksi tidak ditemukan: {self.select_file_path}")
            except Exception as e:
                raise RuntimeError(f"Error memuat tabel seleksi '{self.select_file_path}': {e}")

    def __repr__(self) -> str:
        ultimate_fn = os.path.basename(self.ultimate_file_path) if self.ultimate_file_path else "N/A"
        repr_str = f"<MortalityTable ultimate='{ultimate_fn}'"
        if self.is_select_and_ultimate and self.select_file_path:
            select_fn = os.path.basename(self.select_file_path)
            repr_str += f", select='{select_fn}', select_duration={self.select_duration}"
        repr_str += ">"
        return repr_str

    def get_qx(self,
               attained_age: int,
               gender: Optional[Literal['pria', 'wanita']] = None,
               age_at_selection: Optional[int] = None,
               duration_since_selection: Optional[int] = None) -> float:
        """
        Mengembalikan probabilitas kematian tahunan (q) dengan mempertimbangkan periode seleksi.

        Args:
            attained_age (int): Usia yang dicapai saat ini.
            gender (Optional[Literal['pria', 'wanita']]): Jenis kelamin.
            age_at_selection (Optional[int]): Usia saat pertama kali diseleksi ([x]).
            duration_since_selection (Optional[int]): Durasi dalam tahun sejak seleksi (t).

        Returns:
            float: Nilai q. Mengembalikan 1.0 jika usia di luar batas tabel ultima.
        """
        if attained_age < 0: return 1.0

        use_select_logic = False
        if self.is_select_and_ultimate and \
           age_at_selection is not None and \
           duration_since_selection is not None and \
           self.select_table is not None:
            if duration_since_selection < self.select_duration:
                # Periksa apakah usia seleksi ada di tabel seleksi
                if self.min_age_select is not None and self.max_age_select is not None and \
                   self.min_age_select <= age_at_selection <= self.max_age_select:
                    use_select_logic = True

        if use_select_logic and self.select_table is not None:
            col_name_base = f"{self._select_col_prefix}{duration_since_selection}"
            final_col_name = col_name_base
            
            # Menentukan nama kolom berdasarkan gender untuk tabel seleksi
            gender_specific_select = self.has_gender_columns_select
            if gender_specific_select:
                if gender not in ['pria', 'wanita']:
                    raise ValueError("Gender tidak valid untuk tabel seleksi berbasis gender.")
                final_col_name += "_pria" if gender == 'pria' else "_wanita"
            # Jika tidak gender-specific, nama kolomnya tetap col_name_base (misal, "d0")

            if final_col_name in self.select_table.columns and age_at_selection in self.select_table.index:
                return self.select_table.loc[age_at_selection, final_col_name] # type: ignore
            else:
                # Fallback ke tabel ultima jika kolom/usia seleksi tidak ditemukan
                return self.qx_ultima(attained_age, gender)
        else: # Gunakan tabel ultima
            return self.qx_ultima(attained_age, gender)

    def get_px(self,
               attained_age: int,
               gender: Optional[Literal['pria', 'wanita']] = None,
               age_at_selection: Optional[int] = None,
               duration_since_selection: Optional[int] = None) -> float:
        """Mengembalikan probabilitas hidup tahunan (p) dengan mempertimbangkan periode seleksi."""
        return 1.0 - self.get_qx(attained_age, gender, age_at_selection, duration_since_selection)

    def qx_ultima(self, age: int, gender: Optional[Literal['pria', 'wanita']] = None) -> float:
        """Mengembalikan q_x hanya dari tabel ultima."""
        if age < 0 or age > self.max_age_ultimate: return 1.0
        col_name = self._get_ultimate_col_name(gender)
        return self.ultimate_table.loc[age, col_name]

    def px_ultima(self, age: int, gender: Optional[Literal['pria', 'wanita']] = None) -> float:
        """Mengembalikan p_x hanya dari tabel ultima."""
        return 1.0 - self.qx_ultima(age, gender)

    def _get_ultimate_col_name(self, gender: Optional[Literal['pria', 'wanita']]) -> str:
        """Helper untuk mendapatkan nama kolom qx dari tabel ultima."""
        if self.has_gender_columns_ultimate:
            if gender not in ['pria', 'wanita']:
                raise ValueError("Parameter 'gender' harus 'pria' atau 'wanita' untuk tabel ultima berbasis gender ini.")
            return 'qx_pria' if gender == 'pria' else 'qx_wanita'
        elif self.is_unisex_ultimate:
            return 'qx'
        else:
            raise LookupError("Struktur kolom qx pada tabel ultima tidak dikenali.")