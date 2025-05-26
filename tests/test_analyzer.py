import asyncio
import textwrap
import unittest
from unittest import mock

from uor.llm.analyzer import CodeAnalyzer


class CodeAnalyzerTest(unittest.TestCase):
    def test_basic_metrics(self):
        code = textwrap.dedent(
            """
            def foo(x):
                for i in range(x):
                    x += i
                return x
            """
        )
        analyzer = CodeAnalyzer(code)
        self.assertIn('i', analyzer.variables_defined)
        self.assertIn('x', analyzer.variables_used)
        self.assertEqual(analyzer.loops, [3])
        self.assertGreaterEqual(analyzer.complexity, 2)
        # check loop edge exists
        self.assertIn(3, analyzer.cfg.edges.get(4, set()))

    def test_llm_helpers(self):
        code = "a = 1"
        analyzer = CodeAnalyzer(code)

        provider = mock.MagicMock()
        provider.explain_code = mock.AsyncMock(return_value='exp')
        provider._call = mock.AsyncMock(return_value='cmp')

        async def fake_stream(prompt: str):
            for ch in 'ok':
                yield ch
        provider.stream = fake_stream

        result = asyncio.run(analyzer.explain(provider))
        self.assertEqual(result, 'exp')
        provider.explain_code.assert_awaited_with(code)

        result = asyncio.run(analyzer.compare('b = 2', provider))
        provider._call.assert_awaited()
        self.assertEqual(result, 'cmp')

        result = asyncio.run(analyzer.ask('why?', provider))
        self.assertEqual(result, 'cmp')

        async def gather():
            return ''.join([chunk async for chunk in analyzer.stream_qa('q?', provider)])
        out = asyncio.run(gather())
        self.assertEqual(out, 'ok')


if __name__ == '__main__':
    unittest.main()
