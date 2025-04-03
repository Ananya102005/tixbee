# TixBee

TixBee is a friendly chatbot designed to assist users in booking tickets for various attractions in Bengaluru. The chatbot guides users through the booking process, providing information about attractions, pricing, and generating QR codes for payment.

## Features

- **Interactive Chat Interface**: Engages users in a conversational manner to collect booking details.
- **Attraction Information**: Provides detailed descriptions of popular attractions in Bengaluru.
- **Booking Confirmation**: Sends booking confirmation emails with QR codes for entry.
- **Flexible Date Selection**: Allows users to choose their preferred visit dates.
- **Payment Integration**: Generates UPI QR codes for seamless payment processing.

## Technologies Used

- **Streamlit**: For building the web application interface.
- **Python**: The primary programming language for backend logic.
- **SMTP**: For sending confirmation emails.
- **QR Code Generation**: Utilizes the `qrcode` library to create QR codes for bookings.
- **PIL (Pillow)**: For image processing and manipulation.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/tixbee.git
   cd tixbee
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Create a `.env` file in the root directory and add your email configuration:
     ```
     EMAIL_USERNAME=your_email@gmail.com
     EMAIL_PASSWORD=your_app_password
     EMAIL_HOST=smtp.gmail.com
     EMAIL_PORT=587
     GEMINI_API_KEY=your_api_key
     ```

## Usage

1. Run the application:
   ```bash
   streamlit run tixbee.py
   ```

2. Open your web browser and navigate to `http://localhost:8501` to interact with the chatbot.

3. Follow the prompts to book tickets for your desired Bengaluru attractions.

## Contributing

Contributions are welcome! If you have suggestions for improvements or new features, please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to the contributors and libraries that made this project possible.
- Special thanks to the users for their feedback and support.
