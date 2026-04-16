import pandas as pd
import numpy as np

def generate_semester_electricity(baseline_file, output_file, total_weeks=24):
    # Load baseline matrix
    df_base = pd.read_csv(baseline_file)
    
    # Melt wide matrix to long format for processing
    df_long = df_base.melt(id_vars=['Place'], var_name='Day_Hour', value_name='Base_Usage')
    df_long[['Day', 'Hour']] = df_long['Day_Hour'].str.split('_', expand=True)
    df_long['Hour'] = df_long['Hour'].astype(int)
    
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    day_map = {day: i for i, day in enumerate(days)}
    all_data = []

    for week in range(1, total_weeks + 1):
        # Determine the week's multiplier
        if week == 12:
            week_type, multiplier = 'Holiday', 0.30
        elif week in [21, 22]:
            week_type, multiplier = 'Exams', 1.25
        elif week in [23, 24]:
            week_type, multiplier = 'Post-Exam', 0.15
        else:
            week_type, multiplier = 'Normal', 1.0
            
        for _, row in df_long.iterrows():
            building = row['Place']
            base_val = row['Base_Usage']
            hour = row['Hour']
            
            current_mult = multiplier
            
            # Special Exam logic: Extra night usage in Hostels/Study areas
            if week_type == 'Exams' and ('Hostel' in building or 'SAC' in building):
                if hour >= 22 or hour <= 4:
                    current_mult *= 1.4
            
            # Add random variation (noise)
            noise = np.random.uniform(0.92, 1.08)
            usage = round(base_val * current_mult * noise, 2)
            
            all_data.append({
                'Week': week,
                'Building': building,
                'Day': row['Day'],
                'Day_of_Week': day_map[row['Day']],
                'Hour': hour,
                'Electricity_Usage_kWh': usage,
                'Period_Type': week_type
            })
                
    final_df = pd.DataFrame(all_data)
    final_df.to_csv(output_file, index=False)
    print(f"File saved: {output_file}")

# Run generation
generate_semester_electricity('electricity_matrix_week.csv', 'semester_electricity_usage_24_weeks.csv')