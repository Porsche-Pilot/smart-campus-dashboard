import pandas as pd
from sqlalchemy import create_engine

# Connect to database
engine = create_engine('sqlite:///smart_campus_intelligence.db')

print("Extracting FULL student ledger (ignoring the 75% rule)...")

# Notice: There is NO 'HAVING' or 'WHERE' clause here. We grab everything.
query = """
SELECT 
    Student_ID,
    Course,
    COUNT(*) as Total_Classes,
    SUM(Attendance) as Classes_Attended,
    ROUND((SUM(Attendance) * 100.0 / COUNT(*)), 2) as Attendance_Percentage
FROM attendance
GROUP BY Student_ID, Course
ORDER BY Student_ID ASC
"""

df = pd.read_sql(query, engine)

# Save to the exact file the Streamlit app is looking for
df.to_csv('BI_Full_Student_Ledger.csv', index=False)

print("\n✅ Success! Created BI_Full_Student_Ledger.csv")
print(f"📊 Total course records found: {len(df)}")
print(f"📈 Maximum attendance found: {df['Attendance_Percentage'].max()}%")
print("If the maximum attendance above is greater than 75%, the data is officially fixed!")