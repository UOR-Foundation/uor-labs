import asyncio
import unittest
from unittest import mock

from uor.llm import templates
from uor.llm.providers import LLMProvider


class DummyProvider(LLMProvider):
    async def _send_request(self, prompt: str) -> str:
        return prompt.upper()


class LLMIntegrationTest(unittest.TestCase):
    def test_provider_with_template(self):
        tmpl = templates.load_template("sort")
        prov = DummyProvider()
        text = asyncio.run(prov.generate_code(tmpl.render(algorithm="bubble", language="Python")))
        self.assertIn("BUBBLE", text)

    def test_template_validation_errors(self):
        with self.assertRaises(ValueError):
            templates._validate_template({"prompt": 123})
        with self.assertRaises(ValueError):
            templates._validate_template({"prompt": "x", "examples": ["bad"]})


if __name__ == "__main__":
    unittest.main()
