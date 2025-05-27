# tests/test_latex_renderer.py
from mortapy.latex_renderer import render_actuarial_latex

def test_render_ax():
    assert render_actuarial_latex(r"\Ax{35}") == r"A_{35}"
    assert render_actuarial_latex(r"\Ax{x+t}") == r"A_{x+t}"

def test_render_ax_star():
    assert render_actuarial_latex(r"\Ax*{30}") == r"\overline{A}_{30}"

def test_render_annuity_due():
    assert render_actuarial_latex(r"\ax**{25}") == r"\ddot{a}_{25}"

def test_render_term_insurance():
    assert render_actuarial_latex(r"\term{40}{10}") == r"A_{40:\overline{10}|}^{1}"

def test_no_change_for_basic_latex():
    assert render_actuarial_latex(r"A_x + B_y") == r"A_x + B_y"

def test_multiple_macros():
    assert render_actuarial_latex(r"\Ax{x} + \ax**{y}") == r"A_{x} + \ddot{a}_{y}"