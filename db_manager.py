import pandas as pd
from sqlalchemy import create_engine

# Connect to the integrated database
engine = create_engine('sqlite:///smart_campus_intelligence.db')

def generate_bi_tables():
    print("Initializing Pro-Mode Data Extraction for PowerBI/Tableau...\n")

    # ---------------------------------------------------------
    # METRIC 1: MESS CROWD MANAGEMENT (Peak Hours)
    # Extracts the hour from Scan_Time (e.g., "13" from "13:45")
    # ---------------------------------------------------------
    print("1. Processing Mess Crowd Optimization Data...")
    mess_query = """
    SELECT 
        Meal, 
        substr(Scan_Time, 1, 2) as Hour_of_Day, 
        COUNT(*) as Total_Footfall
    FROM mess
    WHERE Status = 1 AND Scan_Time IS NOT NULL
    GROUP BY Meal, Hour_of_Day
    ORDER BY Meal, Hour_of_Day
    """
    df_mess = pd.read_sql(mess_query, engine)
    df_mess.to_csv('BI_Mess_Peak_Hours.csv', index=False)


    # ---------------------------------------------------------
    # METRIC 2: ENERGY LEAK DETECTION (Electricity vs WiFi/Time)
    # Compares building electricity to overall campus WiFi activity
    # High Electricity + Low Campus Activity = "Ghost Load" Anomaly
    # ---------------------------------------------------------
    print("2. Processing Energy Efficiency & Anomaly Data...")
    energy_query = """
    SELECT 
        e.Building, 
        e.Period_Type,
        e.Hour, 
        AVG(e.Electricity_Usage_kWh) as Avg_Electricity_kWh,
        AVG(w.Wifi_Usage_MB) as Campus_Wifi_Load
    FROM electricity e
    JOIN wifi w ON e.Week = w.Week AND e.Day = w.Day AND e.Hour = w.Hour
    GROUP BY e.Building, e.Period_Type, e.Hour
    """
    df_energy = pd.read_sql(energy_query, engine)
    
    # Create the "Wastage Index" -> higher number means more energy wasted
    # We add 1 to Wifi to prevent division by zero
    df_energy['Wastage_Index'] = df_energy['Avg_Electricity_kWh'] / (df_energy['Campus_Wifi_Load'] + 1)
    df_energy.to_csv('BI_Energy_Anomalies.csv', index=False)


    # ---------------------------------------------------------
    # METRIC 3: SPACE UTILIZATION (Attendance by Course & Period)
    # Identifies classes that can be moved to smaller rooms
    # ---------------------------------------------------------
    print("3. Processing Academic Space Utilization Data...")
    attendance_query = """
    SELECT 
        Course, 
        Period,
        AVG(Attendance) * 100 as Avg_Attendance_Percentage
    FROM attendance
    GROUP BY Course, Period
    """
    df_attendance = pd.read_sql(attendance_query, engine)
    df_attendance.to_csv('BI_Space_Utilization.csv', index=False)


    # ---------------------------------------------------------
    # METRIC 4: THE "FRIDAY FLIGHT" METRIC (Cross-Domain)
    # Do students skip Friday classes AND Friday Mess? 
    # ---------------------------------------------------------
    print("4. Processing Student Behavior Trends...")
    friday_query = """
    SELECT 
        a.Week,
        SUM(CASE WHEN a.Attendance = 0 THEN 1 ELSE 0 END) as Total_Friday_Absences
    FROM attendance a
    WHERE a.Day = 'Friday'
    GROUP BY a.Week
    """
    df_friday = pd.read_sql(friday_query, engine)
    df_friday.to_csv('BI_Friday_Behavior.csv', index=False)

    print("\n✅ All BI Tables generated successfully! Ready for PowerBI/Tableau.")

if __name__ == "__main__":
    generate_bi_tables()