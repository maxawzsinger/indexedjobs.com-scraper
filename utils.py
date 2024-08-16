import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def extract_location_details(location_str):
    suburb, state, country = "", "", ""
    parts = location_str.split(", ")
    if len(parts) == 3:
        suburb, state, country = parts
    return suburb, state, country


def send_gmail(subject: str, body: str, to_email: str):
    from_email = ""
    password = ""

    try:
        server = smtplib.SMTP(host="smtp.gmail.com", port=587)
        server.starttls()
        server.login(from_email, password)

        msg = MIMEMultipart()
        msg["From"] = from_email
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))

        server.send_message(msg)
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email to {to_email}. Error: {e}")
    finally:
        server.quit()
