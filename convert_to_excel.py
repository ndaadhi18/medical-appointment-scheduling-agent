import pandas as pd

# Read the CSV file
df = pd.read_csv('data/doctor_schedule.csv')

# Write to Excel
df.to_excel('data/doctor_schedule.xlsx', index=False, sheet_name='Schedule')

print("Doctor schedule converted to Excel format successfully!")
