from dataclasses import dataclass


@dataclass(frozen=True)
class PatientProfile:
    id: str
    name: str
    age: int
    bed: str
    simulation_pattern: str
    default_condition: str


PATIENT_PROFILES = [
    PatientProfile("P1", "Olivia Reed", 29, "ICU-01", "normal", "Normal"),
    PatientProfile("P2", "Mason Lee", 54, "ICU-02", "hypoxia", "Hypoxia"),
    PatientProfile("P3", "Anika Das", 41, "ICU-03", "fever", "Fever"),
    PatientProfile("P4", "Robert Fox", 62, "ICU-04", "cardiac", "Cardiac Stress"),
    PatientProfile("P5", "Sarah Patel", 47, "ICU-05", "sepsis", "Sepsis Risk"),
    PatientProfile("P6", "John Max", 38, "ICU-06", "recovery", "Recovery"),
]

PATIENT_BY_ID = {profile.id: profile for profile in PATIENT_PROFILES}
