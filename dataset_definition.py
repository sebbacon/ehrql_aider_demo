from ehrql import case, create_dataset, when
from ehrql.tables.core import patients

index_date = "2024-01-01"

dataset = create_dataset()

age = patients.age_on(index_date)

dataset.age_band = case(
    when(age < 18).then("child"),
    when(age < 65).then("adult"),
    when(age >= 65).then("senior"),
    otherwise="missing",
)

dataset.define_population(patients.exists_for_patient())
