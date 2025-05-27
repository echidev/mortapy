# mortapy/latex_renderer.py
import re

ACTUARIAL_MACRO_MAP = {
    "Ax": (r"\\Ax\{(.*?)\}", r"A_{\1}"),
    "Ax\*": (r"\\Ax\*\{(.*?)\}", r"\\overline{A}_{\1}"), # Tetap double backslash
    "ax\*\*": (r"\\ax\*\*\{(.*?)\}", r"\\ddot{a}_{\1}"),   # Tetap double backslash
    "ax": (r"\\ax\{(.*?)\}", r"a_{\1}"),
    "ax\*": (r"\\ax\*\{(.*?)\}", r"\\overline{a}_{\1}"), # Tetap double backslash
    "lx": (r"\\lx\{(.*?)\}", r"l_{\1}"),
    "dx": (r"\\dx\{(.*?)\}", r"d_{\1}"),
    "px": (r"\\px\{(.*?)\}", r"p_{\1}"),
    "qx": (r"\\qx\{(.*?)\}", r"q_{\1}"),
    "IAx": (r"\\IAx\{(.*?)\}", r"(IA)_{\1}"),
    "term": (r"\\term\{(.*?)\}\{(.*?)\}", r"A_{\1:\\overline{\2}|}^{1}"), # Tetap double backslash
    "endow": (r"\\endow\{(.*?)\}\{(.*?)\}", r"A_{\1:\\overline{\2}|}"), # Tetap double backslash
}

def render_actuarial_latex(actsymbol_string: str) -> str:
    """
    Menerjemahkan subset perintah actuarialsymbol yang umum ke LaTeX dasar
    yang lebih mungkin didukung oleh MathJax/KaTeX.
    """
    processed_string = actsymbol_string
    for macro_name, (pattern, replacement) in ACTUARIAL_MACRO_MAP.items():
        # Kembali ke cara standar re.sub
        # String 'replacement' sudah dalam bentuk raw string yang benar
        # untuk interpretasi oleh re.sub (misal, \\1 menjadi grup 1)
        processed_string = re.sub(pattern, replacement, processed_string)
    
    return processed_string