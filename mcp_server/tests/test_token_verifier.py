from __future__ import annotations

import unittest

from albayan_mcp.token_verifier import PassThroughTokenVerifier


class PassThroughTokenVerifierTests(unittest.IsolatedAsyncioTestCase):
    async def test_accepts_agent_key_without_changing_it(self) -> None:
        token = await PassThroughTokenVerifier().verify_token("alb_hosted")

        self.assertIsNotNone(token)
        assert token is not None
        self.assertEqual(token.token, "alb_hosted")

    async def test_rejects_empty_bearer(self) -> None:
        token = await PassThroughTokenVerifier().verify_token("   ")

        self.assertIsNone(token)


if __name__ == "__main__":
    unittest.main()
