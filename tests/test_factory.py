import asyncio
import unittest
from unittest import mock

from uor.agents.factory import AppFactory


class AppFactoryTest(unittest.TestCase):
    def test_build_app(self):
        planner = mock.AsyncMock()
        coder = mock.AsyncMock()
        tester = mock.AsyncMock()

        planner.run.return_value = 'plan'
        coder.run.return_value = 'code'
        tester.run.return_value = 'checked'

        factory = AppFactory()
        factory.planner = planner
        factory.coder = coder
        factory.tester = tester

        with mock.patch('assembler.assemble', return_value=[1]), \
             mock.patch('uor.ipfs_storage.add_data', return_value='CID') as add:
            cid = asyncio.run(factory.build_app('goal'))

        self.assertEqual(cid, 'CID')
        planner.run.assert_called_with('goal')
        coder.run.assert_called_with('plan')
        tester.run.assert_called_with('code')
        add.assert_called()


if __name__ == '__main__':
    unittest.main()
