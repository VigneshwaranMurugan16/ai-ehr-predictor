# AI-EHR-Predictor 🏥

## Hospital 30-Day Readmission Prediction using Machine Learning

A comprehensive machine learning pipeline for predicting 30-day hospital readmissions using MIMIC-III Electronic Health Records (EHR) data. This project implements advanced feature engineering, XGBoost modeling, and SHAP-based explainability for clinical decision support.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Dataset](#dataset)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Usage](#usage)
- [Model Performance](#model-performance)
- [Methodology](#methodology)
- [Results](#results)
- [Future Enhancements](#future-enhancements)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

Hospital readmissions within 30 days of discharge are a critical healthcare quality indicator and cost driver. This project develops a predictive model to identify patients at high risk of readmission, enabling proactive intervention strategies.

**Key Objectives:**
- Predict 30-day readmission risk using structured EHR data
- Provide interpretable predictions using SHAP explainability
- Handle class imbalance in clinical datasets
- Deploy production-ready ML pipeline

---

## ✨ Features

- **Comprehensive Data Pipeline**: Automated data extraction, cleaning, and transformation from MIMIC-III
- **Advanced Feature Engineering**: 15+ engineered clinical features including:
  - Demographic features (age, gender)
  - Clinical indicators (ICU stay duration, number of diagnoses)
  - Laboratory values (creatinine, glucose, heart rate, blood pressure)
  - Comorbidity flags (diabetes, hypertension, heart failure)
  
- **Machine Learning Models**:
  - XGBoost classifier with optimized hyperparameters
  - Class imbalance handling via `scale_pos_weight`
  - Stratified cross-validation
  
- **Model Explainability**:
  - SHAP (SHapley Additive exPlanations) analysis
  - Feature importance visualization
  - Individual prediction explanations

- **Comprehensive Evaluation**:
  - AUROC, Precision, Recall, F1-Score
  - Confusion matrix analysis
  - ROC and Precision-Recall curves
  - 5-fold stratified cross-validation

---

## 📊 Dataset

**Source**: [MIMIC-III Clinical Database](https://physionet.org/content/mimiciii/1.4/)

**Data Tables Used**:
- `ADMISSIONS`: Patient admission records
- `PATIENTS`: Demographic information
- `ICUSTAYS`: ICU stay duration
- `DIAGNOSES_ICD`: Diagnosis codes
- `LABEVENTS`: Laboratory measurements
- `CHARTEVENTS`: Vital signs and clinical observations

**Cohort Inclusion Criteria**:
- Adult patients (age ≥ 18)
- ICU admissions
- Complete discharge information
- Available follow-up data

---

## 🛠️ Installation

### Prerequisites

```bash
- Python 3.8+
- PostgreSQL (for MIMIC-III database)
- pip or conda
```

Setup
1. Clone the repository
```bash
git clone https://github.com/VigneshwaranMurugan16/ai-ehr-predictor.git
cd ai-ehr-predictor
```
2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4.MIMIC-III Database Setup
Obtain access from PhysioNet
Install PostgreSQL
Load MIMIC-III database following official instructions

5.Configure database connection
```python
# Update DATA_PATH in notebooks
DATA_PATH = "/path/to/mimic-iii-clinical-database-demo-1.4/"
```

## 📁 Project Structure
```text
ai-ehr-predictor/
│
├── notebooks/
│   ├── 1_data_extraction.ipynb          # MIMIC-III data extraction
│   ├── 2_feature_engineering.ipynb      # Feature creation & transformation
│   └── 3_model_training.ipynb           # Model training & evaluation
│
├── data/
│   ├── raw/                             # Raw MIMIC-III extracts
│   ├── processed/                       # Cleaned datasets
│   └── mimic_features_engineered.csv    # Final feature set
│
├── models/
│   ├── xgboost_model.pkl               # Trained XGBoost model
│   └── feature_names.json              # Feature metadata
│
├── src/
│   ├── data_preprocessing.py           # Data processing utilities
│   ├── feature_engineering.py          # Feature creation functions
│   ├── model_training.py               # Training pipeline
│   └── evaluation.py                   # Evaluation metrics
│
├── results/
│   ├── plots/                          # Visualization outputs
│   └── metrics/                        # Performance metrics
│
├── requirements.txt                     # Python dependencies
├── README.md                           # Project documentation
└── LICENSE                             # MIT License
```

## 🚀 Usage
1. Data Extraction
```bash
jupyter notebook notebooks/1_data_extraction.ipynb
```
Extracts relevant tables from MIMIC-III database and creates initial cohort.


2. Feature Engineering

```bash
jupyter notebook notebooks/2_feature_engineering.ipynb
```
Transforms raw data into ML-ready features with proper handling of:

-Missing values
-Outliers
-Data types
-Temporal features

3. Model Training
```bash
jupyter notebook notebooks/3_model_training.ipynb
```
Trains XGBoost model with:

-Stratified train-test split (80/20)
-Hyperparameter optimization
-Cross-validation
-SHAP explainability

Python Script Execution
```python
from src.model_training import train_model
from src.evaluation import evaluate_model

# Train model
model, metrics = train_model(
    data_path='data/processed/mimic_features_engineered.csv',
    test_size=0.2,
    random_state=42
)

# Evaluate
results = evaluate_model(model, X_test, y_test)
print(f"Test AUROC: {results['auroc']:.4f}")

```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📚 References

1.Johnson, A.E.W., et al. (2016). MIMIC-III, a freely accessible critical care database. Scientific Data.
2.Chen, T., & Guestrin, C. (2016). XGBoost: A Scalable Tree Boosting System. KDD.
3.Lundberg, S.M., & Lee, S.I. (2017). A Unified Approach to Interpreting Model Predictions. NIPS.

## 👥 Authors
Vigneshwaran Murugan

GitHub: @VigneshwaranMurugan16

## 🙏 Acknowledgments
-MIT Laboratory for Computational Physiology for MIMIC-III database
-PhysioNet for data access
-XGBoost and SHAP library developers
-Healthcare ML research community

## ⚠️ Disclaimer
This project is for research and educational purposes only. Not intended for clinical use without proper validation, regulatory approval, and clinical oversight.



