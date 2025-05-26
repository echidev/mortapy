import mortapy as mp

def test_api_fungsi_berjalan_tanpa_error():
    """
    Tes integrasi sederhana untuk memastikan fungsi API publik bisa dipanggil
    dan mengembalikan nilai float tanpa error.
    """
    # Parameter dasar
    age = 35
    interest_rate = 0.05
    gender = 'wanita'
    
    # Panggil fungsi API
    nsp = mp.calculate_whole_life_nsp(age, interest_rate, gender)
    pv_annuity = mp.calculate_whole_life_annuity_pv(age, interest_rate, gender)
    
    # Pastikan hasilnya adalah angka (float)
    assert isinstance(nsp, float)
    assert isinstance(pv_annuity, float)
    
    # Pastikan hasilnya positif
    assert nsp > 0
    assert pv_annuity > 0