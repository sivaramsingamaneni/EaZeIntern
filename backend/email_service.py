import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for recruiter email (SMTP credentials are now fetched per-function)
RECRUITER_EMAIL = os.getenv("RECRUITER_EMAIL")


def send_confirmation_email(to_email: str, application_id: str):
    """
    Sends confirmation email to candidate
    """
    # Keys matching .env file
    sender_email = os.getenv("SMTP_EMAIL")
    sender_password = os.getenv("SMTP_PASSWORD")

    # 1. Log credential status
    if not sender_email or not sender_password:
        logger.error("[Email Service] Missing SMTP_EMAIL or SMTP_PASSWORD environment variables.")
        logger.info("   -> Please check your .env file.")
        logger.info("   -> Email sending SKIPPED.")
        return False

    msg = EmailMessage()
    msg['Subject'] = "Internship Application Received"
    msg['From'] = sender_email
    msg['To'] = to_email

    content = f"""
    <html>
    <body>
        <h3>Application Received</h3>
        <p>Thank you for applying for the internship.</p>
        <p>Your Application ID is: <strong>{application_id}</strong></p>
        <p>You can track your application status on your dashboard.</p>
        <br>
        <p>Best Regards,</p>
        <p>Team EazeIntern</p>
    </body>
    </html>
    """
    msg.set_content(content, subtype='html')

    try:
        # 2. Connect to Gmail SMTP Server
        logger.info(f"[Email Service] Connecting to smtp.gmail.com:587 for {to_email}...")
        
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls() # Secure the connection
            
            # 3. Login
            server.login(sender_email, sender_password)
            
            # 4. Send Email
            server.send_message(msg)
            
        logger.info(f"[Email Service] Email sent successfully to {to_email} (App ID: {application_id})")
        return True

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"[Email Service] Authentication Failed. Server response: {e}")
        logger.info("   -> Check SMTP_EMAIL and SMTP_PASSWORD in .env.")
        logger.info("   -> Ensure you are using an App Password (16 chars), not your login password.")
        return False
    except Exception as e:
        logger.error(f"[Email Service] Failed to send email: {e}")
        return False


def send_recruiter_notification(application_data: dict):
    """
    Sends new application alert to recruiter
    """
    sender_email = os.getenv("SMTP_EMAIL")
    sender_password = os.getenv("SMTP_PASSWORD")

    if not sender_email or not sender_password or not RECRUITER_EMAIL:
        logger.error("[Email Service] Missing credentials for recruiter notification.")
        return False

    candidate = application_data.get("candidate", {})

    msg = EmailMessage()
    msg["Subject"] = "Inbound: New Internship Application"
    msg["From"] = sender_email
    msg["To"] = RECRUITER_EMAIL

    content = f"""
    New application received!
    
    Name: {candidate.get("name")}
    Email: {candidate.get("email")}
    College: {candidate.get("college")}
    Degree: {candidate.get("degree")}
    
    Application ID: {application_data.get("application_id")}
    """
    msg.set_content(content)

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return True
    except Exception as e:
        logger.error(f"[Email Service] Failed to send recruiter email: {e}")
        return False
