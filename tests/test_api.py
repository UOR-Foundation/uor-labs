import unittest

from uor import api


class APITest(unittest.TestCase):
    def test_run_program_output(self):
        asm = "PUSH 1\nPRINT"
        out = api.run_program(asm)
        self.assertEqual(out, "1")

    def test_type_error_non_string(self):
        with self.assertRaises(TypeError):
            api.run_program(123)

    def test_unknown_instruction_error(self):
        with self.assertRaises(ValueError):
            api.run_program("FOO")


if __name__ == "__main__":
    unittest.main()
