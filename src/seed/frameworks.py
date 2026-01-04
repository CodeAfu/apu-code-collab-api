from sqlmodel import Session, create_engine, select
from src.entities.framework import Framework
from src.config import settings

###################################
## python -m src.seed.frameworks ##
###################################

engine = create_engine(settings.DATABASE_URL)

# Common frameworks/libraries to seed
frameworks_data = [
    # JavaScript / TypeScript
    {"name": "React"},
    {"name": "Next.js"},
    {"name": "Vue.js"},
    {"name": "Nuxt.js"},
    {"name": "Angular"},
    {"name": "Svelte"},
    {"name": "SvelteKit"},
    {"name": "Express.js"},
    {"name": "NestJS"},
    {"name": "Tailwind CSS"},
    # Python
    {"name": "FastAPI"},
    {"name": "Django"},
    {"name": "Flask"},
    # Java
    {"name": "Spring Boot"},
    # C#
    {"name": "ASP.NET Core"},
    # PHP
    {"name": "Laravel"},
    {"name": "Symfony"},
    # Mobile
    {"name": "Flutter"},
    {"name": "React Native"},
]


def seed():
    with Session(engine) as session:
        print(f"Seeding {len(frameworks_data)} frameworks...")

        for data in frameworks_data:
            # Check for existence
            statement = select(Framework).where(Framework.name == data["name"])
            existing = session.exec(statement).first()

            if not existing:
                framework = Framework(name=data["name"])
                session.add(framework)
                print(f"  [+] Added: {data['name']}")
            else:
                print(f"  [~] Skipped (Exists): {data['name']}")

        session.commit()
        print("✅ Framework seeding complete.")


if __name__ == "__main__":
    seed()
