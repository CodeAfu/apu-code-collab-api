from sqlmodel import Session, create_engine, select
from src.entities.framework import Framework
from src.config import settings

###################################
## python -m src.seed.frameworks ##
###################################

engine = create_engine(settings.DATABASE_URL)

frameworks_data = [
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
    {"name": "FastAPI"},
    {"name": "Django"},
    {"name": "Flask"},
    {"name": "Spring Boot"},
    {"name": "ASP.NET Core"},
    {"name": "Laravel"},
    {"name": "Symfony"},
    {"name": "Flutter"},
    {"name": "React Native"},
    {"name": "Preact"},
    {"name": "SolidJS"},
    {"name": "Qwik"},
    {"name": "Alpine.js"},
    {"name": "Lit"},
    {"name": "Ember.js"},
    {"name": "Backbone.js"},
    {"name": "jQuery"},
    {"name": "Remix"},
    {"name": "Astro"},
    {"name": "Gatsby"},
    {"name": "Blazor"},
    {"name": "htmx"},
    {"name": "Bootstrap"},
    {"name": "Material UI (MUI)"},
    {"name": "Chakra UI"},
    {"name": "Shadcn UI"},
    {"name": "Ant Design"},
    {"name": "Mantine"},
    {"name": "Bulma"},
    {"name": "Foundation"},
    {"name": "Sass/SCSS"},
    {"name": "Styled Components"},
    {"name": "Emotion"},
    {"name": "Panda CSS"},
    {"name": "Vanilla Extract"},
    {"name": "Redux"},
    {"name": "Redux Toolkit"},
    {"name": "Zustand"},
    {"name": "Recoil"},
    {"name": "MobX"},
    {"name": "Pinia"},
    {"name": "TanStack Query (React Query)"},
    {"name": "SWR"},
    {"name": "Apollo Client"},
    {"name": "XState"},
    {"name": "Fastify"},
    {"name": "Koa"},
    {"name": "Hapi"},
    {"name": "Socket.io"},
    {"name": "Meteor"},
    {"name": "AdonisJS"},
    {"name": "LoopBack"},
    {"name": "tRPC"},
    {"name": "Tornado"},
    {"name": "Pyramid"},
    {"name": "Bottle"},
    {"name": "Falcon"},
    {"name": "Sanic"},
    {"name": "Litestar"},
    {"name": "Celery"},  # Task Queue
    {"name": "Gin"},
    {"name": "Echo"},
    {"name": "Fiber"},
    {"name": "Chi"},
    {"name": "Revel"},
    {"name": "Beego"},
    {"name": "Gorilla Mux"},
    {"name": "Spring Framework"},
    {"name": "Hibernate"},
    {"name": "Jakarta EE"},
    {"name": "Quarkus"},
    {"name": "Micronaut"},
    {"name": "Ktor"},
    {"name": "Vert.x"},
    {"name": "Blade"},
    {"name": "Ruby on Rails"},
    {"name": "Sinatra"},
    {"name": "Hanami"},
    {"name": "CodeIgniter"},
    {"name": "CakePHP"},
    {"name": "Yii"},
    {"name": "Slim"},
    {"name": "Laminas"},
    {"name": "WordPress"},  # Often listed as a skill framework
    {"name": ".NET MAUI"},
    {"name": "Entity Framework"},
    {"name": "Dapper"},
    {"name": "NancyFX"},
    {"name": "Actix Web"},
    {"name": "Rocket"},
    {"name": "Axum"},
    {"name": "Tokio"},
    {"name": "Tauri"},  # Desktop
    {"name": "Ionic"},
    {"name": "Expo"},
    {"name": "Capacitor"},
    {"name": "Xamarin"},
    {"name": "NativeScript"},
    {"name": "Electron"},
    {"name": "Qt"},
    {"name": "SwiftUI"},  # Apple
    {"name": "UIKit"},  # Apple
    {"name": "Jetpack Compose"},  # Android
    {"name": "Prisma"},
    {"name": "Mongoose"},
    {"name": "TypeORM"},
    {"name": "Sequelize"},
    {"name": "SQLAlchemy"},
    {"name": "SQLModel"},
    {"name": "Drizzle ORM"},
    {"name": "MikroORM"},
    {"name": "Redis"},  # Often listed in tech stacks
    {"name": "GraphQL"},
    {"name": "Pandas"},
    {"name": "NumPy"},
    {"name": "SciPy"},
    {"name": "Scikit-learn"},
    {"name": "TensorFlow"},
    {"name": "PyTorch"},
    {"name": "Keras"},
    {"name": "Matplotlib"},
    {"name": "Seaborn"},
    {"name": "OpenCV"},
    {"name": "Streamlit"},
    {"name": "Hugging Face Transformers"},
    {"name": "LangChain"},
    {"name": "Jest"},
    {"name": "Vitest"},
    {"name": "Cypress"},
    {"name": "Playwright"},
    {"name": "Selenium"},
    {"name": "Mocha"},
    {"name": "Chai"},
    {"name": "Pytest"},
    {"name": "JUnit"},
    {"name": "Storybook"},
    {"name": "Unity"},
    {"name": "Unreal Engine"},
    {"name": "Godot"},
    {"name": "Three.js"},
    {"name": "Phaser"},
    {"name": "Pygame"},
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
