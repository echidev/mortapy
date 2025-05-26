# mortapy/__init__.py

# Ekstrak fungsi-fungsi utama dari modul API agar bisa diakses
# langsung oleh pengguna. Contoh: import mortapy as mp; mp.calculate_whole_life_nsp()

from .api import (
    load_default_table,
    calculate_whole_life_nsp,
    calculate_whole_life_annuity_pv
)

# Anda juga bisa mendefinisikan informasi versi di sini
__version__ = "0.1.0"