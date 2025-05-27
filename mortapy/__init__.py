# mortapy/__init__.py

from .result import ActuarialResult
from .tables.base import MortalityTable
from .api import (
    load_default_table,
    calculate_whole_life_nsp,
    calculate_whole_life_annuity_pv,
    calculate_survival_prob, # Asumsikan ini masih ada dan mengembalikan float
)
__version__ = "0.3.0" # Mungkin naikkan versi lagi karena perubahan signifikan