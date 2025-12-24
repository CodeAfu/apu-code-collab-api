from sqlmodel import Session, create_engine, select
from src.entities.university_course import UniversityCourse
from src.config import settings

################################
## python -m src.seed.courses ##
################################

engine = create_engine(settings.DATABASE_URL)

apu_it_courses = [
    {"name": "BSc (Hons) in Software Engineering", "code": "SE"},
    {"name": "BSc (Hons) in Computer Science", "code": "CS"},
    {"name": "BSc (Hons) in Computer Science (Cyber Security)", "code": "CS-CYBER"},
    {"name": "BSc (Hons) in Computer Science (Data Analytics)", "code": "CS-DA"},
    {
        "name": "BSc (Hons) in Computer Science (Artificial Intelligence)",
        "code": "CS-AI",
    },
    {"name": "BSc (Hons) in Information Technology", "code": "IT"},
    {
        "name": "BSc (Hons) in Information Technology (Information Systems Security)",
        "code": "IT-ISS",
    },
    {"name": "BSc (Hons) in Information Technology (Cloud Computing)", "code": "IT-CC"},
    {
        "name": "BSc (Hons) in Information Technology (Network Computing)",
        "code": "IT-NC",
    },
    {
        "name": "BSc (Hons) in Information Technology (Internet of Things)",
        "code": "IT-IOT",
    },
    {"name": "BSc (Hons) in Information Technology (FinTech)", "code": "IT-FT"},
    {
        "name": "BSc (Hons) in Information Technology (Business Information Systems)",
        "code": "IT-BIS",
    },
]


def seed():
    with Session(engine) as session:
        print(f"Seeding {len(apu_it_courses)} courses...")

        for data in apu_it_courses:
            # Check for existence to prevent UniqueConstraint violations
            statement = select(UniversityCourse).where(
                UniversityCourse.code == data["code"]
            )
            existing = session.exec(statement).first()

            if not existing:
                course = UniversityCourse(name=data["name"], code=data["code"])
                session.add(course)
                print(f"  [+] Added: {data['name']}")
            else:
                print(f"  [~] Skipped (Exists): {data['name']}")

        session.commit()
        print("✅ Seeding complete.")


if __name__ == "__main__":
    seed()
