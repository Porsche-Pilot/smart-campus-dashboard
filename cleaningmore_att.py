import pandas as pd
import numpy as np

def generate_24_weeks():
    # Setup
    num_students = 5000
    courses = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    periods_config = {
        'P1': {'time': '08:00 - 09:00', 'prob': [0.35, 0.65]}, 
        'P2': {'time': '09:00 - 10:00', 'prob': [0.20, 0.80]}, 
        'P3': {'time': '10:00 - 11:00', 'prob': [0.05, 0.95]}, 
        'P4': {'time': '11:00 - 12:00', 'prob': [0.07, 0.93]}, 
        'P5': {'time': '12:00 - 13:00', 'prob': [0.15, 0.85]}  
    }
    period_keys = list(periods_config.keys())
    batch_map = {i: np.arange(i*500, (i+1)*500) for i in range(10)}
    
    all_frames = []
    print("Generating 4.2 million rows for 24 weeks...")

    for week in range(1, 25):
        for day in days:
            for c_idx, course in enumerate(courses):
                for b_idx in range(10):
                    p_idx = (c_idx + b_idx) % 5
                    period = period_keys[p_idx]
                    current_prob = periods_config[period]['prob']
                    
                    # Vectorized creation of the batch data
                    batch_students = batch_map[b_idx]
                    attendance = np.random.choice([0, 1], size=500, p=current_prob)
                    
                    temp_df = pd.DataFrame({
                        'Student_ID': batch_students,
                        'Course': course,
                        'Day': day,
                        'Period': period,
                        'Time_Slot': periods_config[period]['time'],
                        'Attendance': attendance,
                        'Week': week
                    })
                    all_frames.append(temp_df)

    # Consolidate and sort
    df = pd.concat(all_frames, ignore_index=True)
    df['Day'] = pd.Categorical(df['Day'], categories=days, ordered=True)
    df['Period'] = pd.Categorical(df['Period'], categories=period_keys, ordered=True)
    df['Course'] = pd.Categorical(df['Course'], categories=courses, ordered=True)
    
    df = df.sort_values(by=['Week', 'Day', 'Period', 'Course', 'Student_ID'])
    
    file_name = "attendance_24_weeks.csv"
    df.to_csv(file_name, index=False)
    print(f"File '{file_name}' is ready.")

generate_24_weeks()