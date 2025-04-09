import os
import smtplib
import requests
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def send_email(recipient, subject, body, attachment=None, attachment_name=None):
    """
    Send an email with optional attachment.
    
    Parameters:
    - recipient: Email address of the recipient
    - subject: Email subject
    - body: Email body text
    - attachment: String content of the attachment (optional)
    - attachment_name: Filename for the attachment (optional)
    
    Returns:
    - Boolean indicating success or failure
    """
    try:
        # Get email configuration from environment variables
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_username = os.getenv("SMTP_USERNAME", "")
        smtp_password = os.getenv("SMTP_PASSWORD", "")
        
        # If credentials are missing, log an error and return
        if not smtp_username or not smtp_password:
            logging.error("SMTP credentials not configured. Email sending is disabled.")
            return False
        
        # Create a multipart message
        msg = MIMEMultipart()
        msg["From"] = smtp_username
        msg["To"] = recipient
        msg["Subject"] = subject
        
        # Add body to email
        msg.attach(MIMEText(body, "plain"))
        
        # Add attachment if provided
        if attachment and attachment_name:
            attachment_part = MIMEApplication(attachment)
            attachment_part.add_header(
                "Content-Disposition", 
                f"attachment; filename={attachment_name}"
            )
            msg.attach(attachment_part)
        
        # Connect to server and send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        
        logging.info(f"Email sent successfully to {recipient}")
        return True
        
    except Exception as e:
        logging.error(f"Error sending email: {str(e)}")
        return False


def send_slack(channel, message, file_content=None, file_name=None):
    """
    Send a message to a Slack channel with optional file attachment.
    
    Parameters:
    - channel: Slack channel name (e.g., "#grants")
    - message: Text message to send
    - file_content: String content of the file to attach (optional)
    - file_name: Name of the file to attach (optional)
    
    Returns:
    - Boolean indicating success or failure
    """
    try:
        # Get Slack token from environment variables
        slack_token = os.getenv("SLACK_TOKEN", "")
        
        # If token is missing, log an error and return
        if not slack_token:
            logging.error("Slack token not configured. Slack sending is disabled.")
            return False
        
        # Send message
        headers = {
            "Authorization": f"Bearer {slack_token}"
        }
        
        # First, post the message
        message_data = {
            "channel": channel,
            "text": message
        }
        
        message_response = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers=headers,
            json=message_data
        )
        
        if not message_response.json().get("ok", False):
            logging.error(f"Error sending Slack message: {message_response.text}")
            return False
        
        # If file content is provided, upload it
        if file_content and file_name:
            files = {
                "file": (file_name, file_content, "text/csv"),
                "channels": (None, channel),
                "initial_comment": (None, "Here's the grant data you requested.")
            }
            
            file_response = requests.post(
                "https://slack.com/api/files.upload",
                headers={"Authorization": f"Bearer {slack_token}"},
                files=files
            )
            
            if not file_response.json().get("ok", False):
                logging.error(f"Error uploading file to Slack: {file_response.text}")
                return False
        
        logging.info(f"Slack message sent successfully to {channel}")
        return True
        
    except Exception as e:
        logging.error(f"Error sending Slack message: {str(e)}")
        return False
