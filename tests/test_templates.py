import unittest
from uor.llm.templates import PromptTemplate, load_template


class PromptTemplateTest(unittest.TestCase):
    def test_add_example_and_render(self):
        tmpl = PromptTemplate("Hello {name}")
        tmpl.add_example("Alice", "Hi Alice")
        text = tmpl.render(name="Bob")
        self.assertIn("Hello Bob", text)
        self.assertIn("Input: Alice", text)
        self.assertIn("Output: Hi Alice", text)


class LoaderTest(unittest.TestCase):
    def test_load_yaml_template(self):
        tmpl = load_template("sort")
        result = tmpl.render(algorithm="bubble sort", language="Python")
        self.assertIn("bubble sort", result)
        self.assertIn("Python", result)

    def test_load_json_template(self):
        tmpl = load_template("file_ops.json")
        result = tmpl.render(action="read", language="Python")
        self.assertIn("read", result)
        self.assertIn("Python", result)


if __name__ == "__main__":
    unittest.main()
