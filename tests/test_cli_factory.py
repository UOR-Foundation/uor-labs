import io
import contextlib
import unittest
from unittest import mock

import uor_cli


class CLIFactoryTest(unittest.TestCase):
    def test_factory_invokes_appfactory(self):
        async_mock = mock.AsyncMock(return_value='CID')
        with mock.patch.object(uor_cli, 'AppFactory') as Factory:
            inst = Factory.return_value
            inst.build_app = async_mock
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = uor_cli.main(['factory', '--provider', 'openai', 'goal'])
            self.assertEqual(rc, 0)
            async_mock.assert_called_with('goal')
            self.assertEqual(buf.getvalue().strip(), 'CID')


if __name__ == '__main__':
    unittest.main()
