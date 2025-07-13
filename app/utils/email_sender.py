import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import Dict, Any

logger = logging.getLogger(__name__)


def send_pdn_code_email(user_answers: Dict[str, Any], pdn_code: str) -> bool:
    """
    Send comprehensive PDN report via email to the user.
    
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

        # Get user name from answers
        first_name = user_answers.get('metadata', {}).get('first_name', '')
        last_name = user_answers.get('metadata', {}).get('last_name', '')

        # Create message
        msg = MIMEMultipart()
        msg['From'] = 'tomergur@gmail.com'
        msg['To'] = user_email
        msg['Subject'] = f'ברוך הבא למסע – קוד המקור שלך מחכה להתגלות'

        # Create HTML content with modern PDN design
        html_content = f"""
        <!DOCTYPE html>
        <html dir="rtl" lang="he">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>מפת הדרכים האישית שלך - {pdn_code}</title>
            <link href="https://fonts.googleapis.com/css2?family=Rubik:wght@300;400;500;600;700&display=swap" rel="stylesheet">
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                /* Hebrew text support */
                html {{
                    direction: rtl;
                    unicode-bidi: bidi-override;
                }}
                
                body {{
                    font-family: 'Rubik', 'Segoe UI', Arial, sans-serif;
                    line-height: 1.6;
                    color: #1f2937;
                    background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 25%, #c084fc 50%, #d946ef 75%, #ec4899 100%);
                    min-height: 100vh;
                    direction: rtl;
                    text-align: right;
                    unicode-bidi: bidi-override;
                    position: relative;
                    overflow-x: hidden;
                }}
                
                body::before {{
                    content: '';
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: 
                        radial-gradient(circle at 20% 80%, rgba(139, 92, 246, 0.3) 0%, transparent 50%),
                        radial-gradient(circle at 80% 20%, rgba(168, 85, 247, 0.3) 0%, transparent 50%),
                        radial-gradient(circle at 40% 40%, rgba(192, 132, 252, 0.2) 0%, transparent 50%);
                    pointer-events: none;
                    z-index: -1;
                }}
                
                .email-container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: rgba(255, 255, 255, 0.95);
                    backdrop-filter: blur(30px);
                    border-radius: 32px;
                    box-shadow: 
                        0 25px 50px rgba(139, 92, 246, 0.3),
                        0 0 0 1px rgba(255, 255, 255, 0.1),
                        inset 0 1px 0 rgba(255, 255, 255, 0.2);
                    overflow: hidden;
                    position: relative;
                    border: 2px solid rgba(139, 92, 246, 0.2);
                }}
                
                .email-container::before {{
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
                    pointer-events: none;
                }}
                
                .header {{
                    background: linear-gradient(135deg, #7c3aed 0%, #8b5cf6 25%, #a855f7 50%, #c084fc 75%, #d946ef 100%);
                    color: white;
                    padding: 50px 30px;
                    text-align: center;
                    position: relative;
                    overflow: hidden;
                    border-bottom: 3px solid rgba(255, 255, 255, 0.2);
                }}
                
                .header::before {{
                    content: '';
                    position: absolute;
                    top: -50%;
                    left: -50%;
                    width: 200%;
                    height: 200%;
                    background: 
                        radial-gradient(circle, rgba(255,255,255,0.15) 0%, transparent 50%),
                        radial-gradient(circle, rgba(192, 132, 252, 0.1) 0%, transparent 60%);
                    animation: float 8s ease-in-out infinite;
                    filter: blur(1px);
                }}
                
                @keyframes float {{
                    0%, 100% {{ transform: translateY(0px) rotate(0deg); }}
                    50% {{ transform: translateY(-20px) rotate(5deg); }}
                }}
                
                .header h1 {{
                    font-size: 32px;
                    font-weight: 800;
                    margin-bottom: 12px;
                    position: relative;
                    z-index: 1;
                    text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
                    background: linear-gradient(45deg, #ffffff, #f3e8ff);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                }}
                
                .header h2 {{
                    font-size: 18px;
                    font-weight: 400;
                    opacity: 0.9;
                    position: relative;
                    z-index: 1;
                }}
                
                .content {{
                    padding: 40px 30px;
                    position: relative;
                    z-index: 1;
                }}
                
                .greeting {{
                    font-size: 28px;
                    font-weight: 700;
                    color: #1f2937;
                    margin-bottom: 32px;
                    text-align: right;
                    direction: rtl;
                    unicode-bidi: bidi-override;
                    line-height: 1.4;
                }}
                
                .message-box {{
                    background: linear-gradient(135deg, rgba(139, 92, 246, 0.08) 0%, rgba(168, 85, 247, 0.05) 50%, rgba(192, 132, 252, 0.03) 100%);
                    border: 2px solid rgba(139, 92, 246, 0.15);
                    border-radius: 20px;
                    padding: 28px;
                    margin: 28px 0;
                    position: relative;
                    overflow: hidden;
                    box-shadow: 
                        0 8px 32px rgba(139, 92, 246, 0.1),
                        inset 0 1px 0 rgba(255, 255, 255, 0.2);
                }}
                
                .message-box::before {{
                    content: '';
                    position: absolute;
                    top: 0;
                    left: -100%;
                    width: 100%;
                    height: 100%;
                    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
                    animation: shimmer 4s infinite;
                }}
                
                @keyframes shimmer {{
                    0% {{ left: -100%; }}
                    100% {{ left: 100%; }}
                }}
                
                .message-text {{
                    font-size: 20px;
                    line-height: 1.8;
                    color: #1f2937;
                    margin-bottom: 20px;
                    position: relative;
                    z-index: 1;
                    text-align: right;
                    direction: rtl;
                    unicode-bidi: bidi-override;
                    font-weight: 400;
                }}
                
                .pdn-code-section {{
                    background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(168, 85, 247, 0.08) 50%, rgba(192, 132, 252, 0.05) 100%);
                    border: 3px solid transparent;
                    background-clip: padding-box;
                    border-radius: 24px;
                    padding: 32px;
                    margin: 32px 0;
                    text-align: center;
                    position: relative;
                    box-shadow: 
                        0 12px 40px rgba(139, 92, 246, 0.2),
                        inset 0 1px 0 rgba(255, 255, 255, 0.3);
                }}
                
                .pdn-code-section::before {{
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: linear-gradient(135deg, #7c3aed, #8b5cf6, #a855f7, #c084fc);
                    border-radius: inherit;
                    margin: -3px;
                    z-index: -1;
                    animation: gradientShift 4s ease-in-out infinite;
                }}
                
                @keyframes gradientShift {{
                    0%, 100% {{ background-position: 0% 50%; }}
                    50% {{ background-position: 100% 50%; }}
                }}
                
                .pdn-code-label {{
                    font-size: 18px;
                    font-weight: 600;
                    color: #4b5563;
                    margin-bottom: 12px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    direction: rtl;
                    unicode-bidi: bidi-override;
                }}
                
                .pdn-code {{
                    font-size: 56px;
                    font-weight: 900;
                    background: linear-gradient(135deg, #7c3aed, #8b5cf6, #a855f7, #c084fc, #d946ef);
                    background-size: 300% 300%;
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                    margin: 16px 0;
                    direction: ltr;
                    unicode-bidi: bidi-override;
                    animation: gradientFlow 3s ease-in-out infinite;
                    text-shadow: 0 4px 20px rgba(139, 92, 246, 0.3);
                }}
                
                @keyframes gradientFlow {{
                    0%, 100% {{ background-position: 0% 50%; }}
                    50% {{ background-position: 100% 50%; }}
                }}
                
                .cta-section {{
                    background: linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(168, 85, 247, 0.1) 50%, rgba(192, 132, 252, 0.08) 100%);
                    border: 3px solid transparent;
                    background-clip: padding-box;
                    border-radius: 24px;
                    padding: 32px;
                    margin: 32px 0;
                    text-align: center;
                    position: relative;
                    box-shadow: 
                        0 15px 45px rgba(139, 92, 246, 0.25),
                        inset 0 1px 0 rgba(255, 255, 255, 0.3);
                }}
                
                .cta-section::before {{
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: linear-gradient(135deg, #7c3aed, #8b5cf6, #a855f7, #c084fc);
                    border-radius: inherit;
                    margin: -3px;
                    z-index: -1;
                    animation: gradientShift 4s ease-in-out infinite;
                }}
                
                .cta-button {{
                    display: inline-block;
                    background: linear-gradient(135deg, #7c3aed 0%, #8b5cf6 25%, #a855f7 50%, #c084fc 75%, #d946ef 100%);
                    color: white;
                    text-decoration: none;
                    padding: 24px 48px;
                    border-radius: 16px;
                    font-weight: 700;
                    font-size: 22px;
                    margin: 24px 0;
                    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                    box-shadow: 
                        0 8px 25px rgba(139, 92, 246, 0.4),
                        0 4px 10px rgba(139, 92, 246, 0.2);
                    direction: rtl;
                    unicode-bidi: bidi-override;
                    position: relative;
                    overflow: hidden;
                }}
                
                .cta-button::before {{
                    content: '';
                    position: absolute;
                    top: 0;
                    left: -100%;
                    width: 100%;
                    height: 100%;
                    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
                    transition: left 0.5s;
                }}
                
                .cta-button:hover::before {{
                    left: 100%;
                }}
                
                .cta-button:hover {{
                    transform: translateY(-4px) scale(1.05);
                    box-shadow: 
                        0 15px 35px rgba(139, 92, 246, 0.5),
                        0 8px 15px rgba(139, 92, 246, 0.3);
                    background: linear-gradient(135deg, #6d28d9 0%, #7c3aed 25%, #8b5cf6 50%, #a855f7 75%, #c084fc 100%);
                }}
                
                .footer {{
                    background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
                    padding: 30px;
                    text-align: center;
                    border-top: 1px solid rgba(139, 92, 246, 0.1);
                }}
                
                .footer-text {{
                    font-size: 16px;
                    color: #4b5563;
                    margin-bottom: 16px;
                }}
                
                .footer-signature {{
                    font-size: 20px;
                    font-weight: 700;
                    color: #1f2937;
                    margin-bottom: 12px;
                    direction: rtl;
                    unicode-bidi: bidi-override;
                }}
                
                .footer-tagline {{
                    font-size: 16px;
                    color: #6b7280;
                    font-style: italic;
                    direction: rtl;
                    unicode-bidi: bidi-override;
                }}
                
                .heart-emoji {{
                    font-size: 32px;
                    margin: 0 12px;
                    filter: drop-shadow(0 4px 12px rgba(139, 92, 246, 0.5));
                    animation: heartPulse 2s ease-in-out infinite;
                    background: linear-gradient(45deg, #8b5cf6, #a855f7, #c084fc, #d946ef);
                    background-size: 300% 300%;
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                }}
                
                @keyframes heartPulse {{
                    0%, 100% {{ transform: scale(1); filter: drop-shadow(0 4px 12px rgba(139, 92, 246, 0.5)); }}
                    50% {{ transform: scale(1.2); filter: drop-shadow(0 6px 20px rgba(139, 92, 246, 0.8)); }}
                }}
                
                @media (max-width: 600px) {{
                    .email-container {{
                        margin: 10px;
                        border-radius: 16px;
                    }}
                    
                    .header {{
                        padding: 30px 20px;
                    }}
                    
                    .header h1 {{
                        font-size: 28px;
                    }}
                    
                    .content {{
                        padding: 30px 20px;
                    }}
                    
                    .pdn-code {{
                        font-size: 36px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <h1>מפת הדרכים האישית שלך</h1>
                    <h2>קוד המקור" - הנווט הראשי שלך להצלחה"</h2>
                </div>
                
                <div class="content">
                    <div class="greeting">
                       ברוך הבא למסע שלך
זהו הרגע שבו הקוד שלך מתחיל להתגלות 
                    </div>
                    
                    <div class="message-box">
                        <p class="message-text">
                            בשמחה ובהתרגשות, אנו משתפים אותך בתוצאה של תהליך ההקשבה והעיבוד שעבר האבחון שביצעת.
                        </p>
                        <p class="message-text">
                            לאחר ניתוח מעמיק של הנתונים – יצרנו עבורך את מפת הדרכים האישית שלך: מבט ממוקד ואותנטי על הכוחות שמניעים אותך, על החיבורים שבין רגש, משמעות ופעולה, ועל הכיוון שבו הנשמה שלך מבקשת לצעוד.
                        </p>
                    </div>
                    
                    <div class="pdn-code-section">
                        <div class="pdn-code-label">קוד PDN שלך</div>
                        <div class="pdn-code">{pdn_code}</div>
                        <div class="pdn-code-label">הצופן האישי שלך</div>
                    </div>
                    
                    <div class="message-box">
                        <p class="message-text">
                            מצורפת מפת הדרכים האישית המלאה עם כל הפרטים וההמלצות המותאמות במיוחד עבורך.
                        </p>
                        <p class="message-text">
                            הקורס הבא הותאם עבורך בהתאם לשלב שלך לפי קוד המקור       
                 </p>
                    </div>
                    
                    <div class="cta-section">
                        <a href="https://www.pdn.co.il" class="cta-button">
                                רגע האמת הגיע – קורס המנוע הראשי שלך נפתח
                        </a>
                    </div>
                    
                    <div class="message-box">
                        <p class="message-text">
                        כי בתוך כל אחד ואחת מאיתנו טמון צופן ייחודי – שמחכה להתגלות, ולכוון את החיים בדיוק אל המקום שבו הלב מהדהד, והצליל הפנימי מתחיל סוף־סוף להתנגן. זה הזמן ולהתחיל לנגן את המנגינה שלך לעולם.
                        </p>
                    </div>
                </div>
                
                <div class="footer">
                    <div class="footer-signature"קוד המקור</div>
                    <div class="footer-text">PDN Team – Your Personal Source Code</div>
                    <div class="footer-tagline">הצופן האישי שלך</div>
                </div>
            </div>
        </body>
        </html>
        """

        # Attach HTML version only
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))

        # Attach PDF if available
        # Try different filename formats for the PDF
        pdf_filenames = [
            f"{pdn_code}.pdf",  # P10.pdf
            f"P-{pdn_code[1:]}.pdf",  # P-10.pdf (if pdn_code is P10)
            f"{pdn_code.replace('P', 'P-')}.pdf",  # P-10.pdf (alternative)
            f"{pdn_code.lower()}.pdf"  # p10.pdf
        ]
        
        pdf_attached = False
        for pdf_filename in pdf_filenames:
            pdf_path = os.path.join("app", "static", "reports", pdf_filename)
            
            if os.path.exists(pdf_path):
                try:
                    with open(pdf_path, "rb") as file:
                        attach = MIMEApplication(file.read(), _subtype="pdf")
                        attach.add_header('Content-Disposition', 'attachment', filename=f"{pdn_code.lower()}.pdf")
                        msg.attach(attach)
                    logger.info(f"PDF attachment added: {pdf_filename}")
                    pdf_attached = True
                    break
                except Exception as e:
                    logger.error(f"Error reading PDF file {pdf_path}: {e}")
                    continue
        
        if not pdf_attached:
            logger.warning(f"PDF not found for code: {pdn_code}. Tried paths: {[os.path.join('app', 'static', 'reports', f) for f in pdf_filenames]}")

        # Send email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login('tomergur@gmail.com', 'jlzd ytwd dpat hcsi')
            server.send_message(msg)

        logger.info(f"Successfully sent PDN report to {user_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False