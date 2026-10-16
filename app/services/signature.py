import hashlib
import hmac


def sign(body: bytes, secret: str) -> str:
    """HMAC-SHA256 от тела запроса, hex в нижнем регистре."""
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def is_valid_signature(body: bytes, signature: str, secret: str) -> bool:
    # Сравнение байтов: compare_digest на строках падает на не-ASCII символах в заголовке.
    expected = sign(body, secret).encode()
    return hmac.compare_digest(expected, signature.strip().lower().encode())
