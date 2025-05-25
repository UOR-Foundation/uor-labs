import importlib
import os
import sys
import types
import unittest
from unittest import mock


def _load_module(modules: dict[str, object]):
    with mock.patch.dict(sys.modules, modules):
        sys.modules.pop('uor.llm_client', None)
        import uor.llm_client as lc
        return importlib.reload(lc)


class LLMClientTest(unittest.TestCase):
    def test_openai(self):
        fake_openai = types.ModuleType('openai')
        chat = mock.MagicMock()
        fake_openai.ChatCompletion = chat
        resp = mock.MagicMock()
        resp.choices = [mock.MagicMock(message=mock.MagicMock(content='ok'))]
        chat.create.return_value = resp

        modules = {
            'openai': fake_openai,
            'anthropic': types.ModuleType('anthropic'),
            'google': types.ModuleType('google'),
            'google.generativeai': mock.MagicMock(),
        }
        with mock.patch.dict(os.environ, {'OPENAI_API_KEY': 'k'}):
            mod = _load_module(modules)
            result = mod.call_model('openai', 'hi')
        self.assertEqual(result, 'ok')
        chat.create.assert_called()

    def test_anthropic(self):
        fake_anthropic = types.ModuleType('anthropic')
        client_inst = mock.MagicMock()
        fake_anthropic.Anthropic = mock.MagicMock(return_value=client_inst)
        resp = mock.MagicMock(content='anthro')
        client_inst.messages.create.return_value = resp

        modules = {
            'openai': types.ModuleType('openai'),
            'anthropic': fake_anthropic,
            'google': types.ModuleType('google'),
            'google.generativeai': mock.MagicMock(),
        }
        with mock.patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'k'}):
            mod = _load_module(modules)
            result = mod.call_model('anthropic', 'hi')
        self.assertEqual(result, 'anthro')
        client_inst.messages.create.assert_called()

    def test_gemini(self):
        fake_google = types.ModuleType('google')
        genai = mock.MagicMock()
        fake_google.generativeai = genai
        resp = mock.MagicMock(text='gem')
        model = mock.MagicMock(generate_content=mock.MagicMock(return_value=resp))
        genai.GenerativeModel.return_value = model

        modules = {
            'openai': types.ModuleType('openai'),
            'anthropic': types.ModuleType('anthropic'),
            'google': fake_google,
            'google.generativeai': genai,
        }
        with mock.patch.dict(os.environ, {'GOOGLE_API_KEY': 'k'}):
            mod = _load_module(modules)
            result = mod.call_model('gemini', 'hi')
        self.assertEqual(result, 'gem')
        model.generate_content.assert_called_with('hi')

    def test_unknown_provider(self):
        modules = {
            'openai': types.ModuleType('openai'),
            'anthropic': types.ModuleType('anthropic'),
            'google': types.ModuleType('google'),
            'google.generativeai': mock.MagicMock(),
        }
        mod = _load_module(modules)
        with self.assertRaises(ValueError):
            mod.call_model('foo', 'hi')


if __name__ == '__main__':
    unittest.main()
