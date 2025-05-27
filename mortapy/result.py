# mortapy/result.py
from IPython.display import display, Math 

class ActuarialResult:
    """
    Sebuah kelas untuk menampung hasil perhitungan aktuaria,
    beserta formula LaTeX-nya.
    """
    def __init__(self, value: float, formula_to_render: str):
        """
        Inisialisasi objek hasil aktuaria.

        Args:
            value (float): Nilai numerik dari hasil perhitungan.
            formula_to_render (str): String formula LaTeX MENTAH (tanpa apitan $$)
                                     yang akan di-render.
        """
        self.value = value
        # Simpan string formula mentah ke atribut self.formula_latex
        self.formula_latex = r"{}".format(str(formula_to_render).strip('$'))

    def __repr__(self):
        """Representasi teks standar (misal: saat di-print)."""
        # Menampilkan formula yang akan di-render dan hasilnya
        return f"Formula (LaTeX): {self.formula_latex}\nHasil: {self.value:.8f}"

    def _repr_latex_(self):
        """
        Representasi LaTeX untuk Jupyter Notebook / IPython.
        Menampilkan: $$ FORMULA = HASIL $$
        """
        # Pastikan self.formula_latex adalah string LaTeX yang valid
        return f"$ {self.formula_latex} = {self.value:.8f} $"

    def show(self): # Atau display_latex(), atau render()
        """Secara eksplisit menampilkan output LaTeX di Jupyter."""
        # Menggunakan display(Math(...)) untuk merender LaTeX
        # dan display(HTML(...)) untuk deskripsi jika ada
        display(Math(f"{self.formula_latex} = {self.value:.8f}"))
        # Jika Anda ingin mengembalikan deskripsi juga (yang kita hapus sebelumnya):
        # display(HTML(f"<p><strong>{self.description}</strong></p>"))
        # display(HTML(f"<p>Nilai: {self.value:.8f}</p>"))