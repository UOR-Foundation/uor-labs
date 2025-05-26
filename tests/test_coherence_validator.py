import unittest

import chunks
from decoder import decode
from vm import VM
from uor.vm.coherence import CoherenceValidator, CoherenceMode
from uor.exceptions import CoherenceViolationError


class CoherenceValidatorTest(unittest.TestCase):
    def test_strict_violation(self):
        prog = decode([chunks.chunk_push(1)])
        validator = CoherenceValidator(tolerance=0.0, mode=CoherenceMode.STRICT)
        vm = VM(coherence_validator=validator)
        with self.assertRaises(CoherenceViolationError):
            list(vm.execute(prog))

    def test_tolerant_restores(self):
        prog = decode([chunks.chunk_push(1), chunks.chunk_print()])
        validator = CoherenceValidator(tolerance=0.0, mode=CoherenceMode.TOLERANT)
        vm = VM(coherence_validator=validator)
        ''.join(vm.execute(prog))
        self.assertGreater(validator.restorations, 0)

    def test_disabled_no_checks(self):
        prog = decode([chunks.chunk_push(1), chunks.chunk_print()])
        validator = CoherenceValidator(tolerance=0.0, mode=CoherenceMode.DISABLED)
        vm = VM(coherence_validator=validator)
        out = ''.join(vm.execute(prog))
        self.assertEqual(out, '1')
        self.assertEqual(validator.restorations, 0)


if __name__ == '__main__':
    unittest.main()
