import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any

logger = logging.getLogger(__name__)


def send_email(user_answers: Dict[str, Any], pdn_code: str, report_data: Dict[str, Any]) -> bool:
    """
    Send PDN report via email to the user.
    
    Args:
        user_answers (Dict): User's questionnaire answers and metadata
        pdn_code (str): Calculated PDN code
        report_data (Dict): Report data to be included in the email
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Get user email from answers
        user_email = user_answers.get('metadata', {}).get('email')
        if not user_email:
            logger.error("No email address found in user answers")
            return False

        # Create message
        msg = MIMEMultipart()
        msg['From'] = 'tomergur@gmail.com'
        msg['To'] = user_email  # , 'center@pdn.co.il'
        msg['Subject'] = f'Your PDN Analysis Report - {pdn_code}'

        # Create email body
        body = f"""
        Dear {user_answers.get('metadata', {}).get('first_name', '')} {user_answers.get('metadata', {}).get('last_name', '')},

        Thank you for completing the PDN assessment. Here is your PDN code and analysis:

        Your PDN Code: {pdn_code}

        For a detailed analysis of your results, please visit our website.

        Best regards,
        PDN Team
        https://www.pdn.co.il
        """

        # Convert report data to HTML string
        html_content = f"""
        <html>
        <body>
            <h1>PDN Analysis Report</h1>
            <h2>Your PDN Code: {pdn_code}</h2>
            <div>
                <h3>Results:</h3>
                <p>Trait: {report_data.get('trait', 'N/A')}</p>
                <p>Energy: {report_data.get('energy', 'N/A')}</p>
                <p>Explanation: {report_data.get('explanation', 'N/A')}</p>
            </div>
        </body>
        </html>
        """

        # Attach both plain text and HTML versions
        msg.attach(MIMEText(body, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))

        # Send email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login('tomergur@gmail.com', 'jlzd ytwd dpat hcsi')  # Update with your credentials
            server.send_message(msg)

        logger.info(f"Successfully sent PDN report to {user_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False
