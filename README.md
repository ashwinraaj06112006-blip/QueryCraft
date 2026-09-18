# QueryCraft - Phase 1 Prototype

QueryCraft is a rule-based, controlled-English to SQL compiler prototype for the Compiler Design Laboratory. It is **not** an AI, NLP, machine-learning, or API-based system.

## What it demonstrates

`Source query -> Lexer -> Tokens -> Parser -> AST/IR -> Semantic analyzer -> SQL generator`

The predefined schema is:

```text
students(student_id: INTEGER, name: TEXT, department: TEXT, cgpa: REAL, age: INTEGER)
```

Supported examples:

```text
Show all students
Show student names
Show students whose CGPA is greater than 8
Show students with CGPA less than 7
Show students from CSE department
Show students where age greater than 18
Count students
Show students ordered by CGPA
Show top 5 students by CGPA
Show students where CGPA greater than 8 and age greater than 19
```

## Run locally

1. Install Python 3.10 or newer. No third-party packages are required.
2. Open a terminal in this `QueryCraft` folder.
3. Run a query:

```powershell
python -m src.main "Show students whose CGPA is greater than 8"
```

4. Run the test suite:

```powershell
python -m unittest discover -s tests -v
```

## Review 1 demonstration flow

Run three short examples:

```powershell
python -m src.main "Show students whose CGPA is greater than 8"
python -m src.main "Show top 5 students by CGPA"
python -m src.main "Show students where salary greater than 10"
```

For each valid query, point out the displayed tokens, AST/IR, semantic-validation result, and generated SQL. The last command demonstrates a semantic error because `salary` is not in the symbol table.

## Project structure

```text
src/        compiler stages and command-line entry point
tests/      automated Phase 1 test cases
README.md   setup and review instructions
```
