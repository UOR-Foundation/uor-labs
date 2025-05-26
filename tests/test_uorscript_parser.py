import unittest

from uor.uscript import (
    Lexer,
    Parser,
    ProgramNode,
    FunctionNode,
    ObjectNode,
)


class UORScriptParserTest(unittest.TestCase):
    def test_parse_function(self):
        src = "function add(a: int, b: int) -> int { return a + b; }"
        ast = Parser.from_text(src).parse()
        self.assertIsInstance(ast, ProgramNode)
        self.assertIsInstance(ast.body[0], FunctionNode)
        fn = ast.body[0]
        self.assertEqual(fn.name, "add")
        self.assertEqual(len(fn.params), 2)
        self.assertEqual(fn.return_type.name, "int")

    def test_parse_object(self):
        src = "@coherent object Point { x: int; y: int; }"
        ast = Parser.from_text(src).parse()
        self.assertIsInstance(ast.body[0], ObjectNode)
        obj = ast.body[0]
        self.assertTrue(obj.coherent)
        self.assertEqual(obj.name, "Point")
        self.assertEqual(len(obj.members), 2)


if __name__ == "__main__":
    unittest.main()
