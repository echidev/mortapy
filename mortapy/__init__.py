# mortapy/__init__.py

from .result import ActuarialResult
from .tables.base import MortalityTable

# Impor dari API berbasis tabel dengan alias
from .api_tables import (
    load_default_table,
    nsp_whole_life_from_table as nsp_wl_table,
    pv_annuity_due_whole_life_from_table as pv_annuity_due_wl_table,
    survival_probability_from_table as survival_prob_table,
    death_probability_from_table as death_prob_table,
    deferred_death_probability_from_table as deferred_death_prob_table,
    force_of_mortality_from_table as fom_table,
    pdf_death_from_table as pdf_death_table,
)

# Impor dari API berbasis asumsi dengan alias
from .api_assumptions import (
    nsp_whole_life_from_assumption as nsp_wl_assumption,
    pv_annuity_due_whole_life_from_assumption as pv_annuity_due_wl_assumption,
    survival_probability_from_assumption as survival_prob_assumption,
    death_probability_from_assumption as death_prob_assumption,
    deferred_death_probability_from_assumption as deferred_death_prob_assumption,
    force_of_mortality_at_age_t as fom_assumption,
    pdf_death_at_age_t as pdf_death_assumption,
)

__version__ = "0.6.0" # Naikkan versi karena penambahan fitur signifikan