import pandas as pd
import numpy as np

def generate_semester_wifi(baseline_file, output_file, total_weeks=24):
    # Load baseline WiFi data
    df_baseline = pd.read_csv(baseline_file)
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    day_map = {day: i for i, day in enumerate(days)}
    
    # Map baseline to a quick-access dictionary
    baseline_patterns = {}
    for _, row in df_baseline.iterrows():
        day = row['Day']
        baseline_patterns[day] = {int(h): row[h] for h in df_baseline.columns if h.isdigit()}

    all_data = []
    
    for week in range(1, total_weeks + 1):
        # Determine the "state" of the campus
        if week == 12:
            week_type, multiplier = 'Holiday', 0.25
        elif week in [21, 22]:
            week_type, multiplier = 'Exams', 1.30
        elif week in [23, 24]:
            week_type, multiplier = 'Post-Exam', 0.10
        else:
            week_type, multiplier = 'Normal', 1.0
            
        for day in days:
            for hour in range(24):
                base_val = baseline_patterns[day][hour]
                
                # Apply multipliers based on hour and week type
                current_mult = multiplier
                if week_type == 'Exams' and hour <= 4:
                    current_mult *= 1.5 # Extra boost for night study
                
                # Add 10% random noise
                noise = np.random.uniform(0.9, 1.1)
                usage = round(base_val * current_mult * noise, 2)
                
                all_data.append({
                    'Week': week,
                    'Day': day,
                    'Day_of_Week': day_map[day],
                    'Hour': hour,
                    'Wifi_Usage_MB': usage,
                    'Period_Type': week_type
                })
                
    final_df = pd.DataFrame(all_data)
    final_df.to_csv(output_file, index=False)
    return final_df

# Run generation
df_wifi = generate_semester_wifi('wifi_week_matrix.csv', 'semester_wifi_usage_24_weeks.csv')