import os
import smtplib
from email.message import EmailMessage

def send_booking_email(user_booking, provider_email):
    """
    Sends an email to the clinic/provider with the user's booking details.
    Parameters:
    - user_booking (dict): {
        "name": str,
        "email": str,
        "phone": str,
        "date": str,
        "time": str,
        "notes": str
      }
    - provider_email (str): The email address of the clinic/provider
    Returns:
    - str: Success or error message
    """
    EMAIL_SENDER = "praveenpandey5232@gmail.com"
    EMAIL_PASSWORD = "qlbbanhyvhkztytj"
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        return "❌ Email sender credentials not set in environment variables."
    # Compose the email
    msg = EmailMessage()
    msg['Subject'] = f"📅 Appointment Booking Request from {user_booking['name']}"
    msg['From'] = EMAIL_SENDER
    msg['To'] = provider_email
    msg.set_content(f"""
Hello,

You have a new booking request from a user:

👤 Name: {user_booking['name']}
📧 Email: {user_booking['email']}
📞 Phone: {user_booking['phone']}
📅 Date: {user_booking['date']}
⏰ Time: {user_booking['time']}
📝 Notes: {user_booking['notes']}

Please confirm the appointment by replying or contacting the user directly.

Thank you,
Your Booking System
""")
    # Send the email
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
        return f"✅ Email sent to provider: {provider_email}"
    except smtplib.SMTPAuthenticationError as e:
        return f"❌ Auth Error - Check App Password: {e}"
    except Exception as e:
        return f"❌ Failed to send email: {e}" 