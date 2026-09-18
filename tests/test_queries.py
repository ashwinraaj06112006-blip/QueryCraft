import unittest

from src.errors import LexicalError, SemanticError, SyntaxError
from src.main import compile_query


class QueryCraftTests(unittest.TestCase):
    def sql(self, query):
        return compile_query(query)[2]

    def test_show_all(self): self.assertEqual(self.sql("Show all students"), "SELECT * FROM students;")
    def test_projection(self): self.assertEqual(self.sql("Show student names"), "SELECT name FROM students;")
    def test_condition(self): self.assertEqual(self.sql("Show students whose CGPA is greater than 8"), "SELECT * FROM students WHERE cgpa > 8;")
    def test_department(self): self.assertEqual(self.sql("Show students from CSE department"), "SELECT * FROM students WHERE department = 'cse';")
    def test_ordering(self): self.assertEqual(self.sql("Show students ordered by CGPA"), "SELECT * FROM students ORDER BY cgpa ASC;")
    def test_top(self): self.assertEqual(self.sql("Show top 5 students by CGPA"), "SELECT * FROM students ORDER BY cgpa DESC LIMIT 5;")
    def test_count(self): self.assertEqual(self.sql("Count students"), "SELECT COUNT(*) FROM students;")
    def test_and(self): self.assertEqual(self.sql("Show students where CGPA greater than 8 and age greater than 19"), "SELECT * FROM students WHERE cgpa > 8 AND age > 19;")
    def test_unknown_attribute(self):
        with self.assertRaises(SemanticError): self.sql("Show students where salary greater than 10")
    def test_wrong_numeric_type(self):
        with self.assertRaises(SemanticError): self.sql('Show students where CGPA is "high"')
    def test_malformed_query(self):
        with self.assertRaises(SyntaxError): self.sql("Show students where CGPA greater than")
    def test_unsupported_query(self):
        with self.assertRaises(SyntaxError): self.sql("Delete students")
    def test_lexical_error(self):
        with self.assertRaises(LexicalError): self.sql("Show students @ CGPA")


if __name__ == "__main__":
    unittest.main()
