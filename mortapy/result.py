# mortapy/result.py

# Impor renderer Anda
from .latex_renderer import render_actuarial_latex

class ActuarialResult:
    def __init__(self, value: float, formula_actsymbol: str):
        """
        Args:
            value (float): Nilai numerik hasil perhitungan.
            formula_actsymbol (str): String formula MENGGUNAKAN makro gaya actuarialsymbol.
                                     Contoh: r"\Ax{x}" atau r"\term{x}{n}"
        """
        self.value = value
        self.original_formula_actsymbol = formula_actsymbol # Simpan formula asli jika perlu
        
        # Render formula ke LaTeX dasar saat objek dibuat
        self.rendered_latex_formula = render_actuarial_latex(formula_actsymbol)

    def __repr__(self):
        # Menampilkan formula yang sudah di-render untuk konsistensi
        return f"Formula: {self.rendered_latex_formula}\nHasil: {self.value:.8f}"

    def _repr_latex_(self):
        """
        Representasi LaTeX untuk Jupyter Notebook / IPython.
        Menggunakan formula yang sudah di-render ke LaTeX dasar.
        """
        return f"$ {self.rendered_latex_formula} = {self.value:.8f} $"