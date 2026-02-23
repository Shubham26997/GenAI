import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

try:
    from premailer import transform as css_inline
    PREMAILER_AVAILABLE = True
except ImportError:
    PREMAILER_AVAILABLE = False

def _inline_css(html_content):
    """Convert <style> block CSS to inline styles for Gmail compatibility."""
    if PREMAILER_AVAILABLE:
        try:
            return css_inline(
                html_content,
                remove_classes=False,
                strip_important=False,
                cssutils_logging_level=None,
            )
        except Exception as e:
            print(f"⚠️  CSS inlining failed ({e}), sending as-is.")
    else:
        print("⚠️  premailer not installed — CSS may not render in Gmail. Run: pip install premailer")
    return html_content

def send_newsletter_email(html_content, recipient_emails):
    """Sends the HTML newsletter via SMTP to one or multiple recipients."""
    # Inline CSS so Gmail (which strips <style> blocks) renders styles correctly
    html_content = _inline_css(html_content)

    # SMTP Configuration
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    sender_email = os.getenv("SENDER_EMAIL", "ainotifiy@gmail.com")
    sender_password = os.getenv("SENDER_PASSWORD", "qbbf ixwz bshe koor")
    
    if not sender_email or not sender_password:
        print("❌ SENDER_EMAIL or SENDER_PASSWORD not set in environment.")
        return False

    # Handle single recipient string or comma-separated string by converting to list
    if isinstance(recipient_emails, str):
        recipients = [r.strip() for r in recipient_emails.split(",") if r.strip()]
    else:
        recipients = recipient_emails

    if not recipients:
        print("⚠️ No recipients provided.")
        return False

    success_count = 0
    try:
        # Connect once
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        
        for email in recipients:
            try:
                # Create Unique Message for each recipient
                msg = MIMEMultipart()
                msg['From'] = f"AI News Brief <{sender_email}>"
                msg['To'] = email
                msg['Subject'] = "🚀 AI & Tech News Brief - Your Latest Digest"
                msg.attach(MIMEText(html_content, 'html'))
                
                server.send_message(msg)
                print(f"📧 Newsletter sent successfully to {email}")
                success_count += 1
            except Exception as e:
                print(f"❌ Failed to send to {email}: {e}")
        
        server.quit()
        return success_count == len(recipients)
    except Exception as e:
        print(f"❌ SMTP Connection Error: {e}")
        return False
