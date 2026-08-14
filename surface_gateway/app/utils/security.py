import hashlib
import hmac


def verify_github_signature(raw_body: bytes, signature_header: str | None, secret: str) -> bool:
    """
    Verifies that the incoming GitHub webhook payload matches the X-Hub-Signature-256 header.
    """
    if not secret:
        return False

    if not signature_header:
        return False

    if not signature_header.startswith("sha256="):
        return False

    expected_sig = signature_header[7:]
    computed_sig = hmac.new(
        secret.encode("utf-8"),
        raw_body,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(computed_sig, expected_sig)
