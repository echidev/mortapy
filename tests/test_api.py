import mortapy as mp
from mortapy.result import ActuarialResult # Impor kelas ActuarialResult

def test_api_fungsi_berjalan_tanpa_error():
    """
    Tes integrasi sederhana untuk memastikan fungsi API publik bisa dipanggil
    dan mengembalikan objek ActuarialResult.
    """
    # Parameter dasar
    age = 35
    interest_rate = 0.05
    gender = 'wanita'
    
    # Panggil fungsi API
    nsp_result = mp.calculate_whole_life_nsp(age, interest_rate, gender)
    pv_annuity_result = mp.calculate_whole_life_annuity_pv(age, interest_rate, gender)
    
    # Pastikan hasilnya adalah instance dari ActuarialResult
    assert isinstance(nsp_result, ActuarialResult)
    assert isinstance(pv_annuity_result, ActuarialResult)
    
    # Pastikan atribut .value adalah angka (float) dan positif
    assert isinstance(nsp_result.value, float)
    assert isinstance(pv_annuity_result.value, float)
    
    assert nsp_result.value > 0
    assert pv_annuity_result.value > 0