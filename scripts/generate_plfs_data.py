import os
import csv
import json
import random

# State codes and names
STATES = ["09", "27", "19", "33", "07", "08", "10", "24", "29", "32"]
DISTRICTS = ["01", "02", "03", "04", "05"]
SECTORS = ["1", "2"] # 1: Rural, 2: Urban

# Principal Activity Status Codes in PLFS
# 11: Self-employed in own account, 31: Regular salaried employee, 41: Casual wage worker,
# 81: Unemployed / Student, 91: Domestic duties, 92: Domestic + collection, 97: Others
ACTIVITY_CODES = [11, 31, 41, 81, 91, 92, 97]

# Education codes: 01=Illiterate, 05=Primary, 08=Secondary, 10=Higher Secondary, 12=Graduate, 13=Post Graduate
EDU_CODES = [1, 5, 8, 10, 12, 13]

def create_plfs_datasets():
    os.makedirs("data", exist_ok=True)
    
    # Read layout
    with open("data/plfs_layout.json", "r") as f:
        layout = json.load(f)
        
    records = []
    fixed_width_lines = []
    
    # Generate 500 records across 2 rounds: 350 for 2023-24 baseline, 150 for 2024-25 held-out demo stream
    random.seed(42)
    
    rounds = [("2023-24", 350), ("2024-25", 150)]
    
    rec_counter = 1000
    for survey_round, count in rounds:
        for i in range(count):
            rec_counter += 1
            state = random.choice(STATES)
            district = random.choice(DISTRICTS)
            sector = random.choice(SECTORS)
            fsu = f"FSU{state}{district}{sector}{random.randint(10, 99)}"
            hh_no = random.randint(1, 15)
            person_no = random.randint(1, 6)
            rel_to_head = 1 if person_no == 1 else random.choice([2, 3, 4, 9])
            sex = random.choice([1, 2])
            age = random.randint(15, 65)
            
            # Education level correlated with age
            gen_edu = random.choice(EDU_CODES)
            if age < 18:
                gen_edu = min(gen_edu, 10)
                
            # Activity code logic
            if age < 22 and random.random() > 0.4:
                activity = 81 # Student / Unemployed
            else:
                activity = random.choice([11, 31, 41, 91]) if sex == 2 else random.choice([11, 31, 41])
                
            # Earnings & Wages realistic distribution based on sector and activity
            if activity == 31: # Regular salaried
                monthly_exp = round(random.uniform(12000, 45000), 2)
                earnings = round(random.uniform(15000, 65000), 2)
                daily_wages = round(earnings / 26.0, 2)
            elif activity in (11, 41): # Self-employed / Casual
                monthly_exp = round(random.uniform(6000, 22000), 2)
                earnings = round(random.uniform(5000, 25000), 2)
                daily_wages = round(earnings / 24.0, 2)
            else: # Inactive / Student / Domestic
                monthly_exp = round(random.uniform(5000, 18000), 2)
                earnings = 0.0
                daily_wages = 0.0

            # Inject realistic anomalies for data quality detection validation!
            # Anomaly 1: Age 12 with Graduate degree and Regular Salaried high earnings
            if i % 45 == 0 and survey_round == "2024-25":
                age = 12
                gen_edu = 12
                activity = 31
                earnings = 85000.0
                daily_wages = 3200.0
            
            # Anomaly 2: High digit preference (00000) or extreme outlier earnings
            if i % 60 == 0 and survey_round == "2024-25":
                earnings = 999999.0
                monthly_exp = 99999.0
                
            multiplier = round(random.uniform(150.0, 850.0), 2)

            rec = {
                "Survey_Round": survey_round,
                "FSU": fsu,
                "State": state,
                "District": district,
                "Sector": sector,
                "Sub_Sample": random.choice([1, 2]),
                "Hh_No": hh_no,
                "Person_No": person_no,
                "Rel_To_Head": rel_to_head,
                "Sex": sex,
                "Age": age,
                "General_Edu": gen_edu,
                "Usual_Principal_Activity_Status": activity,
                "Subsidiary_Activity_Status": 0,
                "Weekly_Activity_Status": activity,
                "Earnings_Last_Month": earnings,
                "Daily_Wages": daily_wages,
                "Monthly_Exp": monthly_exp,
                "Multiplier": multiplier
            }
            records.append(rec)
            
            # Build fixed width line format matching plfs_layout byte positions
            # Format:
            # Round (8) FSU (8) State (2) Dist (3) Sector (1) Sub (1) Hh (3) Per (2) Rel (1) Sex (1) Age (3) Edu (2) Act (2) SubAct (2) WkAct (2) Earn (7) Wage (6) Exp (7) Mult (10)
            fw_line = f"{survey_round:<8}{fsu:<8}{state:<2}{district:<3}{sector:<1}{rec['Sub_Sample']:1d}{hh_no:03d}{person_no:02d}{rel_to_head:1d}{sex:1d}{age:03d}{gen_edu:02d}{activity:02d}{0:02d}{activity:02d}{int(earnings):07d}{int(daily_wages):06d}{int(monthly_exp):07d}{multiplier:10.2f}"
            fixed_width_lines.append(fw_line)

    # Save CSV format
    fieldnames = list(records[0].keys())
    with open("data/plfs_microdata.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    # Save Fixed-width text format (CHHV1.txt)
    with open("data/CHHV1.txt", "w") as f:
        f.write("\n".join(fixed_width_lines))
        
    print(f"Generated data/plfs_microdata.csv ({len(records)} rows) and data/CHHV1.txt ({len(fixed_width_lines)} lines).")

if __name__ == "__main__":
    create_plfs_datasets()
