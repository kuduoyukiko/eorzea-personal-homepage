import logging
import smtplib
from email.message import EmailMessage
from threading import Thread

from utils.mail_settings import effective_mail_config


logger = logging.getLogger(__name__)


def _send_notification(config, message_data, admin_url):
    email = EmailMessage()
    email["Subject"] = f"[艾欧泽亚留言簿] 来自 {message_data['name']} 的新留言"
    email["From"] = config["MAIL_SENDER"]
    email["To"] = config["MAIL_RECIPIENT"]
    game_id, separator, server = message_data["name"].partition("@")
    email.set_content(
        "你的网站收到了一条新留言。\n\n"
        f"访客昵称 / 游戏 ID：{game_id}\n"
        f"服务器：{server if separator else '未填写'}\n"
        f"提交时间：{message_data['time']}\n\n"
        "留言正文：\n"
        f"{message_data['content']}\n\n"
        f"后台管理：{admin_url}\n"
    )

    with smtplib.SMTP_SSL(
        config["MAIL_SMTP_HOST"],
        config["MAIL_SMTP_PORT"],
        timeout=config["MAIL_TIMEOUT"],
    ) as smtp:
        smtp.login(config["MAIL_SENDER"], config["MAIL_AUTH_CODE"])
        smtp.send_message(email)


def queue_new_message_notification(app, message_data, admin_url):
    config = effective_mail_config(app)
    required = ("MAIL_SENDER", "MAIL_AUTH_CODE", "MAIL_RECIPIENT")
    if not config["MAIL_ENABLED"] or not all(config.get(key) for key in required):
        return False

    mail_config = {key: config[key] for key in (
        "MAIL_SMTP_HOST", "MAIL_SMTP_PORT", "MAIL_TIMEOUT",
        "MAIL_SENDER", "MAIL_AUTH_CODE", "MAIL_RECIPIENT"
    )}

    def send_safely():
        try:
            _send_notification(mail_config, message_data, admin_url)
        except Exception:
            logger.exception("新留言邮件通知发送失败，留言已正常保存")

    try:
        Thread(target=send_safely, name="message-email-notification", daemon=True).start()
        return True
    except Exception:
        logger.exception("新留言邮件通知任务启动失败，留言已正常保存")
        return False
