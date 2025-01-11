def send_booking_confirmation(user_email, booking_details):
    """
    Format and send booking confirmation email
    """
    try:
        subject = f"TixBee Booking Confirmation - {booking_details.get('booking_id', 'Unknown')}"
        
        # Create email body
        body = f"""
        Dear {booking_details.get('name', 'Customer')},

        Thank you for booking with TixBee! Here are your booking details:

        🎫 Booking ID: {booking_details.get('booking_id', 'Unknown')}
        🏰 Attraction: {booking_details.get('attraction', 'Unknown')}
        📅 Visit Date: {booking_details.get('visit_date', 'Unknown')}
        🎟️ Tickets: {booking_details.get('ticket_count', 'Unknown')}
        💰 Amount Paid: ₹{booking_details.get('amount', '0')}

        Please show this email at the entrance.

        Have a great time!
        Team TixBee
        """
        
        return subject, body

    except Exception as e:
        print(f"Error in email template: {str(e)}")
        return None, None 