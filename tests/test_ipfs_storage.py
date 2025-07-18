import importlib
import sys
import unittest
from unittest import mock


class IPFSStorageTest(unittest.TestCase):
    def setUp(self):
        self.fake_module = mock.MagicMock()
        self.patcher = mock.patch.dict(sys.modules, {'ipfshttpclient': self.fake_module})
        self.patcher.start()
        import uor.ipfs_storage
        self.mod = importlib.reload(uor.ipfs_storage)

    def tearDown(self):
        self.patcher.stop()

    def test_add_data(self):
        fake_client = mock.MagicMock()
        fake_client.__enter__.return_value = fake_client
        fake_client.add_bytes.return_value = 'CID'
        self.fake_module.connect.return_value = fake_client
        cid = self.mod.add_data(b'hello')
        fake_client.add_bytes.assert_called_with(b'hello')
        self.assertEqual(cid, 'CID')

    def test_get_data(self):
        fake_client = mock.MagicMock()
        fake_client.__enter__.return_value = fake_client
        fake_client.cat.return_value = b'data'
        self.fake_module.connect.return_value = fake_client
        data = self.mod.get_data('CID')
        fake_client.cat.assert_called_with('CID')
        self.assertEqual(data, b'data')


if __name__ == '__main__':
    unittest.main()
