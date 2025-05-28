# tests/test_result.py
import pytest
from mortapy.result import ActuarialResult 
from typing import Union, Any, Callable 

def test_actuarial_result_creation():
    res = ActuarialResult(value=0.123, formula_latex="A_x", description="NSP Test")
    assert res.value == 0.123
    assert res.formula_latex == "A_x"
    assert res.description == "NSP Test"
    assert "Symbol: 'A_x'" in repr(res)
    assert "Value: 0.12300000" in repr(res)
    assert "Description: 'NSP Test'" in repr(res)
    assert res._repr_latex_() == "$$ A_x = 0.12300000 $$"

def test_actuarial_result_addition():
    res1 = ActuarialResult(0.1, "A_x", "Premi A")
    res2 = ActuarialResult(0.2, "A_y", "Premi B")
    
    res_sum1 = res1 + res2
    assert isinstance(res_sum1, ActuarialResult)
    assert res_sum1.value == pytest.approx(0.3)
    assert res_sum1.formula_latex == "(A_x + A_y)"
    assert "Premi A + Premi B" in res_sum1.description

    res_sum2 = res1 + 0.05
    assert isinstance(res_sum2, ActuarialResult)
    assert res_sum2.value == pytest.approx(0.15)
    assert res_sum2.formula_latex == "(A_x + 0.05)"
    assert "Premi A + 0.05" in res_sum2.description
    
    res_sum3 = 0.07 + res1
    assert isinstance(res_sum3, ActuarialResult)
    assert res_sum3.value == pytest.approx(0.17)
    assert res_sum3.formula_latex == f"(0.07 + {res1.formula_latex})" # <<< PERBAIKAN FORMULA
    assert f"0.07 + ({res1.description or '('+res1.formula_latex+')'})" in res_sum3.description # <<< PERBAIKAN DESKRIPSI

def test_actuarial_result_subtraction():
    res1 = ActuarialResult(0.3, "Term_A", "Premi Term A")
    res2 = ActuarialResult(0.1, "Term_B", "Premi Term B")

    res_diff1 = res1 - res2
    assert isinstance(res_diff1, ActuarialResult)
    assert res_diff1.value == pytest.approx(0.2)
    assert res_diff1.formula_latex == "(Term_A - Term_B)"

    res_diff2 = res1 - 0.05
    assert isinstance(res_diff2, ActuarialResult)
    assert res_diff2.value == pytest.approx(0.25)
    assert res_diff2.formula_latex == "(Term_A - 0.05)"

    res_diff3 = 0.5 - res1
    assert isinstance(res_diff3, ActuarialResult)
    assert res_diff3.value == pytest.approx(0.2)
    assert res_diff3.formula_latex == "(0.5 - Term_A)"

def test_actuarial_result_repr_latex_no_description():
    res = ActuarialResult(value=0.555, formula_latex="P_x")
    assert res._repr_latex_() == "$$ P_x = 0.55500000 $$"

def test_combine_results_description_handling():
    res_desc = ActuarialResult(1, "F1", "Hasil Pertama")
    res_no_desc = ActuarialResult(2, "F2") 

    sum_res = res_desc + res_no_desc
    assert sum_res.description == "Hasil Pertama + (F2)"

    sum_res_rev = res_no_desc + res_desc
    assert sum_res_rev.description == "(F2) + Hasil Pertama"

    sum_with_float = res_desc + 0.5
    assert sum_with_float.description == "Hasil Pertama + 0.5"