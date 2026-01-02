import pkgutil
import importlib
import src.seed


def seed_all():
    print("Starting database seeding process...")

    for _, name, _ in pkgutil.iter_modules(src.seed.__path__):
        if name == "run_all":
            continue

        module_name = f"src.seed.{name}"

        try:
            # Import the module dynamically
            module = importlib.import_module(module_name)

            # Check for a 'seed' function and execute it
            if hasattr(module, "seed") and callable(module.seed):
                print(f"Running seeds for: {name}")
                module.seed()
            else:
                print(f"Skipped {name}: No seed() function found.")

        except Exception as e:
            print(f"Failed to seed {name}: {e}")

    print("All seed scripts executed.")


if __name__ == "__main__":
    seed_all()
