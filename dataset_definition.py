from ehrql import case, create_dataset, when, codelist_from_csv
from ehrql.tables.core import patients, clinical_events
from ehrql.tables.tpp import practice_registrations

index_date = "2024-01-01"

dataset = create_dataset()

# QOF business rules for diabetes mellitus (DM)
# Based on DIABETES.md (Version 46.0, 01/04/2021)

# 3.1 Qualifying dates
# Using index_date as the achievement date (ACHV_DAT)
achievement_date = index_date

# 3.2.3 Clinical code clusters
# DM_COD: Diabetes mellitus codes
dm_codelist = codelist_from_csv("codelists/dm_cod.csv", column="code")
# DMRES_COD: Diabetes resolved codes
dm_resolved_codelist = codelist_from_csv("codelists/dm_resolved_cod.csv", column="code")

# 3.2.4 Clinical data extraction criteria
# DMLAT_DAT: Date of the most recent diabetes diagnosis up to and including the
# achievement date.
dmlat_dat = (
    clinical_events.where(clinical_events.snomedct_code.is_in(dm_codelist))
    .where(clinical_events.date.is_on_or_before(achievement_date))
    .sort_by(clinical_events.date)
    .last_for_patient()
    .date
)

# DMRES_DAT: Date of the most recent diabetes diagnosis resolved code recorded
# after the most recent diabetes diagnosis and up to and including the
# achievement date.
dmres_dat = (
    clinical_events.where(clinical_events.snomedct_code.is_in(dm_resolved_codelist))
    .where(clinical_events.date.is_on_or_before(achievement_date))
    .where(clinical_events.date.is_after(dmlat_dat))
    .sort_by(clinical_events.date)
    .last_for_patient()
    .date
)

# 3.2.2.1 Case registers (DM_REG)
# Rule: If [DMLAT_DAT] != Null AND If [DMRES_DAT] = Null
# This is implemented by checking dmlat_dat exists, and dmres_dat (which is
# defined as being after dmlat_dat) does not.
has_unresolved_diabetes = dmlat_dat.is_not_null() & dmres_dat.is_null()

# PAT_AGE: The age of the patient in full years at the achievement date.
age = patients.age_on(achievement_date)

# Rule: If [PAT_AGE] < 17 years -> Reject, else Select.
is_over_16 = age >= 17

# DM_REG: Diabetes register. This is a boolean variable that is True for
# patients on the register.
dataset.dm_reg = has_unresolved_diabetes & is_over_16

# Re-add age band from original file for context, using the new age definition
dataset.age_band = case(
    when(age < 18).then("child"),
    when(age < 65).then("adult"),
    when(age >= 65).then("senior"),
    otherwise="missing",
)

# Define population based on GMS registration status
# 3.2.1 GMS registration status
# The rule specifies patients must be registered on the achievement date.
is_registered = practice_registrations.for_patient_on(
    achievement_date
).exists_for_patient()
dataset.define_population(is_registered)
