from email.message import EmailMessage
import smtplib
from celery import Celery
import os
from dotenv import load_dotenv


REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery("tasks", broker=REDIS_URL, backend=REDIS_URL)
load_dotenv()

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    timezone="Asia/Almaty",
    enable_utc=True,
)

@celery_app.task(name="send_welcome_email_task")
def send_welcome_email(receiver_email: str):
    SMTP_SERVER = os.getenv("SMTP_SERVER")
    SMTP_PORT = os.getenv("SMTP_PORT")
    SENDER_EMAIL = os.getenv("SENDER_EMAIL")
    SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

    msg = EmailMessage()
    msg["Subject"] = "Добро пожаловать в SuccessTracker!"
    msg["From"] = SENDER_EMAIL
    msg["To"] = receiver_email
    msg.set_content(f"Привет! Ты успешно зарегистрирован. Твой email: {receiver_email}")

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        return f"Email реально отправлен на {receiver_email}"
    except Exception as e:
        return f"Ошибка при отправке: {str(e)}"