import importlib
import sys
import unittest
from unittest import mock

from uor.addressing import canonical_address, DHT
import primes

class CanonicalAddressTest(unittest.TestCase):
    def setUp(self):
        # fake ipfshttpclient module
        self.fake_ipfs = mock.MagicMock()
        self.patcher = mock.patch.dict(sys.modules, {'ipfshttpclient': self.fake_ipfs})
        self.patcher.start()
        import uor.ipfs_storage as ipfs_storage
        importlib.reload(ipfs_storage)
        self.ipfs = ipfs_storage

    def tearDown(self):
        self.patcher.stop()

    def test_canonical_prime(self):
        data = b'hello world'
        addr = canonical_address(data)
        self.assertTrue(primes.miller_rabin(addr))

    def test_store_and_retrieve(self):
        dht = DHT(nodes=2, cache_size=2)
        # mock ipfs add/get
        self.fake_ipfs.connect.return_value.__enter__.return_value = self.fake_ipfs
        self.fake_ipfs.add_bytes.return_value = 'CID'
        self.fake_ipfs.cat.return_value = b'hello'
        addr = dht.store('org.uor.test', b'hello')
        out = dht.retrieve(addr)
        self.assertEqual(out, b'hello')
        # cached retrieval should not call IPFS again
        self.fake_ipfs.cat.reset_mock()
        out2 = dht.retrieve(addr)
        self.assertEqual(out2, b'hello')
        self.fake_ipfs.cat.assert_not_called()
        self.assertEqual(dht.resolve('org.uor.test'), addr)

if __name__ == '__main__':
    unittest.main()
