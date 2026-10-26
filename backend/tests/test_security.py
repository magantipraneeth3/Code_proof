import time
import unittest

import jwt

from app.core.ratelimit import SlidingWindowLimiter
from app.core.security import (DUMMY_HASH, create_access_token, decode_access_token,
                               hash_password, verify_password)


class PasswordTests(unittest.TestCase):
    def test_roundtrip_and_wrong_password(self):
        h = hash_password("correct horse battery")
        self.assertNotIn("correct horse", h)
        self.assertTrue(verify_password("correct horse battery", h))
        self.assertFalse(verify_password("wrong", h))

    def test_hashes_are_salted(self):
        self.assertNotEqual(hash_password("same-password"), hash_password("same-password"))

    def test_malformed_hash_is_rejected_not_raised(self):
        self.assertFalse(verify_password("x", "garbage"))
        self.assertFalse(verify_password("x", ""))
        self.assertFalse(verify_password("x", DUMMY_HASH))


class TokenTests(unittest.TestCase):
    def test_roundtrip(self):
        claims = decode_access_token(create_access_token(7, "professor"))
        self.assertEqual(claims["sub"], "7")
        self.assertEqual(claims["role"], "professor")

    def test_tampered_token_rejected(self):
        tok = create_access_token(1, "student")
        with self.assertRaises(jwt.PyJWTError):
            decode_access_token(tok[:-3] + "abc")

    def test_alg_none_rejected(self):
        forged = jwt.encode({"sub": "1", "exp": int(time.time()) + 60}, key=None, algorithm="none")
        with self.assertRaises(jwt.PyJWTError):
            decode_access_token(forged)

    def test_expired_rejected(self):
        tok = jwt.encode({"sub": "1", "exp": int(time.time()) - 10}, "x" * 40, algorithm="HS256")
        with self.assertRaises(jwt.PyJWTError):
            decode_access_token(tok)


class RateLimitTests(unittest.TestCase):
    def test_blocks_then_recovers(self):
        now = [0.0]
        rl = SlidingWindowLimiter(2, 60, clock=lambda: now[0])
        self.assertTrue(rl.allow("a")); self.assertTrue(rl.allow("a"))
        self.assertFalse(rl.allow("a"))
        self.assertTrue(rl.allow("b"))
        now[0] = 61
        self.assertTrue(rl.allow("a"))


if __name__ == "__main__":
    unittest.main()
