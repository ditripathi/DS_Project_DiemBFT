import unittest
from unittest import TestCase

from src.block import VoteInfo
from src.crypto import hasher, sign
from nacl.signing import SigningKey


class TestCrypto(TestCase):
    def setUp(self) -> None:
        self.priv_key = SigningKey.generate()
        self.pub_key = self.priv_key.verify_key

    def test_hasher_when_message_are_strings_returns_strings(self):
        msg = "Hello World"
        digest = hasher(msg)
        self.assertIsInstance(digest, str)

    def test_hasher_when_msg_are_same_strings_validate(self):
        msg1 = "Hello World"
        msg2 = "Hello World"
        digest1 = hasher(msg1)
        digest2 = hasher(msg2)
        self.assertEqual(digest1, digest2)

    def test_hasher_when_msg_are_different_strings_fail_validate(self):
        msg1 = "Hello World"
        msg2 = "Hola World"
        digest1 = hasher(msg1)
        digest2 = hasher(msg2)
        self.assertNotEqual(digest1, digest2)

    def test_hasher_when_msg_is_dataclass(self):
        msg = VoteInfo('abc', 5464, 'sadbjasdjb', 8574, 'asidnasiodn')
        digest = hasher(msg)
        # print(digest)
        self.assertIsInstance(digest, str)

    def test_hasher_when_msg_are_same_dataclasses_then_validate(self):
        msg1 = VoteInfo('abc', 5464, 'sadbjasdjb', 8574, 'asidnasiodn')
        msg2 = VoteInfo('abc', 5464, 'sadbjasdjb', 8574, 'asidnasiodn')
        digest1 = hasher(msg1)
        digest2 = hasher(msg2)
        self.assertEqual(digest1, digest2)

    def test_hasher_when_multiple_items(self):
        digest1 = hasher('client 1', 11, 'asjbsadjb', 5, '6947sadbiodnasd')
        digest2 = hasher('client 1', 11, 'asjbsadjb', 5, '6947sadbiodnasd')
        self.assertEqual(digest1, digest2)

    def test_sign_when_zero_items_throw_exception(self):
        with self.assertRaises(Exception) as ctx:
            sign(self.priv_key)

    def test_sign_when_single_item_generate_sign(self):
        with self.assertRaises(Exception) as ctx:
            sign(self.priv_key, '')


if __name__ == "__main__":
    unittest.main()
