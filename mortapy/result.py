# mortapy/result.py
from IPython.display import display, Math
from typing import Union, Any, Callable

class ActuarialResult:
    """
    Menampung hasil numerik dari perhitungan aktuaria, representasi formula
    LaTeX-nya, dan deskripsi kontekstual.

    Kelas ini juga mendukung operasi aritmatika dasar (+, -) yang memungkinkan
    kombinasi intuitif dari berbagai hasil aktuaria. Outputnya dapat
    ditampilkan secara kaya (LaTeX) di lingkungan Jupyter Notebook.

    Attributes:
        value (float): Nilai numerik dari hasil perhitungan.
        formula_latex (str): Representasi simbol LaTeX utama dari hasil (tanpa apitan $$).
        description (str): Deskripsi tekstual mengenai hasil perhitungan.
    """
    def __init__(self, value: float, formula_latex: str, description: str = ""):
        """
        Inisialisasi objek ActuarialResult.

        Args:
            value (float): Nilai numerik dari hasil perhitungan.
            formula_latex (str): Representasi simbol LaTeX utama dari hasil.
                                 Contoh: "A_x", "\\ddot{a}_{x:\\overline{n}|}".
                                 Sebaiknya tidak menyertakan "$$" atau "= nilai".
            description (str, optional): Deskripsi kontekstual dari hasil.
                                         Defaults to "".
        """
        self.value: float = value
        self.formula_latex: str = str(formula_latex).strip('$')
        self.description: str = str(description)

    def __repr__(self) -> str:
        """
        Representasi string standar objek, berguna untuk debugging atau saat
        fungsi print() dipanggil pada objek ini.

        Returns:
            str: Representasi string dari objek ActuarialResult.
        """
        return f"ActuarialResult(Symbol: '{self.formula_latex}', Value: {self.value:.8f}, Description: '{self.description}')"

    def _repr_latex_(self) -> str:
        """
        Representasi LaTeX untuk Jupyter Notebook/IPython.
        Metode ini dipanggil secara otomatis oleh lingkungan Jupyter/IPython
        ketika objek ini adalah ekspresi terakhir dalam sebuah sel.
        Menghasilkan string LaTeX yang akan di-render.

        Returns:
            str: String LaTeX dalam format display math ("$$ FORMULA = HASIL $$").
        """
        return f"$$ {self.formula_latex} = {self.value:.8f} $$"

    def show(self) -> None:
        """
        Secara eksplisit menampilkan output LaTeX dan deskripsi di lingkungan
        Jupyter/IPython menggunakan IPython.display.
        Ini berguna jika ingin menampilkan hasil di tengah-tengah sel atau
        bersama output lain.
        """
        display(Math(f"{self.formula_latex} = {self.value:.8f}"))
        if self.description:
            print(f"Deskripsi: {self.description}")

    def _combine_results(self, other: Any, op_symbol: str, op_func: Callable[[float, float], float]) -> 'ActuarialResult':
        """
        Helper internal untuk menangani logika operasi aritmatika.

        Args:
            other (Any): Objek atau angka lain yang akan dioperasikan.
            op_symbol (str): Simbol operasi dalam bentuk string (misal: "+", "-").
            op_func (Callable[[float, float], float]): Fungsi yang melakukan operasi numerik (misal: lambda a,b: a+b).

        Returns:
            ActuarialResult: Objek ActuarialResult baru hasil operasi.

        Raises:
            NotImplemented: Jika tipe 'other' tidak didukung.
        """
        new_description_parts = []
        current_desc_or_formula = self.description if self.description else f"({self.formula_latex})"
        new_description_parts.append(current_desc_or_formula)
        new_description_parts.append(op_symbol)

        if isinstance(other, ActuarialResult):
            new_value = op_func(self.value, other.value)
            new_formula = f"({self.formula_latex} {op_symbol} {other.formula_latex})"
            other_desc_or_formula = other.description if other.description else f"({other.formula_latex})"
            new_description_parts.append(other_desc_or_formula)
        elif isinstance(other, (int, float)):
            new_value = op_func(self.value, other)
            new_formula = f"({self.formula_latex} {op_symbol} {other})"
            new_description_parts.append(str(other))
        else:
            return NotImplemented

        return ActuarialResult(new_value, new_formula, " ".join(new_description_parts))

    def __add__(self, other: Union[float, 'ActuarialResult']) -> 'ActuarialResult':
        """Mendefinisikan operasi penjumlahan (self + other)."""
        return self._combine_results(other, "+", lambda a, b: a + b)

    def __radd__(self, other: Union[float, 'ActuarialResult']) -> 'ActuarialResult':
        """Mendefinisikan operasi penjumlahan reflektif (other + self)."""
        if isinstance(other, (int, float)):
            new_value = other + self.value
            new_formula = f"({other} + {self.formula_latex})"
            self_desc_part = self.description if self.description else f"({self.formula_latex})"
            new_description = f"{other} + {self_desc_part}"
            return ActuarialResult(new_value, new_formula, new_description)
        return NotImplemented

    def __sub__(self, other: Union[float, 'ActuarialResult']) -> 'ActuarialResult':
        """Mendefinisikan operasi pengurangan (self - other)."""
        return self._combine_results(other, "-", lambda a, b: a - b)

    def __rsub__(self, other: float) -> 'ActuarialResult':
        """Mendefinisikan operasi pengurangan reflektif (other - self)."""
        if isinstance(other, (int, float)):
            new_value = other - self.value
            new_formula = f"({other} - {self.formula_latex})"
            self_desc_part = self.description if self.description else f"({self.formula_latex})"
            new_description = f"{other} - {self_desc_part}"
            return ActuarialResult(new_value, new_formula, new_description)
        return NotImplemented