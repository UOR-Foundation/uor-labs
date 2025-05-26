import unittest

from uor.compiler.lexer import Lexer
from uor.compiler.parser import Parser, ProgramNode, VarDeclNode
from uor.compiler.codegen import CodeGenerator


class LexerParserCodegenTest(unittest.TestCase):
    def test_lexer_basic(self):
        tokens = list(Lexer("let x = 1;").tokenize())
        types_vals = [(t.type, t.value) for t in tokens]
        self.assertEqual(types_vals, [
            ("KEYWORD", "let"),
            ("IDENTIFIER", "x"),
            ("=", "="),
            ("NUMBER", "1"),
            (";", ";"),
        ])

    def test_parser(self):
        ast = Parser.from_text("let x = 1;").parse()
        self.assertIsInstance(ast, ProgramNode)
        self.assertIsInstance(ast.body[0], VarDeclNode)

    def test_codegen_nonempty(self):
        src = "let x = 1; x = x + 2;"
        ast = Parser.from_text(src).parse()
        program = CodeGenerator().generate(ast)
        self.assertTrue(program.instructions)


if __name__ == "__main__":
    unittest.main()
