ALTER TABLE encounters ADD COLUMN age_years_cleaned FLOAT;
ALTER TABLE encounters ADD COLUMN gender_M INTEGER;  -- 1=Male, 0=Female
ALTER TABLE encounters ADD COLUMN los_days FLOAT;
ALTER TABLE encounters ADD COLUMN previous_admissions INTEGER;
ALTER TABLE encounters ADD COLUMN days_since_last_admit FLOAT;
ALTER TABLE encounters ADD COLUMN diagnosis_count INTEGER;
ALTER TABLE encounters ADD COLUMN charlson_score INTEGER;
ALTER TABLE encounters ADD COLUMN procedure_count INTEGER;
ALTER TABLE encounters ADD COLUMN icu_stay_count INTEGER;
ALTER TABLE encounters ADD COLUMN icu_los_days FLOAT;
ALTER TABLE encounters ADD COLUMN admit_type_EMERGENCY INTEGER;
ALTER TABLE encounters ADD COLUMN admit_type_URGENT INTEGER;
ALTER TABLE encounters ADD COLUMN insurance_Medicare INTEGER;
ALTER TABLE encounters ADD COLUMN insurance_Private INTEGER;
ALTER TABLE encounters ADD COLUMN hospital_expire_flag INTEGER;
