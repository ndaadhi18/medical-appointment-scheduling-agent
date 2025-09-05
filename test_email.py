import os
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
import base64

# Load environment variables from .env file
load_dotenv()

def test_sendgrid_email_with_attachment():
    """
    Tests sending an email with a PDF attachment using SendGrid.
    """
    print("--- Testing SendGrid Email with Attachment ---")

    # --- Configuration ---
    sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
    from_email = os.getenv("SENDGRID_FROM_EMAIL")
    # --- !! IMPORTANT !! ---
    # --- Replace with a valid recipient email address for testing ---
    to_email = "ndaadhi18@gmail.comt" 
    # --- !! IMPORTANT !! ---

    if not sendgrid_api_key or not from_email:
        print("❌ Error: SENDGRID_API_KEY or SENDGRID_FROM_EMAIL not set in .env file.")
        return
    
    if to_email == "test@example.com":
        print("✋ Please open `test_email.py` and replace 'test@example.com' with a valid recipient email address.")
        return

    print(f"✅ SendGrid credentials found. From: {from_email}")

    # --- PDF Attachment ---
    form_path = 'forms/New Patient Intake Form.pdf'
    print(f"Checking for PDF at: {os.path.abspath(form_path)}")
    if not os.path.exists(form_path):
        print(f"❌ Error: Intake form not found at: {form_path}")
        return
    print("✅ PDF form found.")

    with open(form_path, 'rb') as f:
        pdf_data = f.read()
    encoded_pdf = base64.b64encode(pdf_data).decode()
    print("✅ PDF form encoded.")

    # --- Email Content ---
    email_subject = "Test Email with PDF Attachment"
    email_content = """
    <h1>Test Email</h1>
    <p>This is a test email from the Medical Scheduling Agent to confirm that the SendGrid integration is working.</p>
    <p>You should see a PDF file attached to this email.</p>
    """
    print("✅ Email content generated.")

    # --- Create Mail Object ---
    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=email_subject,
        html_content=email_content
    )
    
    attached_pdf = Attachment(
        FileContent(encoded_pdf),
        FileName('New_Patient_Intake_Form.pdf'),
        FileType('application/pdf'),
        Disposition('attachment')
    )
    message.attachment = attached_pdf
    print("✅ SendGrid Mail object created.")

    # --- Send Email ---
    try:
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)
        print(f"✅ Email sent to {to_email} with status code: {response.status_code}")
        if response.status_code >= 400:
            print(f"   Response Body: {response.body}")
    except Exception as e:
        print(f"❌ Error sending email with SendGrid: {e}")

if __name__ == "__main__":
    test_sendgrid_email_with_attachment()
