import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailService:
    def __init__(self):
        self.smtp_server = st.secrets["EMAIL_HOST"]
        self.smtp_port = int(st.secrets["EMAIL_PORT"])
        self.sender_email = st.secrets["EMAIL_USERNAME"]
        self.password = st.secrets["EMAIL_PASSWORD"]

    def send_confirmation_email(self, booking_details, recipient_email):
        try:
            # Create message
            message = MIMEMultipart()
            message["From"] = self.sender_email
            message["To"] = recipient_email
            message["Subject"] = f"TixBee Booking Confirmation - {booking_details['booking_id']}"

            # Email body
            body = f"""
            Dear {booking_details['customer_name']},

            Thank you for booking with TixBee! Here are your booking details:

            Booking ID: {booking_details['booking_id']}
            Attraction: {booking_details['attraction']}
            Visit Date: {booking_details['visit_date']}
            Tickets: {booking_details['ticket_count']}
            Amount Paid: ₹{booking_details['amount']}

            Please show this email at the entrance.

            Have a great time!
            Team TixBee
            """

            message.attach(MIMEText(body, "plain"))

            # Connect to SMTP server
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.password)
                server.send_message(message)

            return True, "Email sent successfully!"

        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False, str(e)