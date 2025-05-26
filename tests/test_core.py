import pytest
from mortapy.tables.base import MortalityTable
from mortapy.core import ActuarialCalculator
import os

TEST_TABLE_PATH = os.path.join(os.path.dirname(__file__), '..', 'mortapy', 'tables', 'tabel_mortalita_penduduk_indonesia_2023.csv')

@pytest.fixture
def calc():
    """Fixture untuk membuat objek kalkulator yang bisa dipakai ulang di semua tes."""
    table = MortalityTable(TEST_TABLE_PATH)
    # Gunakan suku bunga 5% untuk konsistensi tes
    return ActuarialCalculator(table, interest_rate=0.05)

def test_prob_hidup_logis(calc):
    """Memastikan probabilitas hidup n tahun lebih kecil dari probabilitas hidup 1 tahun."""
    p1 = calc.p(age=30, n=1, gender='pria') # _1p_30
    p10 = calc.p(age=30, n=10, gender='pria') # _10p_30
    
    assert p10 < p1
    assert calc.p(age=30, n=0) == 1.0 # Probabilitas hidup 0 tahun adalah 1

def test_premi_dan_anuitas_logis(calc):
    """
    Memastikan nilai premi dan anuitas logis secara hubungan.
    Contoh: Anuitas untuk orang yang lebih muda harus lebih mahal.
    Premi untuk orang yang lebih tua harus lebih mahal.
    """
    # Premi untuk usia 30 vs 50
    ax_30 = calc.Ax(age=30, gender='wanita')
    ax_50 = calc.Ax(age=50, gender='wanita')
    
    # Anuitas untuk usia 30 vs 50
    adue_30 = calc.a_due_x(age=30, gender='wanita')
    adue_50 = calc.a_due_x(age=50, gender='wanita')
    
    # Semakin tua, semakin mahal premi asuransinya
    assert ax_50 > ax_30
    # Semakin muda, semakin mahal anuitasnya (karena ekspektasi pembayaran lebih lama)
    assert adue_30 > adue_50

def test_hubungan_premi_dan_anuitas(calc):
    """
    Menguji identitas aktuaria dasar: A_x = 1 - d * a_due_x
    di mana d = i / (1+i)
    """
    age = 40
    i = calc.interest_rate
    d = i / (1 + i)

    ax = calc.Ax(age, gender='pria')
    adue_x = calc.a_due_x(age, gender='pria')

    # Cek apakah identitasnya terpenuhi
    assert ax == pytest.approx(1 - d * adue_x)