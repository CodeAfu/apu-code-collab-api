from sqlmodel import Session, create_engine, select
from src.entities.programming_language import ProgrammingLanguage
from src.config import settings

##################################
## python -m src.seed.languages ##
##################################

engine = create_engine(settings.DATABASE_URL)

languages_data = [
    {"name": "Python"},
    {"name": "JavaScript"},
    {"name": "TypeScript"},
    {"name": "Java"},
    {"name": "C"},
    {"name": "C++"},
    {"name": "C#"},
    {"name": "Go"},
    {"name": "Rust"},
    {"name": "PHP"},
    {"name": "Ruby"},
    {"name": "Swift"},
    {"name": "Kotlin"},
    {"name": "Dart"},
    {"name": "SQL"},
    {"name": "HTML"},  # Often listed as a language skill
    {"name": "CSS"},  # Often listed as a language skill
    {"name": "Shell"},
    {"name": "Bash"},
    {"name": "PowerShell"},
    {"name": "Haskell"},
    {"name": "Elixir"},
    {"name": "Erlang"},
    {"name": "Clojure"},
    {"name": "F#"},
    {"name": "OCaml"},
    {"name": "Scala"},
    {"name": "Lisp"},
    {"name": "Scheme"},
    {"name": "Racket"},
    {"name": "Elm"},
    {"name": "Reason"},
    {"name": "PureScript"},
    {"name": "Zig"},
    {"name": "Nim"},
    {"name": "Crystal"},
    {"name": "V"},
    {"name": "D"},
    {"name": "Julia"},
    {"name": "Lua"},
    {"name": "Perl"},
    {"name": "R"},
    {"name": "Matlab"},
    {"name": "Groovy"},
    {"name": "Tcl"},
    {"name": "Delphi"},
    {"name": "Object Pascal"},
    {"name": "Ada"},
    {"name": "Fortran"},
    {"name": "Cobol"},
    {"name": "Assembly"},
    {"name": "WebAssembly"},
    {"name": "Objective-C"},
    {"name": "Solidity"},  # Blockchain
    {"name": "Vyper"},  # Blockchain
    {"name": "Apex"},  # Salesforce
    {"name": "ABAP"},  # SAP
    {"name": "SAS"},  # Analytics
    {"name": "Visual Basic"},
    {"name": "VBA"},
    {"name": "ActionScript"},
    {"name": "CoffeeScript"},
    {"name": "Pascal"},
    {"name": "Basic"},
    {"name": "Prolog"},
    {"name": "Smalltalk"},
    {"name": "Scratch"},
    {"name": "Logo"},
    {"name": "Alice"},
    {"name": "Awk"},
    {"name": "Sed"},
    {"name": "Verilog"},
    {"name": "VHDL"},
    {"name": "LabVIEW"},
    {"name": "OpenEdge ABL"},
    {"name": "PL/SQL"},
    {"name": "Transact-SQL"},
    {"name": "ColdFusion"},
    {"name": "AutoLISP"},
    {"name": "Eiffel"},
    {"name": "Forth"},
    {"name": "FoxPro"},
    {"name": "Hack"},
    {"name": "Haxe"},
    {"name": "Idris"},
    {"name": "J#"},
    {"name": "JScript"},
    {"name": "Mercury"},
    {"name": "Mojo"},
    {"name": "Oxygene"},
    {"name": "Oz"},
    {"name": "PostScript"},
    {"name": "Q#"},
    {"name": "RPG"},
    {"name": "Simula"},
    {"name": "Standard ML"},
    {"name": "Vala"},
    {"name": "Wolfram Language"},
    {"name": "XSLT"},
]


def seed():
    with Session(engine) as session:
        print(f"Seeding {len(languages_data)} programming languages...")

        for data in languages_data:
            # Check for existence
            statement = select(ProgrammingLanguage).where(
                ProgrammingLanguage.name == data["name"]
            )
            existing = session.exec(statement).first()

            if not existing:
                language = ProgrammingLanguage(name=data["name"])
                session.add(language)
                print(f"  [+] Added: {data['name']}")
            else:
                print(f"  [~] Skipped (Exists): {data['name']}")

        session.commit()
        print("✅ Language seeding complete.")


if __name__ == "__main__":
    seed()
