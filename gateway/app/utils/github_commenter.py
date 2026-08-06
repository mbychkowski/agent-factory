import logging
import os
import time

import requests
from google.auth import crypt, jwt

logger = logging.getLogger(__name__)


def get_github_installation_token() -> str:
    app_id = os.getenv("GITHUB_APP_ID", "4487667")
    installation_id = os.getenv("GITHUB_APP_INSTALLATION_ID", "151266010")
    pem_string = os.getenv("GITHUB_APP_PRIVATE_KEY")

    private_key_str = ""
    if pem_string:
        private_key_str = pem_string.replace("\\n", "\n")
    else:
        candidate_paths = [
            os.getenv("GITHUB_APP_PRIVATE_KEY_PATH"),
            "gateway/app/private-key.pem",
            "app/private-key.pem",
            "private-key.pem",
            "./agent-factory-spec-deliberator.2026-08-04.private-key.pem",
        ]
        for path in filter(None, candidate_paths):
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        private_key_str = f.read()
                    if private_key_str.strip():
                        logger.info(f"[GitHub Commenter] Loaded private key from {path}")
                        break
                except Exception:
                    pass


    if not private_key_str or not app_id or not installation_id:
        logger.warning("[GitHub Commenter] Missing GitHub App credentials or private key.")
        return ""

    try:
        signer = crypt.RSASigner.from_string(private_key_str)
        now = int(time.time())
        payload = {"iat": now - 60, "exp": now + (10 * 60), "iss": app_id}
        jwt_token = jwt.encode(signer, payload).decode("utf-8")

        url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
        resp = requests.post(
            url,
            headers={"Authorization": f"Bearer {jwt_token}", "Accept": "application/vnd.github+json"},
            timeout=10,
        )
        if resp.status_code in (200, 201):
            return resp.json().get("token", "")
        else:
            logger.error(f"[GitHub Commenter] Access token error ({resp.status_code}): {resp.text}")
    except Exception as e:
        logger.error(f"[GitHub Commenter Error] Could not obtain installation token: {e}")
    return ""


def post_agent_github_comment(issue_id: int, comment_body: str) -> bool:
    """Posts a comment back to the GitHub issue on behalf of the agent."""
    if not comment_body or not comment_body.strip():
        logger.warning("[GitHub Commenter] Empty comment body provided. Skipping post.")
        return False

    token = get_github_installation_token()
    if not token:
        logger.error("[GitHub Commenter] No installation token available.")
        return False

    repo = os.getenv("GITHUB_REPO", "mbychkowski/agent-factory")
    url = f"https://api.github.com/repos/{repo}/issues/{issue_id}/comments"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    try:
        resp = requests.post(url, headers=headers, json={"body": comment_body}, timeout=15)
        if resp.status_code in (200, 201):
            comment_data = resp.json()
            logger.info(f"[GitHub Commenter] Posted comment #{comment_data.get('id')} to Issue #{issue_id}")
            return True
        else:
            logger.error(f"[GitHub Commenter] Failed to post comment ({resp.status_code}): {resp.text}")
            return False
    except Exception as e:
        logger.error(f"[GitHub Commenter] Failed to post comment: {e}")
        return False
