# mortapy/__init__.py

from .result import ActuarialResult
from .tables.base import MortalityTable
from .core_calculator import ActuarialCalculator 

# Impor dari API berbasis tabel
from .api_tables import (
    load_default_table,
    nsp_whole_life_from_table, 
    pv_annuity_due_whole_life_from_table, 
    survival_probability_from_table, 
    death_probability_from_table,
    deferred_death_probability_from_table,
    force_of_mortality_from_table,
    pdf_death_from_table,
    expected_curtate_future_lifetime_from_table,      
    second_moment_curtate_future_lifetime_from_table, 
    variance_curtate_future_lifetime_from_table,
    expected_complete_future_lifetime_from_table,     
    second_moment_complete_future_lifetime_from_table,
    variance_complete_future_lifetime_from_table      
)

# Impor dari API berbasis asumsi
from .api_assumptions import (
    nsp_whole_life_from_assumption, 
    pv_annuity_due_whole_life_from_assumption, 
    survival_probability_from_assumption, 
    death_probability_from_assumption,
    deferred_death_probability_from_assumption,
    force_of_mortality_at_age_t, 
    pdf_death_at_age_t,
    expected_curtate_future_lifetime_from_assumption,      
    second_moment_curtate_future_lifetime_from_assumption, 
    variance_curtate_future_lifetime_from_assumption,
    expected_complete_future_lifetime_from_assumption,     
    second_moment_complete_future_lifetime_from_assumption,
    variance_complete_future_lifetime_from_assumption      
)

# Membuat alias yang lebih pendek dan jelas untuk pengguna
# Berbasis Tabel
nsp_wl_table = nsp_whole_life_from_table
pv_annuity_due_wl_table = pv_annuity_due_whole_life_from_table
survival_prob_table = survival_probability_from_table
death_prob_table = death_probability_from_table
deferred_death_prob_table = deferred_death_probability_from_table
fom_table = force_of_mortality_from_table
pdf_death_table = pdf_death_from_table
ex_curtate_table = expected_curtate_future_lifetime_from_table          
e_sq_curtate_table = second_moment_curtate_future_lifetime_from_table   
var_k_table = variance_curtate_future_lifetime_from_table
ex_complete_table = expected_complete_future_lifetime_from_table       
e_sq_complete_table = second_moment_complete_future_lifetime_from_table 
var_t_table = variance_complete_future_lifetime_from_table             

# Berbasis Asumsi
nsp_wl_assumption = nsp_whole_life_from_assumption
pv_annuity_due_wl_assumption = pv_annuity_due_whole_life_from_assumption
survival_prob_assumption = survival_probability_from_assumption
death_prob_assumption = death_probability_from_assumption
deferred_death_prob_assumption = deferred_death_probability_from_assumption
fom_assumption = force_of_mortality_at_age_t 
pdf_death_assumption = pdf_death_at_age_t   
ex_curtate_assumption = expected_curtate_future_lifetime_from_assumption      
e_sq_curtate_assumption = second_moment_curtate_future_lifetime_from_assumption 
var_k_assumption = variance_curtate_future_lifetime_from_assumption
ex_complete_assumption = expected_complete_future_lifetime_from_assumption       
e_sq_complete_assumption = second_moment_complete_future_lifetime_from_assumption 
var_t_assumption = variance_complete_future_lifetime_from_assumption             

__version__ = "0.9.0"