import streamlit as st
import google.generativeai as genai
import json
from datetime import datetime, timedelta
import calendar
import random
import qrcode
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from urllib.parse import quote
import re
import base64
import time
from email_template import send_booking_confirmation
from email_service import EmailService
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables

# Page configuration
st.set_page_config(
    page_title="TixBee - Your Ticket Booking Assistant",
    page_icon="🎫",
    layout="centered"
)

def get_upi_qr(amount, upi_id="arupiop@axl", name="TixBee", user_email=None, booking_details=None):
    try:
        print(f"Received booking details: {booking_details}")
        print(f"User email: {user_email}")
        
        if user_email and booking_details:
            print(f"Preparing email with name: {booking_details.get('name', 'Not found')}")
            email_booking_details = {
                'booking_id': 'TIX' + datetime.now().strftime('%Y%m%d%H%M%S'),
                'customer_name': booking_details['name'],
                'attraction': booking_details['attraction'],
                'visit_date': booking_details['visit_date'],
                'ticket_count': booking_details['ticket_count'],
                'amount': amount
            }
            print(f"Email details prepared: {email_booking_details}")
        
        # Keep UPI string simple
        upi_string = f"upi://pay?pa={upi_id}&pn={name}&am={amount}&cu=INR"
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=0,
        )
        qr.add_data(upi_string)
        qr.make(fit=True)
        qr_image = qr.make_image(fill_color="black", back_color="white")

        # Create a white background image with reduced height
        width = 400
        height = 480  # Reduced height
        background = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(background)

        try:
            title_font = ImageFont.truetype("arial.ttf", 32)
            text_font = ImageFont.truetype("arial.ttf", 16)
            upi_font = ImageFont.truetype("arial.ttf", 18)
        except:
            title_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
            upi_font = ImageFont.load_default()

        # Add TIXBEE title with less top padding
        title = "TIXBEE"
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        draw.text(((width - title_width) // 2, 20), title, font=title_font, fill='#333333')  # Reduced top padding

        # Add QR code with adjusted position
        qr_size = 220
        qr_image = qr_image.resize((qr_size, qr_size))
        qr_pos = ((width - qr_size) // 2, 70)  # Adjusted position
        background.paste(qr_image, qr_pos)

        # Add UPI ID with adjusted position
        upi_text = upi_id
        upi_bbox = draw.textbbox((0, 0), upi_text, font=upi_font)
        upi_width = upi_bbox[2] - upi_bbox[0]
        draw.text(((width - upi_width) // 2, 300), upi_text, font=upi_font, fill='#666666')  # Adjusted position

        # Add scan instruction with adjusted position
        instruction = "Scan and pay with any BHIM UPI app"
        inst_bbox = draw.textbbox((0, 0), instruction, font=text_font)
        inst_width = inst_bbox[2] - inst_bbox[0]
        draw.text(((width - inst_width) // 2, 330), instruction, font=text_font, fill='#333333')  # Adjusted position

        # Add payment logos with increased size
        logo_y = 380  # Adjusted position
        logo_size = (65, 65)  # Increased logo size
        logos = ['bhim.png', 'gpay.png', 'phonepe.png', 'paytm.png', 'amazon.png']
        total_logos_width = len(logos) * logo_size[0] + (len(logos) - 1) * 15
        current_x = (width - total_logos_width) // 2

        for logo_file in logos:
            try:
                logo = Image.open(f'assets/{logo_file}')
                logo = logo.convert('RGBA')
                logo.thumbnail(logo_size, Image.Resampling.LANCZOS)
                logo_pos_x = current_x
                logo_pos_y = logo_y + (logo_size[1] - logo.size[1]) // 2
                background.paste(logo, (logo_pos_x, logo_pos_y), logo if logo.mode == 'RGBA' else None)
                current_x += logo_size[0] + 15
            except Exception as e:
                print(f"Error loading logo {logo_file}: {e}")

        # Add subtle border
        border_color = '#EEEEEE'
        draw.rectangle([0, 0, width-1, height-1], outline=border_color, width=1)

        # Convert to bytes
        img_byte_arr = BytesIO()
        background.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        # Display in Streamlit with custom CSS and fixed container width
        st.markdown("""
            <style>
                .stImage {
                    background-color: white;
                    padding: 20px;
                    border-radius: 15px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }
            </style>
        """, unsafe_allow_html=True)
        
        # Using use_container_width instead of use_column_width
        st.image(img_byte_arr, use_container_width=False, width=400)

        # Add timer and confirmation message
        timer_placeholder = st.empty()
        email_placeholder = st.empty()
        final_message_placeholder = st.empty()
        
        # Initialize email service
        email_service = EmailService()
        
        for secs in range(10, -1, -1):
            if secs > 0:
                timer_placeholder.markdown(f"""
                    <div style="text-align: center; padding: 10px; color: #666;">
                        Payment window closes in {secs} seconds...
                    </div>
                """, unsafe_allow_html=True)
                time.sleep(1)
            else:
                # Clear the timer
                timer_placeholder.empty()
                
                if user_email and booking_details:
                    # Prepare complete booking details with user's name from chat
                    email_booking_details = {
                        'booking_id': 'TIX' + datetime.now().strftime('%Y%m%d%H%M%S'),
                        'customer_name': booking_details['name'],  # This comes from chat input
                        'attraction': booking_details['attraction'],
                        'visit_date': booking_details['visit_date'],
                        'ticket_count': booking_details['ticket_count'],
                        'amount': amount
                    }
                    
                    # Send confirmation email with user's name
                    success, message = email_service.send_confirmation_email(
                        email_booking_details,
                        user_email
                    )
                    
                    # Show email status
                    with email_placeholder.container():
                        if success:
                            col1, col2 = st.columns([1, 20])
                            with col1:
                                st.markdown("✅")
                            with col2:
                                st.success("Email Sent Successfully!")
                            
                            st.info("""
                                We've sent your payment confirmation and booking details to your registered email address.
                                Please check your inbox (and spam folder) for the confirmation email.
                            """)
                        else:
                            st.error(f"Failed to send email: {message}")
                
                # Show final thank you message
                final_message_placeholder.markdown("Thanks for choosing TixBee! We look forward to serving you soon! 🎫")
                break

        return None

    except Exception as e:
        print(f"Error generating QR code: {e}")
        return None

def extract_amount(text):
    match = re.search(r'Total Amount: ₹(\d+)', text)
    if match:
        return match.group(1)
    return "0"

def start_booking():
    """Initialize the booking process"""
    try:
        if st.session_state['user_name']:
            print(f"Found user name in session: {st.session_state['user_name']}")
            return True
            
        if st.session_state['messages']:
            last_message = st.session_state['messages'][-1]
            if last_message['role'] == 'user':
                st.session_state['user_name'] = last_message['content']
                print(f"Stored user name in session: {last_message['content']}")
                return True
        return False
        
    except Exception as e:
        print(f"Error in start_booking: {str(e)}")
        return False

def extract_booking_details(response_text):
    """Extract booking details from chat response"""
    try:
        # Extract email
        email_match = re.search(r'📧 Contact Email: (.+?)\n', response_text)
        user_email = email_match.group(1).strip() if email_match else None

        # Get name directly from session state
        user_name = st.session_state.get('user_name', 'User')
        print(f"Retrieved user name from session: {user_name}")  # Debug print

        return {
            'user_email': user_email,
            'booking_details': {
                'name': user_name,  # Use the stored name
                'attraction': re.search(r'🏰 Attraction: (.+?)\n', response_text).group(1).strip(),
                'visit_date': re.search(r'📅 Visit Date: (.+?)\n', response_text).group(1).strip(),
                'ticket_count': re.search(r'🎟️ Tickets Booked:(.*?)💰', response_text, re.DOTALL).group(1).strip(),
            },
            'amount': re.search(r'Total Amount: ₹(\d+)', response_text).group(1)
        }
    except Exception as e:
        print(f"Error extracting details: {str(e)}")
        return None

# Initialize all session states at the very beginning
if 'current_state' not in st.session_state:
    st.session_state['current_state'] = 'START'
if 'user_email' not in st.session_state:
    st.session_state['user_email'] = None
if 'user_name' not in st.session_state:
    st.session_state['user_name'] = None
if 'booking_details' not in st.session_state:
    st.session_state['booking_details'] = {}
if 'greeted' not in st.session_state:
    st.session_state['greeted'] = False
if 'messages' not in st.session_state:
    st.session_state['messages'] = []
if 'conversation_history' not in st.session_state:
    st.session_state['conversation_history'] = []
if 'payment_completed' not in st.session_state:
    st.session_state['payment_completed'] = False

# Configure the API and model
api_key = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

# Initialize chat if not in session state
if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])

# Get current date information
current_date = datetime.now()
current_day = current_date.strftime("%A")
current_date_str = current_date.strftime("%Y-%m-%d")

# Initial prompt with conversation flow
initial_prompt = f"""You are TixBee, a friendly ticket booking assistant. You are aware that today is {current_day}, {current_date_str}. Follow this conversation flow STRICTLY in order:

1. First, just greet and ask for the user's name
2. Then ask which city they would like to visit
3. If they mention any city other than Bengaluru, respond: "I wish I could help you explore [city name]! Right now, I can only book tickets in Bengaluru, but we're working on adding more cities soon. Would you like to discover some amazing places in Bengaluru instead?"
4. Once they agree to Bengaluru, show them these options in this exact format:

Here are the amazing places you can visit in Bengaluru:

a) Bangalore Palace
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   A magnificent palace with Tudor-style architecture,
   featuring beautiful gardens and royal interiors.

b) Lalbagh Botanical Garden
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   A beautiful garden spanning 240 acres with rare plants,
   a glasshouse, and a serene lake.

c) Visvesvaraya Technological Museum
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   An interactive science and technology museum with
   engaging exhibits and hands-on demonstrations.

d) Bannerghatta National Park
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   A wildlife sanctuary offering exciting safari experiences
   and a chance to see animals in their natural habitat.

Which place would you like to visit?

5. If user selects anything other than these 4 options, say: "I apologize, but I can only process bookings for the listed attractions (a/b/c/d). Please choose one of these options."

6. After they choose a valid place, ask for their preferred date of visit. When processing date:
   - If user says "today", use {current_date_str}
   - If user says "tomorrow", use {(current_date + timedelta(days=1)).strftime("%Y-%m-%d")}
   - If user mentions a day of the week (e.g., "this Sunday"), calculate the next occurrence of that day
   - If user provides a specific date, verify it's not in the past
   - If date is in the past, ask them to choose a future date

7. After getting a valid date, show the pricing and ask for quantities in this exact format:

Here are our ticket prices:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    Children:  ₹10 per ticket
    Students:  ₹15 per ticket
    Adults:    ₹20 per ticket

Please tell me how many tickets you need in each category
(for example: 2 adults, 1 student, 1 child)

8. After getting the quantities, show breakdown ONLY for tickets that were requested (don't show calculations for zero tickets):

Here's your booking breakdown:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Only show these lines if that ticket type was requested:
    Adult tickets:   Z × ₹20 = ₹[amount]
    Student tickets: Y × ₹15 = ₹[amount]
    Children tickets: X × ₹10 = ₹[amount]]
    ────────────────────────────────────
    Total amount:    ₹[total]

9. After showing the total, say: "Great! To complete your booking, please provide your contact email address where I can send the booking details once payment is processed."

10. After user provides the email, show this complete booking summary:

Thank you for providing your email! Here's your booking summary: 📋

Booking Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    🏰 Attraction: [Selected Place]
    📅 Visit Date: [Chosen Date]
    
    🎟️ Tickets Booked:
        • X Adult tickets
        • Y Student tickets
        • Z Children tickets
    
    💰 Total Amount: ₹[total]
    📧 Contact Email: [user's email]
    🔢 Booking Reference: TIX[Random 6-digit number]

    📱 Scan QR code to pay:
    [QR_CODE_PLACEHOLDER]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

# UI Elements
st.title("🎫 TixBee Booking Assistant")
st.markdown("Your friendly ticket booking companion!")

# Initialize chat with prompt and send welcome message
if not st.session_state['greeted']:
    st.session_state['greeted'] = True
    st.session_state.chat.send_message(initial_prompt)
    
    welcome_message = """Hey there! 👋 I'm TixBee, your friendly ticket booking assistant! 

Would you like to start by telling me your name? 😊"""
    
    # Add welcome message to chat history
    st.session_state.messages.append({"role": "assistant", "content": welcome_message})

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "[QR_CODE_PLACEHOLDER]" in message["content"]:
            # Split the response at the placeholder
            parts = message["content"].split("[QR_CODE_PLACEHOLDER]")
            
            # Display the first part
            st.markdown(parts[0])
            
            # Display the QR code
            total_amount = extract_amount(message["content"])
            get_upi_qr(total_amount)
            
            # Display the rest of the message
            if len(parts) > 1:
                st.markdown(parts[1])
        else:
            st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Type your message here..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # If bot's last message was asking for name
    if st.session_state.messages[-2]["content"].strip().endswith("Would you like to start by telling me your name? 😊"):
        st.session_state['user_name'] = prompt
        print(f"Captured user name from chat: {prompt}")
    
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get bot response
    response = st.session_state.chat.send_message(prompt)
    response_text = response.text
    
    # Add assistant response
    st.session_state.messages.append({"role": "assistant", "content": response_text})
    
    with st.chat_message("assistant"):
        if "[QR_CODE_PLACEHOLDER]" in response_text and not st.session_state['payment_completed']:
            # Split the response at the placeholder
            parts = response_text.split("[QR_CODE_PLACEHOLDER]")
            
            # Display the first part
            st.markdown(parts[0])
            
            # Extract all booking details
            details = extract_booking_details(response_text)
            if details:
                # Display the QR code with email functionality
                get_upi_qr(
                    amount=details['amount'],
                    user_email=details['user_email'],
                    booking_details=details['booking_details']
                )
                # Mark payment as completed
                st.session_state['payment_completed'] = True
            
            # Display the rest of the message
            if len(parts) > 1:
                st.markdown(parts[1])
        else:
            # Normal chat response
            st.markdown(response_text)

    # Save conversation history
    st.session_state['conversation_history'].append({
        "user_message": prompt,
        "bot_response": response_text,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    # Save to JSON file
    with open("conversation_history.json", "w") as file:
        json.dump(st.session_state.conversation_history, file, indent=4)

# Main chat flow
if st.session_state['current_state'] == 'START':
    # Initial greeting and start of booking
    if start_booking():  # Your existing start function
        st.session_state['current_state'] = 'COLLECT_DETAILS'

elif st.session_state['current_state'] == 'COLLECT_DETAILS':
    pass

elif st.session_state['current_state'] == 'PAYMENT':
    if not st.session_state['user_email'] or not st.session_state['user_name']:
        st.session_state['current_state'] = 'COLLECT_DETAILS'
    else:
        get_upi_qr(
            amount=total_amount,
            user_email=st.session_state['user_email'],
            booking_details={
                'name': st.session_state['user_name'],
                'attraction': selected_attraction,
                'visit_date': selected_date,
                'ticket_count': f"{adult_tickets} Adults, {child_tickets} Children",
            }
        )

# Initialize variables
total_amount = 0
selected_attraction = ""
selected_date = ""
adult_tickets = 0
child_tickets = 0

# Extract these values from the chat messages
for message in st.session_state['messages']:
    if message['role'] == 'assistant' and 'Total Amount: ₹' in message['content']:
        total_amount = extract_amount(message['content'])
    if message['role'] == 'assistant' and '🏰 Attraction:' in message['content']:
        match = re.search(r'🏰 Attraction: (.+?)\n', message['content'])
        if match:
            selected_attraction = match.group(1)
    if message['role'] == 'assistant' and '📅 Visit Date:' in message['content']:
        match = re.search(r'📅 Visit Date: (.+?)\n', message['content'])
        if match:
            selected_date = match.group(1)
    if message['role'] == 'assistant' and '🎟️ Tickets Booked:' in message['content']:
        adult_match = re.search(r'(\d+) Adult tickets', message['content'])
        child_match = re.search(r'(\d+) Children tickets', message['content'])
        if adult_match:
            adult_tickets = int(adult_match.group(1))
        if child_match:
            child_tickets = int(child_match.group(1))