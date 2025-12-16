import csv
from datetime import datetime, date

from sqlalchemy.orm import Session

from app.db import Base, engine, SessionLocal
from app.models import Patient, Encounter, Task
from app.risk import calculate_readmission_risk


def parse_date(value: str) -> date | None:
    value = (value or "").strip()
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def load_patients(session: Session, path: str) -> None:
    print(f"Loading patients from {path}")
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        print(f"Read {len(rows)} patient rows")
        for row in rows:
            patient = Patient(
                id=int(row["id"]),
                first_name=row["first_name"],
                last_name=row["last_name"],
                birth_date=parse_date(row["birth_date"]),
                gender=row["gender"] or None,
            )
            session.merge(patient)

    # Make sure inserts/updates are visible to subsequent queries
    session.flush()


def load_encounters_and_risk(session: Session, path: str) -> None:
    print(f"Loading encounters from {path}")
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        print(f"Read {len(rows)} encounter rows")
        for row in rows:
            print("Row:", row)

            patient_id = int(row["patient_id"])

            patient = session.get(Patient, patient_id)
            if not patient:
                print(f"No patient {patient_id}, skipping")
                continue

            enc = Encounter(
                id=int(row["id"]),
                patient_id=patient_id,
                encounter_type=row["encounter_type"],
                start_date=parse_date(row["start_date"]),
                end_date=parse_date(row["end_date"]),
            )

            score, level = calculate_readmission_risk(patient, enc)
            enc.risk_score = score
            enc.risk_level = level
            session.merge(enc)

            # create nurse_review task for high risk
            if level == "high":
                task = Task(
                    patient_id=patient_id,
                    encounter_id=int(row["id"]),
                    task_type="nurse_review",
                    status="open",
                )
                session.add(task)
 

def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        load_patients(db, "data/patients.csv")
        load_encounters_and_risk(db, "data/encounters.csv")
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
