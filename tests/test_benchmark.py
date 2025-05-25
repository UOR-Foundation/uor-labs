import time
import unittest

import assembler
from vm import VM
from decoder import decode


class DecodeBenchTest(unittest.TestCase):
    def test_reuse_decoded_program_faster(self):
        src = """
        PUSH 1
        PUSH 2
        ADD
        PRINT
        """
        prog = assembler.assemble(src)
        runs = 200

        start = time.time()
        for _ in range(runs):
            VM().execute(decode(prog))
        fresh_time = time.time() - start

        decoded = decode(prog)
        start = time.time()
        for _ in range(runs):
            VM().execute(decoded)
        reused_time = time.time() - start

        self.assertLess(reused_time, fresh_time)


if __name__ == "__main__":
    unittest.main()
