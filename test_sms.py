import os
from dotenv import load_dotenv
from twilio.rest import Client

# Load environment variables from .env file
load_dotenv()

def test_twilio_sms():
    """
    Tests sending an SMS message using Twilio.
    """
    print("--- Testing Twilio SMS ---")

    # --- Configuration ---
    twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")
    # --- !! IMPORTANT !! ---
    # --- Replace with a valid, Twilio-verified recipient phone number ---
    to_phone_number = "+918867478871" 
    # --- !! IMPORTANT !! ---

    if not all([twilio_account_sid, twilio_auth_token, twilio_phone_number]):
        print("❌ Error: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, or TWILIO_PHONE_NUMBER not set in .env file.")
        return

    if to_phone_number == "+15551234567":
        print("✋ Please open `test_sms.py` and replace '+15551234567' with a valid, Twilio-verified recipient phone number.")
        return

    print(f"✅ Twilio credentials found. Sending from: {twilio_phone_number}")

    # --- Send SMS ---
    try:
        client = Client(twilio_account_sid, twilio_auth_token)
        message = client.messages.create(
            body="This is a test message from the Medical Scheduling Agent.",
            from_=twilio_phone_number,
            to=to_phone_number
        )
        print(f"✅ SMS sent to {to_phone_number} with SID: {message.sid}")
        print(f"   Status: {message.status}")
    except Exception as e:
        print(f"❌ Error sending SMS with Twilio: {e}")

if __name__ == "__main__":
    test_twilio_sms()
