# examples/hitung_dasar.py

# Impor library mortapy Anda
import mortapy as mp

# Tentukan parameter
usia_tertanggung = 35
jenis_kelamin = 'pria'
suku_bunga_teknis = 0.05 # 5%

# Hitung Premi Tunggal Bersih (NSP) untuk asuransi jiwa seumur hidup
nsp = mp.calculate_whole_life_nsp(
    age=usia_tertanggung,
    interest_rate=suku_bunga_teknis,
    gender=jenis_kelamin
)

# Hitung Nilai Sekarang (PV) dari anuitas jiwa seumur hidup awal tahun
pv_anuitas = mp.calculate_whole_life_annuity_pv(
    age=usia_tertanggung,
    interest_rate=suku_bunga_teknis,
    gender=jenis_kelamin
)


print("="*40)
print("Hasil Perhitungan Aktuaria Dasar")
print("="*40)
print(f"Parameter:")
print(f"  Usia         : {usia_tertanggung}")
print(f"  Jenis Kelamin: {jenis_kelamin}")
print(f"  Suku Bunga   : {suku_bunga_teknis * 100:.2f}%")
print("-"*40)
print(f"Premi Tunggal Bersih (Whole Life): {nsp:.6f}")
print(f"PV Anuitas Awal Tahun (Whole Life): {pv_anuitas:.6f}")
print("="*40)