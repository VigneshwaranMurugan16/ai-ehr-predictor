from datetime import date
from app.models import Patient, Encounter

def calculate_readmission_risk(patient: Patient, encounter: Encounter) -> tuple[float, str]:
    """
    Very simple rule-based risk calculator.
    Later this will be replaced by a real ML model.
    """

    score = 0.0

    # Age-based risk
    if patient.birth_date:
        today = date.today()
        age = today.year - patient.birth_date.year - (
            (today.month, today.day) < (patient.birth_date.month, patient.birth_date.day)
        )
        if age >= 75:
            score += 0.4
        elif age >= 65:
            score += 0.3
        elif age >= 50:
            score += 0.2
        else:
            score += 0.1

    # Length-of-stay based risk (if end_date known)
    if encounter.start_date and encounter.end_date:
        los = (encounter.end_date - encounter.start_date).days
        if los >= 10:
            score += 0.3
        elif los >= 5:
            score += 0.2
        elif los >= 2:
            score += 0.1

    # Encounter type
    if encounter.encounter_type == "IPD":
        score += 0.2
    elif encounter.encounter_type == "ER":
        score += 0.1

    # Clamp score between 0 and 1
    score = max(0.0, min(1.0, score))

    # Map to level
    if score >= 0.7:
        level = "high"
    elif score >= 0.4:
        level = "medium"
    else:
        level = "low"

    return score, level


from datetime import date
from app.models import Patient, Encounter

# existing calculate_readmission_risk...


def calculate_los_risk(encounter: Encounter) -> tuple[int | None, str]:
    """
    Returns (length_of_stay_days, los_level)
    los_level: "short", "medium", "long"
    """
    if not encounter.start_date or not encounter.end_date:
        return None, "unknown"

    los = (encounter.end_date - encounter.start_date).days
    if los <= 1:
        level = "short"
    elif los <= 7:
        level = "medium"
    else:
        level = "long"
    return los, level
