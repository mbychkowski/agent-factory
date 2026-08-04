import hmac
import hashlib
import json
import unittest
from fastapi.testclient import TestClient

from gateway.main import app
from gateway.app.config import config
from gateway.app.utils.security import verify_github_signature
from gateway.app.utils.bot_filter import is_bot_event


class TestGatewayModule(unittest.TestCase):

    def setUp(self) -> None:
        self.client = TestClient(app)
        self.secret = config.github_webhook_secret or "dev_secret_change_me"

    def _get_signature_header(self, raw_bytes: bytes) -> str:
        sig = hmac.new(self.secret.encode("utf-8"), raw_bytes, hashlib.sha256).hexdigest()
        return f"sha256={sig}"

    def test_health_check(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")

    def test_signature_verification(self) -> None:
        raw_body = b'{"test": "payload"}'
        sig = self._get_signature_header(raw_body)

        self.assertTrue(verify_github_signature(raw_body, sig, self.secret))
        self.assertFalse(verify_github_signature(raw_body, "sha256=invalid", self.secret))

    def test_bot_filter(self) -> None:
        bot_payload = {
            "sender": {"type": "Bot", "login": "github-actions[bot]"},
            "comment": {"user": {"type": "Bot", "login": "github-actions[bot]"}}
        }
        human_payload = {
            "sender": {"type": "User", "login": "mbychkowski"},
            "comment": {"user": {"type": "User", "login": "mbychkowski"}}
        }

        self.assertTrue(is_bot_event(bot_payload))
        self.assertFalse(is_bot_event(human_payload))

    def test_github_webhook_human_comment(self) -> None:
        payload = {
            "action": "created",
            "issue": {"number": 100},
            "comment": {
                "id": 456,
                "body": "Use Cloud Spanner for global scalability.",
                "user": {"type": "User", "login": "alice_pm"}
            },
            "sender": {"type": "User", "login": "alice_pm"}
        }

        body_bytes = json.dumps(payload).encode("utf-8")
        headers = {
            "X-GitHub-Event": "issue_comment",
            "X-Hub-Signature-256": self._get_signature_header(body_bytes),
            "Content-Type": "application/json",
        }

        response = self.client.post(
            "/webhooks/github",
            content=body_bytes,
            headers=headers
        )

        self.assertEqual(response.status_code, 202)
        res_data = response.json()
        self.assertIn("accepted", res_data["status"])
        self.assertIsNotNone(res_data["event_id"])

    def test_github_webhook_bot_comment_dropped(self) -> None:
        payload = {
            "action": "created",
            "issue": {"number": 100},
            "comment": {
                "id": 789,
                "body": "Automated spec updated.",
                "user": {"type": "Bot", "login": "spec-agent[bot]"}
            },
            "sender": {"type": "Bot", "login": "spec-agent[bot]"}
        }

        body_bytes = json.dumps(payload).encode("utf-8")
        headers = {
            "X-GitHub-Event": "issue_comment",
            "X-Hub-Signature-256": self._get_signature_header(body_bytes),
            "Content-Type": "application/json",
        }

        response = self.client.post(
            "/webhooks/github",
            content=body_bytes,
            headers=headers
        )

        self.assertEqual(response.status_code, 200)
        res_data = response.json()
        self.assertEqual(res_data["status"], "ignored_bot")


if __name__ == "__main__":
    unittest.main()
