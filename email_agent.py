import os
import logging
import smtplib
from typing import Dict
from email.message import EmailMessage
from agents import Agent, function_tool


# @function_tool
# def push(subject: str, message: str) -> Dict[str, str]:
#     push_mail = os.getenv("CLONE_EMAIL")
#     push_password = os.getenv("CLONE_PASSWORD")    
#     if not push_mail or not push_password:
#         print("Error: CLONE_EMAIL or CLONE_PASSWORD not found in environment variables")
#         print("Please create a .env file with CLONE_EMAIL and CLONE_PASSWORD")
#         return
#     try:
#         mail=smtplib.SMTP("smtp.gmail.com")
#         mail.starttls()
#         mail.login(user=push_mail, password=push_password)
#         mail.sendmail(
#             from_addr=push_mail, 
#             to_addrs="rumesefia@gmail.com", 
#             msg=f"Subject:{subject}\n\n{message}"
#             )
#         mail.quit()
#         status = "Email sent successfully"
#     except Exception as e:
#         status = "Error sending email: {e}"
#     finally:
#         return {"status": status}
    
# INSTRUCTIONS = """You are able to send a nicely formatted HTML email based on a detailed report.
# You will be provided with a detailed report. You should use your tool to send one email, providing the 
# report converted into clean, well presented HTML with an appropriate subject line."""

# email_agent = Agent(
#     name="Email Agent",
#     instructions=INSTRUCTIONS,
#     model="gpt-4o-mini",
#     tools=[push],
#     handoff_description= "Send a formatted email of the report"
# )



logger = logging.getLogger(__name__)

def _sanitize_subject(subject: str) -> str:
    if subject is None:
        return "Research Report"
    s = str(subject).replace("\n", " ").replace("\r", " ")
    return s[:200]

@function_tool
def push(subject: str, message: str) -> Dict[str, str]:
    """
    Send an HTML email using SMTP credentials stored in env variables.
    This function performs basic sanitization and limits recipients to configured env var.
    Returns {"status": "..."}.
    """
    sender = os.getenv("CLONE_EMAIL")
    password = os.getenv("CLONE_PASSWORD")
    recipient = os.getenv("REPORT_RECIPIENT")  # prefer configured recipient
    smtp_host = "smtp.gmail.com"
    smtp_port = 587

    if not sender or not password or not recipient:
        logger.error("Email credentials or recipient not configured in env; aborting email send.")
        return {"status": "Email disabled: missing configuration."}

    subj = _sanitize_subject(subject)
    msg = EmailMessage()
    msg["Subject"] = subj
    msg["From"] = sender
    msg["To"] = recipient
    msg.set_content(message, subtype="html")

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as mail:
            mail.starttls()
            mail.login(user=sender, password=password)
            mail.send_message(msg)
        status = "Email sent successfully"
    except Exception as e:
        logger.exception("Error sending email")
        status = f"Error sending email: {e}"
    return {"status": status}

INSTRUCTIONS = """You are able to send a nicely formatted HTML email based on a detailed report.
You will be provided with a detailed report. You should use your tool to send one email, providing the 
report converted into clean, well presented HTML with an appropriate subject line."""

email_agent = Agent(
    name="Email Agent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    tools=[push],
    handoff_description="Send a formatted email of the report"
)