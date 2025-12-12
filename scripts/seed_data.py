from datetime import date
from app.db import SessionLocal
from app.models import Patient, Encounter, Task
from app.db import Base, engine
from app.risk import calculate_readmission_risk

def main():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if db.query(Patient).count() == 0:
            p1 = Patient(first_name="John", last_name="Doe", birth_date=date(1980, 5, 20), gender="M")
            p2 = Patient(first_name="Mary", last_name="Smith", birth_date=date(1950, 9, 10), gender="F")
            db.add_all([p1, p2])
            db.commit()

            e1 = Encounter(
                patient_id=p1.id,
                encounter_type="IPD",
                start_date=date(2025, 12, 1),
                end_date=date(2025, 12, 10),
            )
            e2 = Encounter(
                patient_id=p2.id,
                encounter_type="IPD",
                start_date=date(2025, 12, 5),
                end_date=date(2025, 12, 7),
            )
            db.add_all([e1, e2])
            db.commit()

            # compute risk using the function
            for enc in [e1, e2]:
                patient = p1 if enc.patient_id == p1.id else p2
                score, level = calculate_readmission_risk(patient, enc)
                enc.risk_score = score
                enc.risk_level = level
            db.commit()

            # create tasks only for high risk
            for enc in [e1, e2]:
                if enc.risk_level == "high":
                    t = Task(
                        patient_id=enc.patient_id,
                        encounter_id=enc.id,
                        task_type="nurse_review",
                        status="open",
                    )
                    db.add(t)
            db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    main()
