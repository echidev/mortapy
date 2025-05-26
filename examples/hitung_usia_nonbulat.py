# examples/hitung_usia_nonbulat.py

import mortapy as mp

# Perbarui __init__.py di folder mortapy agar mengimpor fungsi baru
# from .api import calculate_survival_prob
# Tambahkan baris di atas ke mortapy/__init__.py Anda

# Parameter
usia = 50
periode_setengah_tahun = 0.5
periode_satu_setengah_tahun = 1.5
suku_bunga = 0.05 # Suku bunga tidak memengaruhi probabilitas

# Hitung probabilitas hidup selama setengah tahun
p_udd = mp.calculate_survival_prob(usia, periode_setengah_tahun, suku_bunga, assumption='udd')
p_cfm = mp.calculate_survival_prob(usia, periode_setengah_tahun, suku_bunga, assumption='cfm')

print("="*60)
print(f"Probabilitas hidup {periode_setengah_tahun} tahun untuk seseorang berusia {usia}:")
print(f"  - Dengan Asumsi UDD: {p_udd:.8f}")
print(f"  - Dengan Asumsi CFM: {p_cfm:.8f}")
print("="*60)

# Hitung probabilitas hidup selama 1.5 tahun
p_total_udd = mp.calculate_survival_prob(usia, periode_satu_setengah_tahun, suku_bunga, assumption='udd')
p_total_cfm = mp.calculate_survival_prob(usia, periode_satu_setengah_tahun, suku_bunga, assumption='cfm')

print(f"Probabilitas hidup {periode_satu_setengah_tahun} tahun untuk seseorang berusia {usia}:")
print(f"  - Dengan Asumsi UDD: {p_total_udd:.8f}")
print(f"  - Dengan Asumsi CFM: {p_total_cfm:.8f}")
print("="*60)