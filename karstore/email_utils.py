from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os

def send_email(to_email, subject, message):
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        email = Mail(
            from_email=os.environ.get('DEFAULT_FROM_EMAIL'),
            to_emails=to_email,
            subject=subject,
            plain_text_content=message
        )
        sg.send(email)
        print(f"[EMAIL] SUCCESS - {to_email}")
    except Exception as e:
        print(f"[EMAIL] FAILED - {e}")