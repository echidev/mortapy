# tests/test_result.py
import pytest
from mortapy.result import ActuarialResult
from typing import Union, Any, Callable

def test_actuarial_result_creation():
    """Tes pembuatan objek ActuarialResult dan representasinya."""
    res = ActuarialResult(value=0.123, formula_latex="A_x", description="NSP Test")
    assert res.value == 0.123
    assert res.formula_latex == "A_x"
    assert res.description == "NSP Test"
    assert "Symbol: 'A_x'" in repr(res)
    assert "Value: 0.12300000" in repr(res)
    assert "Description: 'NSP Test'" in repr(res)
    assert res._repr_latex_() == "$$ A_x = 0.12300000 $$"

def test_actuarial_result_addition():
    """Tes operasi penjumlahan pada ActuarialResult."""
    res1 = ActuarialResult(0.1, "A_x", "Premi A")
    res2 = ActuarialResult(0.2, "A_y", "Premi B")

    # Result + Result
    res_sum1 = res1 + res2
    assert isinstance(res_sum1, ActuarialResult)
    assert res_sum1.value == pytest.approx(0.3)
    assert res_sum1.formula_latex == "(A_x + A_y)"
    assert res_sum1.description == "Premi A + Premi B"

    # Result + float
    res_sum2 = res1 + 0.05
    assert isinstance(res_sum2, ActuarialResult)
    assert res_sum2.value == pytest.approx(0.15)
    assert res_sum2.formula_latex == "(A_x + 0.05)"
    assert res_sum2.description == "Premi A + 0.05"

    # float + Result
    res_sum3 = 0.07 + res1
    assert isinstance(res_sum3, ActuarialResult)
    assert res_sum3.value == pytest.approx(0.17)
    assert res_sum3.formula_latex == f"(0.07 + {res1.formula_latex})"
    expected_desc_radd = f"0.07 + {res1.description if res1.description else '('+res1.formula_latex+')'}"
    assert res_sum3.description == expected_desc_radd


def test_actuarial_result_subtraction():
    """Tes operasi pengurangan pada ActuarialResult."""
    res1 = ActuarialResult(0.3, "Term_A", "Premi Term A")
    res2 = ActuarialResult(0.1, "Term_B", "Premi Term B")

    # Result - Result
    res_diff1 = res1 - res2
    assert isinstance(res_diff1, ActuarialResult)
    assert res_diff1.value == pytest.approx(0.2)
    assert res_diff1.formula_latex == "(Term_A - Term_B)"
    assert res_diff1.description == "Premi Term A - Premi Term B"

    # Result - float
    res_diff2 = res1 - 0.05
    assert isinstance(res_diff2, ActuarialResult)
    assert res_diff2.value == pytest.approx(0.25)
    assert res_diff2.formula_latex == "(Term_A - 0.05)"
    assert res_diff2.description == "Premi Term A - 0.05"

    # float - Result
    res_diff3 = 0.5 - res1
    assert isinstance(res_diff3, ActuarialResult)
    assert res_diff3.value == pytest.approx(0.2)
    assert res_diff3.formula_latex == "(0.5 - Term_A)"
    expected_desc_rsub = f"0.5 - {res1.description if res1.description else '('+res1.formula_latex+')'}"
    assert res_diff3.description == expected_desc_rsub


def test_actuarial_result_repr_latex_no_description():
    """Tes _repr_latex_ jika deskripsi kosong."""
    res = ActuarialResult(value=0.555, formula_latex="P_x")
    assert res._repr_latex_() == "$$ P_x = 0.55500000 $$"
    assert res.description == ""

def test_combine_results_description_handling():
    """Tes bagaimana deskripsi digabungkan."""
    res_desc = ActuarialResult(1, "F1", "Hasil Pertama")
    res_no_desc = ActuarialResult(2, "F2")

    sum_res = res_desc + res_no_desc
    assert sum_res.description == "Hasil Pertama + (F2)"

    sum_res_rev = res_no_desc + res_desc
    assert sum_res_rev.description == "(F2) + Hasil Pertama"

    sum_with_float = res_desc + 0.5
    assert sum_with_float.description == "Hasil Pertama + 0.5"

    res_no_desc_self = ActuarialResult(3, "F3")
    sum_radd_no_desc_self = 0.7 + res_no_desc_self
    expected_desc_radd_no_self_desc = f"0.7 + ({res_no_desc_self.formula_latex})"
    assert sum_radd_no_desc_self.description == expected_desc_radd_no_self_desc