from datetime import datetime, timedelta
from email.message import EmailMessage
from random import randint

import aiosmtplib
from fastapi import Form, HTTPException


otp_store = {}

# Email configuration
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587  
EMAIL_USER = "edusync521@gmail.com"  
EMAIL_PASSWORD = "zazi wgrw ofir bmbd" 

def generate_otp():
    """Generate a 6-digit OTP."""
    return str(randint(100000, 999999))

@app.get("/send-otp/")
async def send_otp(email: str = Form(None)):
    """Send OTP to the provided email address."""
    otp = generate_otp()
    email="arbitbhandari17@gmail.com"
    expiry_time = datetime.utcnow() + timedelta(minutes=5) 
    otp_store[email] = {"otp": otp, "expires_at": expiry_time}

    # Create the email message
    try:
        message = EmailMessage()
        message.set_content(f"Your OTP is: {otp}. It is valid for 5 minutes.")
        message["Subject"] = "Your OTP"
        message["From"] = EMAIL_USER
        message["To"] = email

        # Connect to the SMTP server with STARTTLS on port 587
        smtp_client = aiosmtplib.SMTP(hostname=EMAIL_HOST, port=EMAIL_PORT)
        await smtp_client.connect()

        # Login to the SMTP server
        await smtp_client.login(EMAIL_USER, EMAIL_PASSWORD)

        # Send the email
        await smtp_client.send_message(message)

        # Close the connection
        await smtp_client.quit()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send OTP: {str(e)}")

    return {"message": "OTP sent successfully"}
