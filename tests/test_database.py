import unittest

from src.database import execute_generated_sql


class DatabaseTests(unittest.TestCase):
    def test_executes_generated_select(self):
        columns, rows = execute_generated_sql("SELECT name FROM students WHERE cgpa > 8;")
        self.assertEqual(columns, ["name"])
        self.assertEqual([row["name"] for row in rows], ["Ananya", "Charan"])

    def test_blocks_non_select_sql(self):
        with self.assertRaises(ValueError):
            execute_generated_sql("DELETE FROM students;")


if __name__ == "__main__":
    unittest.main()
