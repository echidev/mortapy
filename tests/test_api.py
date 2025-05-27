import mortapy as mp
from mortapy.result import ActuarialResult # Impor kelas ActuarialResult
import pytest

def test_api_dengan_tabel():
    nsp_result = mp.calculate_whole_life_nsp(age=35, interest_rate=0.05, gender='pria')
    assert isinstance(nsp_result, mp.ActuarialResult)
    assert nsp_result.value > 0

def test_api_dengan_base_qx():
    # Contoh qx = 0.01 untuk semua usia (penyederhanaan)
    nsp_result = mp.calculate_whole_life_nsp(age=35, interest_rate=0.05, base_qx=0.01)
    assert isinstance(nsp_result, mp.ActuarialResult)
    assert nsp_result.value > 0
    # Anda bisa menambahkan assert nilai spesifik jika Anda menghitungnya manual

    # Untuk fungsi probabilitas (setelah Anda menamakannya kembali)
    prob_result = mp.calculate_survival_prob_integer(age=30, period_years=1, interest_rate=0.05, base_qx=0.02)
    assert isinstance(prob_result, mp.ActuarialResult)
    assert prob_result.value == pytest.approx(0.98) # p_x = 1 - q_x