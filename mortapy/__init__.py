# mortapy/__init__.py

from .result import ActuarialResult
from .tables.base import MortalityTable
# Sebaiknya tidak mengekspos ActuarialCalculator langsung jika tidak diperlukan pengguna akhir
# from .core_calculator import ActuarialCalculator 

# Impor dari API berbasis tabel dengan alias yang jelas
from .api_tables import (
    load_default_table,
    nsp_whole_life as nsp_wl_table, # alias: nsp_wl_table
    pv_annuity_due_whole_life as pv_annuity_due_wl_table, # alias: pv_annuity_due_wl_table
    survival_probability as survival_prob_table, # alias: survival_prob_table
)

# Impor dari API berbasis asumsi dengan alias yang jelas
from .api_assumptions import (
    nsp_whole_life_from_assumption as nsp_wl_assumption,
    pv_annuity_due_whole_life_from_assumption as pv_annuity_due_wl_assumption, # alias
    survival_probability_from_assumption as survival_prob_assumption, # alias
)

__version__ = "0.4.0"