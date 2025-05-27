# mortapy/result.py
from IPython.display import display, Math
from typing import Union, Any, Callable # Tambahkan Callable

class ActuarialResult:
    """
    Menampung hasil perhitungan aktuaria, formula LaTeX representatif, dan deskripsi.
    Mendukung operasi aritmatika dasar untuk nilai numeriknya.
    """
    def __init__(self, value: float, formula_latex: str, description: str = ""):
        """
        Inisialisasi objek hasil aktuaria.

        Args:
            value (float): Nilai numerik dari hasil perhitungan.
            formula_latex (str): Representasi simbol LaTeX utama dari hasil.
                                 Contoh: "A_x", "\\ddot{a}_{x:\overline{n}|}".
                                 Tidak perlu menyertakan "$$" atau "= nilai".
            description (str, optional): Deskripsi kontekstual dari hasil. 
                                         Defaults to "".
        """
        self.value: float = value
        self.formula_latex: str = r"{}".format(str(formula_latex).strip('$'))
        self.description: str = str(description)

    def __repr__(self) -> str:
        """Representasi string standar objek untuk debugging atau print()."""
        return f"ActuarialResult(Symbol: '{self.formula_latex}', Value: {self.value:.8f}, Description: '{self.description}')"

    def _repr_latex_(self) -> str:
        """Representasi LaTeX untuk Jupyter Notebook/IPython (dipanggil otomatis)."""
        return f"$$ {self.formula_latex} = {self.value:.8f} $$"

    def show(self) -> None:
        """Secara eksplisit menampilkan output LaTeX dan deskripsi di Jupyter."""
        display(Math(f"{self.formula_latex} = {self.value:.8f}"))
        if self.description:
            print(f"Deskripsi: {self.description}")

    def _combine_results(self, other: Any, op_symbol: str, op_func: Callable[[float, float], float]) -> 'ActuarialResult':
        """Helper internal untuk operasi aritmatika."""
        new_description_parts = []
        if self.description:
            new_description_parts.append(self.description)
        else:
            new_description_parts.append(f"({self.formula_latex})")
        
        new_description_parts.append(op_symbol)

        if isinstance(other, ActuarialResult):
            new_value = op_func(self.value, other.value)
            new_formula = f"({self.formula_latex} {op_symbol} {other.formula_latex})"
            if other.description:
                new_description_parts.append(other.description)
            else:
                new_description_parts.append(f"({other.formula_latex})")
        elif isinstance(other, (int, float)):
            new_value = op_func(self.value, other)
            new_formula = f"({self.formula_latex} {op_symbol} {other})"
            new_description_parts.append(str(other))
        else:
            return NotImplemented
        
        return ActuarialResult(new_value, new_formula, " ".join(new_description_parts))

    def __add__(self, other: Union[float, 'ActuarialResult']) -> 'ActuarialResult':
        """Menambahkan nilai ActuarialResult dengan ActuarialResult lain atau angka."""
        return self._combine_results(other, "+", lambda a, b: a + b)

    def __radd__(self, other: Union[float, 'ActuarialResult']) -> 'ActuarialResult':
        """Menambahkan angka dengan ActuarialResult (operasi reflektif)."""
        return self.__add__(other)

    def __sub__(self, other: Union[float, 'ActuarialResult']) -> 'ActuarialResult':
        """Mengurangkan ActuarialResult lain atau angka dari ActuarialResult ini."""
        return self._combine_results(other, "-", lambda a, b: a - b)

    def __rsub__(self, other: float) -> 'ActuarialResult':
        """Mengurangkan ActuarialResult dari angka (operasi reflektif)."""
        if isinstance(other, (int, float)):
            new_value = other - self.value
            new_formula = f"({other} - {self.formula_latex})"
            new_description = f"{other} - ({self.description or self.formula_latex})"
            return ActuarialResult(new_value, new_formula, new_description)
        return NotImplemented