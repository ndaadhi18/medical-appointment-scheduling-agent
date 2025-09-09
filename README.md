# 🏥 Medical Appointment Scheduling AI

An intelligent appointment booking system that automates patient scheduling, reduces no-shows, and streamlines clinic operations using LangGraph multi-agent orchestration and Google Gemini AI.

---

**🚀 Deployed Version:** [https://medical-appointment-scheduling-agent-langgraph-orchestration.streamlit.app/](https://medical-appointment-scheduling-agent-langgraph-orchestration.streamlit.app/) - Do check out the deployed version!
ff
---

## 📸 Result Screenshots

Below are screenshots and demo videos showcasing the working application:

### Screenshots

- **Home Screen & Chatbot Interface**
  ![Home Screen](results/chat_interface.png)

- **Appointment Confirmation**
  ![Confirmation](results/confirmation.png)

- **Excel Export Example**
  ![Excel Export](results/excel.png)

- **Email Confirmation Example**
  ![Email Confirmation](results/email_confirmation.png)

- **Form issued to Patient Email**
  ![SMS Reminder](results/form.png)


## 🎯 Project Overview

This AI-powered medical appointment scheduling system provides a complete solution for healthcare facilities to automate their booking process. Built using cutting-edge AI technologies, it handles the entire patient journey from initial contact to appointment confirmation and follow-up reminders.

### 🚀 Key Features

- **Multi-Agent Architecture**: 6 specialized AI agents handle different booking stages
- **Smart Patient Detection**: Automatically identifies new vs returning patients based on comprehensive patient records.
- **Intelligent Scheduling**: Determines 60-minute slots for new patients and 30-minute for returning patients, and provides a Calendly link for booking.
- **Calendar Integration**: Integrates with Calendly for real-time appointment booking.
- **Insurance Processing**: Streamlined insurance information collection with structured input.
- **Form Automation**: Automatic patient intake form distribution via email (for new patients).
- **Smart Reminders**: 3-tier reminder system with conditional follow-ups via simulated email and SMS.
- **Excel Integration**: Automated appointment confirmations and admin reports.

## 🏗️ System Architecture

### LangGraph Workflow
The system uses LangGraph to orchestrate a multi-agent conversation flow:

```
[Start] → Greeting → Lookup → Scheduler → Insurance → Confirmation → Forms → Reminders → [End]
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Google API key for Gemini
- Calendly API Key
- SendGrid API Key
- Twilio Account SID, Auth Token, and Phone Number
- Required Python packages (see requirements.txt)

### Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/ndaadhi18/medical-appointment-scheduling-agent
    cd medical-appointment-ai
    ```

2.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up secrets for Streamlit**
    Create a `.streamlit/secrets.toml` file in your project's root directory (if it doesn't exist) and add your API keys:
    ```toml
    GOOGLE_API_KEY="your_google_api_key_here"
    CALENDLY_API_KEY="your_calendly_api_key_here"
    SENDGRID_API_KEY="your_sendgrid_api_key_here"
    SENDGRID_FROM_EMAIL="your_sendgrid_from_email_here"
    TWILIO_ACCOUNT_SID="your_twilio_account_sid_here"
    TWILIO_AUTH_TOKEN="your_twilio_auth_token_here"
    TWILIO_PHONE_NUMBER="your_twilio_phone_number_here"
    ```
    **Note**: For local development, Streamlit reads secrets from this file. When deploying to Streamlit Community Cloud, you will need to add these secrets directly in the app's settings on the Streamlit Cloud platform.

4.  **Run the Streamlit application**
    ```bash
    streamlit run src/ui_app.py
    ```

5.  **Access the application**
    - Open your browser to `http://localhost:8501`
    - Start a conversation with the AI assistant

