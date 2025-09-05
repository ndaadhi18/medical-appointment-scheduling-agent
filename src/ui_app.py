import streamlit as st
import pandas as pd
from datetime import datetime
import os
import sys


# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from workflow import MedicalSchedulingWorkflow
from langchain_core.messages import HumanMessage, AIMessage

# Configure Streamlit page
st.set_page_config(
    page_title="Medical Appointment Scheduling AI",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #2E86AB, #A23B72);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .chat-container {
        max-height: 600px;
        overflow-y: auto;
        padding: 1rem;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        background-color: #f8f9fa;
    }
    
    .user-message {
        background-color: #007bff;
        color: white;
        padding: 0.8rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        margin-left: 20%;
        text-align: right;
    }
    
    .ai-message {
        background-color: #e9ecef;
        color: #333;
        padding: 0.8rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        margin-right: 20%;
    }
    
    .sidebar-info {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    
    .appointment-summary {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .error-message {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        color: #721c24;
    }
    
    .success-message {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        color: #0c5460;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'workflow' not in st.session_state:
        # Retrieve secrets from Streamlit's secrets management
        google_api_key = st.secrets.get("GOOGLE_API_KEY")
        calendly_api_key = st.secrets.get("CALENDLY_API_KEY")
        sendgrid_api_key = st.secrets.get("SENDGRID_API_KEY")
        sendgrid_from_email = st.secrets.get("SENDGRID_FROM_EMAIL")
        twilio_account_sid = st.secrets.get("TWILIO_ACCOUNT_SID")
        twilio_auth_token = st.secrets.get("TWILIO_AUTH_TOKEN")
        twilio_phone_number = st.secrets.get("TWILIO_PHONE_NUMBER")

        # Pass secrets to the workflow constructor
        st.session_state.workflow = MedicalSchedulingWorkflow(
            google_api_key=google_api_key,
            calendly_api_key=calendly_api_key,
            sendgrid_api_key=sendgrid_api_key,
            sendgrid_from_email=sendgrid_from_email,
            twilio_account_sid=twilio_account_sid,
            twilio_auth_token=twilio_auth_token,
            twilio_phone_number=twilio_phone_number
        )
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'appointment_state' not in st.session_state:
        st.session_state.appointment_state = {
            'patient_name': '',
            'date_of_birth': '',
            'phone': '',
            'email': '',
            'preferred_doctor': '',
            'location': '',
            'patient_type': '',
            'patient_id': '',
            'insurance_carrier': '',
            'member_id': '',
            'group_number': '',
            'appointment_date': '',
            'appointment_time': '',
            'appointment_duration': 0,
            'forms_sent': False,
            'confirmation_sent': False,
            'reminders_scheduled': False,
            'conversation_stage': 'greeting',
            'available_slots': [],
            'messages': []
        }
    
    if 'conversation_started' not in st.session_state:
        st.session_state.conversation_started = False

def display_chat_history():
    """Display the chat history"""
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    for message in st.session_state.chat_history:
        if isinstance(message, HumanMessage):
            st.markdown(f'<div class="user-message">👤 <strong>You:</strong> {message.content}</div>', 
                       unsafe_allow_html=True)
        elif isinstance(message, AIMessage):
            st.markdown(f'<div class="ai-message">🤖 <strong>AI Assistant:</strong> {message.content}</div>', 
                       unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_appointment_summary():
    """Display current appointment information"""
    state = st.session_state.appointment_state
    
    st.markdown("### 📋 Current Appointment Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Patient Details:**")
        st.write(f"Name: {state.get('patient_name', 'Not provided')}")
        st.write(f"DOB: {state.get('date_of_birth', 'Not provided')}")
        st.write(f"Phone: {state.get('phone', 'Not provided')}")
        st.write(f"Email: {state.get('email', 'Not provided')}")
        st.write(f"Type: {state.get('patient_type', 'Not determined').title()}")
        
    with col2:
        st.markdown("**Appointment Details:**")
        st.write(f"Doctor: {state.get('preferred_doctor', 'Not selected')}")
        st.write(f"Location: {state.get('location', 'Not selected')}")
        st.write(f"Date: {state.get('appointment_date', 'Not scheduled')}")
        st.write(f"Time: {state.get('appointment_time', 'Not scheduled')}")
        st.write(f"Duration: {state.get('appointment_duration', 0)} minutes")
    
    # Insurance information
    if state.get('insurance_carrier'):
        st.markdown("**Insurance Information:**")
        st.write(f"Carrier: {state.get('insurance_carrier', 'Not provided')}")
        st.write(f"Member ID: {state.get('member_id', 'Not provided')}")
        st.write(f"Group: {state.get('group_number', 'Not provided')}")
    
    # Status indicators
    st.markdown("**Status:**")
    col3, col4, col5 = st.columns(3)
    
    with col3:
        status = "✅" if state.get('confirmation_sent') else "⏳"
        st.write(f"{status} Confirmed")
    
    with col4:
        status = "✅" if state.get('forms_sent') else "⏳"
        st.write(f"{status} Forms Sent")
    
    with col5:
        status = "✅" if state.get('reminders_scheduled') else "⏳"
        st.write(f"{status} Reminders Set")

def display_available_doctors():
    """Display available doctors and locations"""
    st.markdown("### 👨‍⚕️ Available Doctors & Locations")
    
    doctors_info = [
        {"name": "Dr. Ramesh", "location": "Fortis Hospital - Bannerghatta Road", "specialties": "Cardiology"},
        {"name": "Dr. Manoj", "location": "People Tree Hospital - Yeshwanthpur", "specialties": "Orthopedics"},
        {"name": "Dr. Vivek", "location": "Sparsh Hospital - Infantry Road", "specialties": "Neurology"}
    ]
    
    for doctor in doctors_info:
        st.markdown(f"**{doctor['name']}** - {doctor['location']}")
        st.write(f"Specialties: {doctor['specialties']}")
        st.write("---")

def display_admin_panel():
    """Display admin panel with data exports"""
    st.markdown("### 🔧 Admin Panel")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 View Appointment Confirmations"):
            try:
                if os.path.exists('data/appointment_confirmations.xlsx'):
                    df = pd.read_excel('data/appointment_confirmations.xlsx')
                    st.dataframe(df)
                else:
                    st.info("No appointment confirmations found.")
            except Exception as e:
                st.error(f"Error loading confirmations: {e}")
    
    with col2:
        if st.button("📋 View Reminder Logs"):
            try:
                if os.path.exists('data/remainders_log.csv'):
                    df = pd.read_csv('data/remainders_log.csv')
                    st.dataframe(df)
                else:
                    st.info("No reminder logs found.")
            except Exception as e:
                st.error(f"Error loading reminder logs: {e}")
    
    # Data export buttons
    st.markdown("### 📥 Data Export")
    col3, col4 = st.columns(2)
    
    with col3:
        if st.button("Export Patient Data"):
            try:
                df = pd.read_csv('data/patients.csv')
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download Patients CSV",
                    data=csv,
                    file_name=f"patients_export_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            except Exception as e:
                st.error(f"Error exporting patient data: {e}")
    
    with col4:
        if st.button("Export Schedule Data"):
            try:
                if os.path.exists('data/doctor_schedule.csv'):
                    df = pd.read_csv('data/doctor_schedule.csv')
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download Schedule CSV",
                        data=csv,
                        file_name=f"schedule_export_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.error("Schedule data not found.")
            except Exception as e:
                st.error(f"Error exporting schedule data: {e}")

def process_user_input(user_input):
    """Process user input through the workflow"""
    try:
        # Add user message to chat history
        user_message = HumanMessage(content=user_input)
        st.session_state.chat_history.append(user_message)
        st.session_state.appointment_state['messages'].append(user_message)
        
        # Process through workflow based on current stage
        stage = st.session_state.appointment_state.get('conversation_stage', 'greeting')
        
        if stage == 'greeting':
            result = st.session_state.workflow.greeting_agent(st.session_state.appointment_state)
        elif stage == 'lookup':
            result = st.session_state.workflow.lookup_agent(st.session_state.appointment_state)
        elif stage == 'scheduling':
            result = st.session_state.workflow.scheduler_agent(st.session_state.appointment_state)
        elif stage == 'insurance':
            result = st.session_state.workflow.insurance_agent(st.session_state.appointment_state)
        elif stage == 'confirmation':
            result = st.session_state.workflow.confirmation_agent(st.session_state.appointment_state)
        elif stage == 'forms':
            result = st.session_state.workflow.form_agent(st.session_state.appointment_state)
        elif stage == 'reminders':
            result = st.session_state.workflow.reminder_agent(st.session_state.appointment_state)
        else:
            # Default to greeting
            result = st.session_state.workflow.greeting_agent(st.session_state.appointment_state)
        
        # Update session state with result
        st.session_state.appointment_state.update(result)
        
        # Add AI response to chat history
        if result.get('messages'):
            latest_ai_message = result['messages'][-1]
            if isinstance(latest_ai_message, AIMessage):
                st.session_state.chat_history.append(latest_ai_message)
        
        return True
        
    except Exception as e:
        st.error(f"Error processing input: {e}")
        return False

def main():
    """Main Streamlit application"""
    initialize_session_state()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🏥 AI Medical Appointment Scheduling Assistant</h1>
        <p>Book your appointment with our intelligent scheduling system</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown('<div class="sidebar-info">', unsafe_allow_html=True)
        st.markdown("### 🤖 How to Use")
        st.write("1. Start a conversation")
        st.write("2. Provide your information")
        st.write("3. Select doctor & time")
        st.write("4. Complete insurance details")
        st.write("5. Confirm appointment")
        st.markdown('</div>', unsafe_allow_html=True)
        
        display_available_doctors()
        
        # Reset conversation button
        if st.button("🔄 Reset Conversation"):
            st.session_state.chat_history = []
            st.session_state.appointment_state = {
                'patient_name': '',
                'date_of_birth': '',
                'phone': '',
                'email': '',
                'preferred_doctor': '',
                'location': '',
                'patient_type': '',
                'patient_id': '',
                'insurance_carrier': '',
                'member_id': '',
                'group_number': '',
                'appointment_date': '',
                'appointment_time': '',
                'appointment_duration': 0,
                'forms_sent': False,
                'confirmation_sent': False,
                'reminders_scheduled': False,
                'conversation_stage': 'greeting',
                'available_slots': [],
                'messages': []
            }
            st.session_state.conversation_started = False
            st.rerun()
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 💬 Conversation")
        
        # Welcome message
        if not st.session_state.conversation_started:
            welcome_message = AIMessage(content="""Hello! 👋 Welcome to our medical appointment scheduling system. 

I'm here to help you book an appointment with one of our doctors. I'll need to collect some information from you:

• Your name and date of birth
• Contact information (phone and email)
• Preferred doctor and location
• Insurance information

Let's get started! What's your full name?""")
            
            st.session_state.chat_history.append(welcome_message)
            st.session_state.conversation_started = True
        
        # Display chat
        display_chat_history()
        
        # Chat input
        user_input = st.chat_input("Type your message here...")
        
        if user_input:
            process_user_input(user_input)
            st.rerun()
    
    with col2:
        display_appointment_summary()
    
    # Admin panel (collapsible)
    with st.expander("🔧 Admin Panel", expanded=False):
        display_admin_panel()
    
    # Footer
    st.markdown("---")
    st.markdown("**Medical Appointment Scheduling AI** | Built with LangGraph & Streamlit | Powered by Google Gemini")

if __name__ == "__main__":
    main()
