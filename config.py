import os
from dotenv import load_dotenv

load_dotenv()  # 加载.env文件


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    # Admin authentication lasts only for the current browser session.
    # The versioned name invalidates older login cookies after deployment.
    SESSION_COOKIE_NAME = "yukiko_session_v2"
    SESSION_PERMANENT = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False  # The current production site is HTTP-only.
    REMEMBER_COOKIE_NAME = "yukiko_remember_v2"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = False
    # 管理员账号
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
    MAIL_SMTP_HOST = os.getenv("MAIL_SMTP_HOST", "smtp.qq.com")
    MAIL_SMTP_PORT = int(os.getenv("MAIL_SMTP_PORT", "465"))
    MAIL_TIMEOUT = int(os.getenv("MAIL_TIMEOUT", "10"))
    MAIL_SENDER = os.getenv("MAIL_SENDER", "")
    MAIL_AUTH_CODE = os.getenv("MAIL_AUTH_CODE", "")
    MAIL_RECIPIENT = os.getenv("MAIL_RECIPIENT", "")
    SITE_URL = os.getenv("SITE_URL", "").rstrip("/")
    INTRO_VIDEO_URL = os.getenv("INTRO_VIDEO_URL", "")
    SITE_MODE = os.getenv("SITE_MODE", "dual").strip().lower()
    if SITE_MODE not in {"single", "dual"}:
        SITE_MODE = "dual"
    # 数据文件路径
    DATA_PATH = os.path.join(os.path.dirname(__file__), "data")
