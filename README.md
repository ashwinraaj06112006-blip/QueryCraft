# QueryCraft - Phase 3 Schema-Adaptive Compiler

QueryCraft is a rule-based, controlled-English to SQL compiler for the Compiler Design Laboratory. It is **not** an LLM, external AI API, machine-learning, or cloud-based system.

## What it demonstrates

`Source query -> Lexer -> Tokens -> Parser -> AST/IR -> Semantic analyzer -> SQL generator -> SQLite result`

The original compiler demonstration uses this predefined schema:

```text
students(student_id: INTEGER, name: TEXT, department: TEXT, cgpa: REAL, age: INTEGER)
```

Supported fixed-schema examples:

```text
Show all students
Show student names
Show students whose CGPA is greater than 8
Show students from CSE department
Count students
Show top 5 students by CGPA
```

## Run locally

1. Install Python 3.10 or newer. No third-party packages are required.
2. Open PowerShell in this `QueryCraft` folder.
3. Run the local workbench:

```powershell
python -m src.webapp
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in a browser.

## Phase 3: upload-aware workbench

The browser workbench supports CSV, XLSX and JSON files up to 100 MB. It imports the file locally into SQLite in batches, derives column names and basic types, previews the schema, then accepts controlled-English queries such as:

```text
Show all records
Count records where experience greater than 2
Show name, department where salary greater than 50000
Show top 5 records by salary
Count records group by department
Show average salary group by department
```

The Phase 3 novelty is an **offline retrieval-augmented schema layer**. Before SQL generation, it scores uploaded column names against the query and shows the relevant fields used for compilation. This is transparent and deterministic; it does not use a generative model.

For a quick local demonstration, upload `sample_data/employees.csv`.

## Tests

```powershell
python -m unittest discover -s tests -v
```

There are 20 automated Phase 1–3 tests covering the original compiler, safe SQL execution, schema inference, retrieval, dynamic compilation, valid queries and an unknown-column failure.

## Review 3 demonstration

1. Start the workbench and upload `sample_data/employees.csv`.
2. Show the inferred schema: name, department, salary and experience.
3. Run `Show name, department where salary greater than 50000`.
4. Explain the retrieved fields, AST/IR, generated SQL and result table.
5. Run `Count records group by department` to demonstrate aggregate and grouping support.
6. Run `Show all records where bonus greater than 5` to demonstrate schema validation.

## Project structure

```text
src/          compiler stages, upload importer, retrieval and web server
web/          browser workbench assets
tests/        automated Phase 1–3 test cases
sample_data/  safe review demonstration dataset
docs/         phase reports
README.md     setup and review instructions
```
