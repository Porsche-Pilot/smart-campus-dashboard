import pandas as pd
from sqlalchemy import create_engine

# Connect to the integrated database
engine = create_engine('sqlite:///smart_campus_intelligence.db')

def generate_advanced_bi_tables():
    print("Initializing Advanced BI Extraction...\n")

    # ---------------------------------------------------------
    # ADVANCED METRIC 1: THE EXAM STRESS & OVERLOAD INDEX
    # Compares resources during Exam weeks vs. Normal weeks
    # ---------------------------------------------------------
    print("1. Processing Exam Period Overload Data...")
    exam_stress_query = """
    SELECT 
        e.Period_Type,
        ROUND(AVG(e.Electricity_Usage_kWh), 2) as Avg_Hourly_Electricity,
        ROUND(AVG(w.Wifi_Usage_MB), 2) as Avg_Hourly_Wifi
    FROM electricity e
    JOIN wifi w ON e.Week = w.Week AND e.Day = w.Day AND e.Hour = w.Hour
    GROUP BY e.Period_Type
    """
    df_exam_stress = pd.read_sql(exam_stress_query, engine)
    df_exam_stress.to_csv('BI_Adv_Exam_Stress_Index.csv', index=False)


    # ---------------------------------------------------------
    # ADVANCED METRIC 2: AT-RISK STUDENT TRACKER
    # Identifies students who have dropped below the 75% threshold
    # ---------------------------------------------------------
    # ---------------------------------------------------------
    # ADVANCED METRIC 2: FULL STUDENT LEDGER (Holistic View)
    # Extracts ALL courses for ALL students to allow deep-dive searches
    # ---------------------------------------------------------
    print("2. Processing Full Student Academic Ledger...")
    at_risk_query = """
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
    df_at_risk = pd.read_sql(at_risk_query, engine)
    df_at_risk.to_csv('BI_Full_Student_Ledger.csv', index=False)

    # ---------------------------------------------------------
    # ADVANCED METRIC 3: FULL-WEEK BEHAVIORAL "FLIGHT" RISK
    # Calculates the absentee rate for every day of the week 
    # to find the highest "skip" days.
    # ---------------------------------------------------------
    print("3. Processing Full-Week Flight Risk...")
    flight_risk_query = """
    SELECT 
        Day,
        COUNT(*) as Total_Seats,
        SUM(CASE WHEN Attendance = 0 THEN 1 ELSE 0 END) as Total_Absences,
        ROUND((SUM(CASE WHEN Attendance = 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 2) as Absentee_Rate_Percentage
    FROM attendance
    GROUP BY Day
    """
    df_flight_risk = pd.read_sql(flight_risk_query, engine)
    
    # Ensure Days are sorted chronologically, not alphabetically
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    df_flight_risk['Day'] = pd.Categorical(df_flight_risk['Day'], categories=days_order, ordered=True)
    df_flight_risk = df_flight_risk.sort_values('Day')
    
    df_flight_risk.to_csv('BI_Adv_Flight_Risk.csv', index=False)

    print("\n✅ Advanced BI Tables generated successfully! Ready for the Dashboard.")

if __name__ == "__main__":
    generate_advanced_bi_tables()