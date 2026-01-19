import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import EMAIL
from logger import log

def send_email(body):
    if not EMAIL["sender"] or not EMAIL["password"]:
        raise RuntimeError("Email credentials missing")
    msg = MIMEMultipart()
    msg["From"] = EMAIL["sender"]
    msg["To"] = ", ".join(EMAIL["recipients"])
    msg["Subject"] = "Kenya Policy News Digest"
    msg.attach(MIMEText(body, "plain"))
    with smtplib.SMTP(EMAIL["smtp"], EMAIL["port"]) as server:
        server.starttls()
        server.login(EMAIL["sender"], EMAIL["password"])
        server.send_message(msg)
    log.info(f"Email sent to {EMAIL['recipients']}")
