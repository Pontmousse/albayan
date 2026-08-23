import unittest

from fastapi import HTTPException

from app.services import agent_token_service


class AgentTokenServiceTests(unittest.TestCase):
    def test_generate_token_has_prefix_and_hash(self) -> None:
        plaintext, token_hash = agent_token_service.generate_agent_token()
        self.assertTrue(plaintext.startswith("alb_"))
        self.assertEqual(len(token_hash), 64)

    def test_normalize_scopes_deduplicates(self) -> None:
        scopes = agent_token_service.normalize_scopes(
            ["articles:read", "profile:read", "articles:read"]
        )
        self.assertEqual(scopes, ["articles:read", "profile:read"])

    def test_normalize_scopes_rejects_unknown(self) -> None:
        with self.assertRaises(HTTPException) as ctx:
            agent_token_service.normalize_scopes(["articles:submit"])
        self.assertEqual(ctx.exception.status_code, 400)

    def test_default_scopes_subset_of_allowed(self) -> None:
        for scope in agent_token_service.DEFAULT_AGENT_SCOPES:
            self.assertIn(scope, agent_token_service.ALLOWED_AGENT_SCOPES)


if __name__ == "__main__":
    unittest.main()
