import tempfile
import unittest
import zipfile
from pathlib import Path

from src.data_ingestion import import_dataset
from src.dynamic_compiler import compile_uploaded_query, execute_uploaded_sql
from src.schema_retrieval import retrieve_columns


class Phase3Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "employees.csv"
        self.source.write_text("Name,Department,Salary,Experience\nAsha,CSE,72000,4\nBala,ECE,45000,2\nChitra,CSE,90000,6\n", encoding="utf-8")
        self.schema = import_dataset(self.source, self.root / "data.sqlite3")

    def tearDown(self): self.temp.cleanup()

    def test_infers_schema_and_rows(self):
        self.assertEqual(self.schema["row_count"], 3)
        self.assertEqual([column["name"] for column in self.schema["columns"]], ["name", "department", "salary", "experience"])
        self.assertEqual(self.schema["columns"][2]["type"], "INTEGER")

    def test_retrieves_relevant_column(self):
        found = retrieve_columns("show employees with salary greater than 50000", self.schema["columns"])
        self.assertEqual(found[0]["name"], "salary")

    def test_compiles_and_executes_dynamic_query(self):
        compiled = compile_uploaded_query("Show name, department where salary greater than 50000", self.schema)
        self.assertIn('"salary" > 50000', compiled["sql"])
        columns, rows = execute_uploaded_sql(compiled["sql"], self.root / "data.sqlite3")
        self.assertEqual(columns, ["name", "department"])
        self.assertEqual([row["name"] for row in rows], ["Asha", "Chitra"])

    def test_count_and_top_query(self):
        compiled = compile_uploaded_query("Count records where experience greater than 2", self.schema)
        _, rows = execute_uploaded_sql(compiled["sql"], self.root / "data.sqlite3")
        self.assertEqual(rows[0]["count"], 2)
        top = compile_uploaded_query("Show top 2 records by salary", self.schema)
        _, rows = execute_uploaded_sql(top["sql"], self.root / "data.sqlite3")
        self.assertEqual(rows[0]["name"], "Chitra")

    def test_grouped_count_and_average(self):
        grouped = compile_uploaded_query("Count records group by department", self.schema)
        self.assertIn('GROUP BY "department"', grouped["sql"])
        _, rows = execute_uploaded_sql(grouped["sql"], self.root / "data.sqlite3")
        self.assertEqual({row["department"]: row["count"] for row in rows}, {"CSE": 2, "ECE": 1})
        average = compile_uploaded_query("Show average salary group by department", self.schema)
        self.assertIn('AVG("salary")', average["sql"])
        _, rows = execute_uploaded_sql(average["sql"], self.root / "data.sqlite3")
        self.assertEqual({row["department"]: row["avg_salary"] for row in rows}, {"CSE": 81000.0, "ECE": 45000.0})

    def test_rejects_unknown_column(self):
        with self.assertRaises(ValueError):
            compile_uploaded_query("Show all records where bonus greater than 5", self.schema)

    def test_imports_basic_xlsx(self):
        source = self.root / "scores.xlsx"
        worksheet = '''<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c t="inlineStr"><is><t>Name</t></is></c><c t="inlineStr"><is><t>Score</t></is></c></row><row r="2"><c t="inlineStr"><is><t>Asha</t></is></c><c><v>98</v></c></row></sheetData></worksheet>'''
        with zipfile.ZipFile(source, "w") as book:
            book.writestr("xl/worksheets/sheet1.xml", worksheet)
        schema = import_dataset(source, self.root / "xlsx.sqlite3")
        self.assertEqual(schema["row_count"], 1)
        self.assertEqual(schema["columns"][1], {"name": "score", "type": "INTEGER"})

    def test_imports_json_records(self):
        source = self.root / "products.json"
        source.write_text('[{"Product": "Pen", "Price": 10.5}, {"Product": "Book", "Price": 120}]', encoding="utf-8")
        schema = import_dataset(source, self.root / "json.sqlite3")
        self.assertEqual(schema["row_count"], 2)
        self.assertEqual([item["name"] for item in schema["columns"]], ["product", "price"])


if __name__ == "__main__":
    unittest.main()
