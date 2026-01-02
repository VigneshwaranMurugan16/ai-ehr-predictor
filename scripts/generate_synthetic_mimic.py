# scripts/generate_synthetic_mimic.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(42)

def generate_synthetic_data(n_patients=100):
    """Generate realistic MIMIC-III style synthetic data"""
    
    # Generate patients
    patients = []
    for i in range(1, n_patients + 1):
        gender = np.random.choice(['M', 'F'], p=[0.54, 0.46])
        dob_year = np.random.randint(1930, 2000)
        patients.append({
            'patient_id': i,
            'first_name': f'Patient{i}',
            'last_name': f'Lastname{i}',
            'gender': gender,
            'dob': f'{dob_year}-01-01'
        })
    
    # Generate encounters
    encounters = []
    encounter_id = 1
    
    for patient in patients:
        n_encounters = np.random.choice([1, 2, 3], p=[0.70, 0.20, 0.10])
        
        for encounter_num in range(n_encounters):
            admit_date = datetime(2025, 1, 1) + timedelta(days=np.random.randint(0, 365))
            age = admit_date.year - int(patient['dob'].split('-')[0])
            
            los_days = max(1, int(np.random.lognormal(1.7, 0.8)))
            discharge_date = admit_date + timedelta(days=los_days)
            
            previous_admissions = encounter_num
            days_since_last_admit = -1 if encounter_num == 0 else np.random.randint(30, 180)
            
            diagnosis_count = max(3, int(np.random.poisson(13)))
            
            if age < 40:
                charlson_score = np.random.choice([0, 1, 2], p=[0.6, 0.3, 0.1])
            elif age < 60:
                charlson_score = np.random.choice([0, 1, 2, 3, 4], p=[0.2, 0.3, 0.25, 0.15, 0.1])
            else:
                charlson_score = np.random.choice([1, 2, 3, 4, 5, 6], p=[0.15, 0.25, 0.25, 0.2, 0.1, 0.05])
            
            procedure_count = max(0, int(np.random.poisson(3.9)))
            icu_stay_count = np.random.choice([1, 2, 3], p=[0.85, 0.12, 0.03])
            icu_los_days = min(los_days, max(1, int(np.random.exponential(4.7))))
            
            admit_type = np.random.choice(['EMERGENCY', 'ELECTIVE', 'URGENT'], p=[0.92, 0.06, 0.02])
            
            if age >= 65:
                insurance = np.random.choice(['Medicare', 'Private', 'Medicaid'], p=[0.85, 0.10, 0.05])
            else:
                insurance = np.random.choice(['Private', 'Medicare', 'Medicaid'], p=[0.60, 0.25, 0.15])
            
            hospital_expire_flag = 1 if np.random.random() < 0.31 else 0
            
            encounters.append({
                'encounter_id': encounter_id,
                'patient_id': patient['patient_id'],
                'admit_date': admit_date.strftime('%Y-%m-%d'),
                'discharge_date': discharge_date.strftime('%Y-%m-%d'),
                'diagnosis': f'ICD9_{np.random.randint(100, 999)}',
                'age_years_cleaned': float(age),
                'gender_M': 1 if patient['gender'] == 'M' else 0,
                'los_days': float(los_days),
                'previous_admissions': previous_admissions,
                'days_since_last_admit': float(days_since_last_admit),
                'diagnosis_count': diagnosis_count,
                'charlson_score': charlson_score,
                'procedure_count': procedure_count,
                'icu_stay_count': icu_stay_count,
                'icu_los_days': float(icu_los_days),
                'admit_type_EMERGENCY': 1 if admit_type == 'EMERGENCY' else 0,
                'admit_type_URGENT': 1 if admit_type == 'URGENT' else 0,
                'insurance_Medicare': 1 if insurance == 'Medicare' else 0,
                'insurance_Private': 1 if insurance == 'Private' else 0,
                'hospital_expire_flag': hospital_expire_flag
            })
            
            encounter_id += 1
    
    return pd.DataFrame(patients), pd.DataFrame(encounters)

if __name__ == "__main__":
    patients_df, encounters_df = generate_synthetic_data(100)
    patients_df.to_csv('data/patients.csv', index=False)
    encounters_df.to_csv('data/encounters.csv', index=False)
    
    print(f"✅ Generated {len(patients_df)} patients")
    print(f"✅ Generated {len(encounters_df)} encounters")
    print(f"\n📊 Sample features:")
    print(encounters_df[['age_years_cleaned', 'los_days', 'charlson_score']].describe())
