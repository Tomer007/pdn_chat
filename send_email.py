#!/usr/bin/env python3
"""
Simple script to send email using Gmail API
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def send_email():
    # Email configuration
    sender_email = "tomergur@gmail.com"  # You'll need to use an app password
    receiver_email = "tomergur@gmail.com"
    
    # Email content
    subject = "PDN Chat - New Version Release Notes"
    
    body = """
Hi Tomer,

I'm pleased to announce the release of a new version of the PDN Chat application with significant improvements to the export functionality and user interface.

## 🚀 New Version Release Notes

### Key Improvements:

**1. Simplified Export Functionality**
- Removed complex PDF export option
- Implemented reliable text-only export
- Streamlined export process with single-click functionality
- Better error handling and user feedback

**2. Enhanced UI/UX During Message Processing**
- All interactive elements are now disabled during message processing
- Visual feedback with loading states and disabled styling
- Prevents multiple message submissions and button clicks during processing
- Clear error messages when users try to interact during processing

**3. Code Quality Improvements**
- Cleaned up unused PDF-related code and dependencies
- Simplified JavaScript functions for better maintainability
- Improved error handling with fallback mechanisms
- Better code organization and documentation

### Technical Details:

**Files Modified:**
- app/pdn_chat_ai/templates/chat.html - Main chat interface with export and UI improvements

**Key Features:**
- ✅ Reliable text file export with Hebrew UTF-8 encoding
- ✅ Complete UI state management during processing
- ✅ Simplified user experience
- ✅ Better error handling and user feedback
- ✅ Clean, maintainable codebase

### How to Use:

1. **Export Chat**: Click the "ייצא" (Export) button to download conversation as text file
2. **Send Messages**: All UI elements properly disable during processing
3. **Voice Recording**: Disabled during message processing to prevent conflicts

The application is now more stable and user-friendly, with a focus on reliability and simplicity.

Best regards,
AI Assistant

---
*This email was automatically generated regarding the PDN Chat application updates.*
"""

    # Create message
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    
    # Add body to email
    message.attach(MIMEText(body, "plain"))
    
    # Gmail SMTP configuration
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    
    print("To send this email, you need to:")
    print("1. Enable 2-factor authentication on your Gmail account")
    print("2. Generate an App Password for this application")
    print("3. Replace 'YOUR_APP_PASSWORD' below with your actual app password")
    print("\nEmail content:")
    print("=" * 50)
    print(f"To: {receiver_email}")
    print(f"Subject: {subject}")
    print("=" * 50)
    print(body)
    print("=" * 50)
    
    # Uncomment and modify the following lines to actually send the email
    # You'll need to replace 'YOUR_APP_PASSWORD' with your Gmail app password
    
    # try:
    #     # Create SMTP session
    #     server = smtplib.SMTP(smtp_server, smtp_port)
    #     server.starttls()  # Enable security
    #     server.login(sender_email, "YOUR_APP_PASSWORD")  # Replace with your app password
    #     
    #     # Send email
    #     text = message.as_string()
    #     server.sendmail(sender_email, receiver_email, text)
    #     server.quit()
    #     
    #     print("Email sent successfully!")
    #     
    # except Exception as e:
    #     print(f"Error sending email: {e}")

if __name__ == "__main__":
    send_email()

