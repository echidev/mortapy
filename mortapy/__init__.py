# mortapy/__init__.py

# Impor kelas-kelas utama yang perlu diakses pengguna
from .result import ActuarialResult
from .tables.base import MortalityTable

# Impor fungsi-fungsi API utama
from .api import (
    load_default_table,
    calculate_whole_life_nsp,
    calculate_whole_life_annuity_pv,
    calculate_survival_prob_integer,
)

__version__ = "0.3.0" # atau versi yang sesuai