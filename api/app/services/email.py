import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
from app.services.email_templates import reset_password_template


def send_reset_email(to_email: str, reset_link: str):

    msg = MIMEMultipart("alternative")

    msg["Subject"] = "Восстановление пароля"
    msg["From"] = SMTP_USER
    msg["To"] = to_email

    html = reset_password_template(reset_link)
    msg.attach(MIMEText(html, "html"))
    
    server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT)
    server.login(SMTP_USER, SMTP_PASSWORD)
    server.send_message(msg)
    server.quit()