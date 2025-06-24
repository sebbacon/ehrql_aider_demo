from ehrql import case, create_dataset, when, codelist_from_csv, months, days
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

# --- DM020 ---
# The percentage of patients with diabetes, on the register, without moderate or
# severe frailty in whom the last IFCC-HbA1c is 58 mmol/mol or less in the
# preceding 12 months.

# Define codelists for DM020 from 3.2.3 Clinical code clusters
mild_frailty_codelist = codelist_from_csv(
    "codelists/mild_frailty_qof.csv", column="code"
)
moderate_frailty_codelist = codelist_from_csv(
    "codelists/moderate_frailty_qof.csv", column="code"
)
severe_frailty_codelist = codelist_from_csv(
    "codelists/severe_frailty_qof.csv", column="code"
)
ifcchbam_codelist = codelist_from_csv("codelists/ifcchbam_cod.csv", column="code")
serfruc_codelist = codelist_from_csv("codelists/serfruc_cod.csv", column="code")
dmmax_codelist = codelist_from_csv("codelists/dmmax_cod.csv", column="code")
dmpcapu_codelist = codelist_from_csv("codelists/dmpcapu_cod.csv", column="code")
bldtestdec_codelist = codelist_from_csv("codelists/bldtestdec_cod.csv", column="code")
dmpcadec_codelist = codelist_from_csv("codelists/dmpcadec_cod.csv", column="code")
dminvite_codelist = codelist_from_csv("codelists/dminvite_cod.csv", column="code")

# Define time periods from 3.1 Qualifying dates
# PPED (Payment Period End Date) is the achievement date
twelve_months_before_pped = achievement_date - months(12)
nine_months_before_pped = achievement_date - months(9)
qssd = "2021-04-01"  # Quality Service Start Date from the doc

# Define clinical data extraction criteria from 3.2.4
latest_hba1c = (
    clinical_events.where(clinical_events.snomedct_code.is_in(ifcchbam_codelist))
    .where(clinical_events.date.is_on_or_before(achievement_date))
    .sort_by(clinical_events.date)
    .last_for_patient()
)

# Denominator rules for DM020
# Rule 1: Reject if moderate or severe frailty
all_frailty_codelist = (
    mild_frailty_codelist + moderate_frailty_codelist + severe_frailty_codelist
)
latest_frailty_event = (
    clinical_events.where(clinical_events.snomedct_code.is_in(all_frailty_codelist))
    .where(clinical_events.date.is_on_or_before(achievement_date))
    .sort_by(clinical_events.date)
    .last_for_patient()
)
is_moderate_or_severe_frail = latest_frailty_event.snomedct_code.is_in(
    moderate_frailty_codelist + severe_frailty_codelist
)
population_rule_1 = dataset.dm_reg & ~is_moderate_or_severe_frail

# Rule 2: Select if HbA1c target met
hba1c_in_target = (latest_hba1c.numeric_value <= 58) & (
    latest_hba1c.date > twelve_months_before_pped
)
selected_by_rule_2 = population_rule_1 & hba1c_in_target
population_for_rule_3 = population_rule_1 & ~hba1c_in_target

# Rule 3: Reject if no recent HbA1c but recent serum fructosamine
no_recent_hba1c = latest_hba1c.date.is_null() | (
    latest_hba1c.date <= twelve_months_before_pped
)
latest_serfruc_date = (
    clinical_events.where(clinical_events.snomedct_code.is_in(serfruc_codelist))
    .where(clinical_events.date.is_on_or_before(achievement_date))
    .sort_by(clinical_events.date)
    .last_for_patient()
    .date
)
has_recent_serfruc = latest_serfruc_date.is_not_null() & (
    latest_serfruc_date > twelve_months_before_pped
)
rejected_by_rule_3 = no_recent_hba1c & has_recent_serfruc
population_after_rule_3 = population_for_rule_3 & ~rejected_by_rule_3

# Rule 4: Reject if on max tolerated treatment
dmmax_dat = (
    clinical_events.where(clinical_events.snomedct_code.is_in(dmmax_codelist))
    .where(clinical_events.date.is_on_or_before(achievement_date))
    .sort_by(clinical_events.date)
    .last_for_patient()
    .date
)
rejected_by_rule_4 = dmmax_dat.is_not_null() & (dmmax_dat > twelve_months_before_pped)
population_after_rule_4 = population_after_rule_3 & ~rejected_by_rule_4

# Rule 5: Reject if care unsuitable
dmpcapu_dat = (
    clinical_events.where(clinical_events.snomedct_code.is_in(dmpcapu_codelist))
    .where(clinical_events.date.is_on_or_before(achievement_date))
    .sort_by(clinical_events.date)
    .last_for_patient()
    .date
)
rejected_by_rule_5 = dmpcapu_dat.is_not_null() & (
    dmpcapu_dat > twelve_months_before_pped
)
population_after_rule_5 = population_after_rule_4 & ~rejected_by_rule_5

# Rule 6: Reject if blood test declined
bldtestdec_dat = (
    clinical_events.where(clinical_events.snomedct_code.is_in(bldtestdec_codelist))
    .where(clinical_events.date.is_on_or_before(achievement_date))
    .sort_by(clinical_events.date)
    .last_for_patient()
    .date
)
rejected_by_rule_6 = bldtestdec_dat.is_not_null() & (
    bldtestdec_dat > twelve_months_before_pped
)
population_after_rule_6 = population_after_rule_5 & ~rejected_by_rule_6

# Rule 7: Reject if care declined
dmpcadec_dat = (
    clinical_events.where(clinical_events.snomedct_code.is_in(dmpcadec_codelist))
    .where(clinical_events.date.is_on_or_before(achievement_date))
    .sort_by(clinical_events.date)
    .last_for_patient()
    .date
)
rejected_by_rule_7 = dmpcadec_dat.is_not_null() & (
    dmpcadec_dat > twelve_months_before_pped
)
population_after_rule_7 = population_after_rule_6 & ~rejected_by_rule_7

# Rule 8: Reject based on invitations
dminvite1_dat = (
    clinical_events.where(clinical_events.snomedct_code.is_in(dminvite_codelist))
    .where(clinical_events.date.is_on_or_between(qssd, achievement_date))
    .sort_by(clinical_events.date)
    .first_for_patient()
    .date
)
dminvite2_dat = (
    clinical_events.where(clinical_events.snomedct_code.is_in(dminvite_codelist))
    .where(
        clinical_events.date.is_on_or_between(dminvite1_dat + days(7), achievement_date)
    )
    .sort_by(clinical_events.date)
    .first_for_patient()
    .date
)
rejected_by_rule_8_part_a = (
    (latest_hba1c.date > twelve_months_before_pped)
    & (latest_hba1c.numeric_value > 58)
    & (dminvite1_dat > latest_hba1c.date)
    & dminvite2_dat.is_not_null()
)
rejected_by_rule_8_part_b = dminvite2_dat.is_not_null() & no_recent_hba1c
rejected_by_rule_8 = rejected_by_rule_8_part_a | rejected_by_rule_8_part_b
population_after_rule_8 = population_after_rule_7 & ~rejected_by_rule_8

# Rule 9: Reject if newly diagnosed
dm_dat = (
    clinical_events.where(clinical_events.snomedct_code.is_in(dm_codelist))
    .where(clinical_events.date.is_on_or_before(achievement_date))
    .sort_by(clinical_events.date)
    .first_for_patient()
    .date
)
rejected_by_rule_9 = dm_dat.is_not_null() & (dm_dat > nine_months_before_pped)
population_after_rule_9 = population_after_rule_8 & ~rejected_by_rule_9

# Rule 10: Reject if newly registered, otherwise select
reg_dat = practice_registrations.for_patient_on(achievement_date).start_date
rejected_by_rule_10 = reg_dat > nine_months_before_pped
selected_by_rule_10 = population_after_rule_9 & ~rejected_by_rule_10

# Final denominator and numerator for DM020
dataset.dm020_denominator = selected_by_rule_2 | selected_by_rule_10
dataset.dm020_numerator = selected_by_rule_2

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
