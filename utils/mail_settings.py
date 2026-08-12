import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from utils import data_utils


SETTINGS_FILE = "mail_settings.json"


def _cipher(secret_key):
    digest = hashlib.sha256(str(secret_key).encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_auth_code(secret_key, auth_code):
    return _cipher(secret_key).encrypt(auth_code.encode("utf-8")).decode("ascii")


def decrypt_auth_code(secret_key, encrypted_auth_code):
    if not encrypted_auth_code:
        return ""
    try:
        return _cipher(secret_key).decrypt(encrypted_auth_code.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError, TypeError):
        return ""


def load_stored_settings():
    settings = data_utils.read_json(SETTINGS_FILE)
    return settings if isinstance(settings, dict) else {}


def save_stored_settings(settings):
    data_utils.write_json(SETTINGS_FILE, settings)


def effective_mail_config(app):
    stored = load_stored_settings()
    has_stored_settings = bool(stored)
    encrypted_code = stored.get("auth_code_encrypted", "")
    stored_code = decrypt_auth_code(app.config["SECRET_KEY"], encrypted_code)
    return {
        "MAIL_ENABLED": stored.get("enabled", True) if has_stored_settings else True,
        "MAIL_SMTP_HOST": stored.get("smtp_host") or app.config.get("MAIL_SMTP_HOST", "smtp.qq.com"),
        "MAIL_SMTP_PORT": int(stored.get("smtp_port") or app.config.get("MAIL_SMTP_PORT", 465)),
        "MAIL_TIMEOUT": int(app.config.get("MAIL_TIMEOUT", 10)),
        "MAIL_SENDER": stored.get("sender") or app.config.get("MAIL_SENDER", ""),
        "MAIL_AUTH_CODE": stored_code or app.config.get("MAIL_AUTH_CODE", ""),
        "MAIL_RECIPIENT": stored.get("recipient") or app.config.get("MAIL_RECIPIENT", ""),
        "AUTH_CODE_CONFIGURED": bool(stored_code or app.config.get("MAIL_AUTH_CODE", "")),
    }
