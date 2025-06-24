from ehrql import case, when
from ehrql.tables.tpp import patients

# Define reference date (typically study start date or current date)
index_date = "2024-01-01"  # Replace with your actual reference date

# Calculate age at index date
age = patients.age_on(index_date)

# Create age bands
age_band = case(
    when(age < 18).then("Child"),
    when(age < 65).then("Adult"), 
    when(age >= 65).then("Senior"),
    default="Unknown"
)

# Define the dataset
dataset = {
    "patient_id": patients.patient_id,
    "age": age,
    "age_band": age_band,
}
