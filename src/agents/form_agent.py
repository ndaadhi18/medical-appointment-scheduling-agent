from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from typing import Dict, Any
import os
from datetime import datetime

class FormAgent:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.3
        )
        
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Send patient intake forms after confirmation"""
        
        if not state.get('confirmation_sent'):
            response = "Your appointment needs to be confirmed before I can send the intake forms."
            state['conversation_stage'] = 'confirmation'
        else:
            # Check if this is a new patient (they need forms)
            if state.get('patient_type') == 'new':
                # Send intake forms
                success = self._send_intake_forms(state)
                
                if success:
                    state['forms_sent'] = True
                    
                    response = f"""📋 PATIENT INTAKE FORMS SENT

{state['patient_name']}, since this is your first visit with us, I've sent the New Patient Intake Form to your email address: {state['email']}

IMPORTANT INSTRUCTIONS:
✅ Please complete and return the forms at least 24 hours before your appointment
✅ You can fill them out digitally or print and complete by hand
✅ Bring a completed copy with you to your appointment
✅ Also bring a valid photo ID and your insurance card

The forms include:
• Medical history questionnaire
• Current medications list
• Insurance information verification
• Emergency contact information
• Privacy acknowledgment (HIPAA)

📧 If you don't see the email in your inbox, please check your spam/junk folder.

Your appointment is scheduled for {state.get('appointment_date')} at {state.get('appointment_time')} with {state.get('preferred_doctor')}.

Now I'll set up your appointment reminder system!"""
                    
                    state['conversation_stage'] = 'reminders'
                    
                else:
                    response = "I encountered an issue sending the intake forms. Please contact our office, and we'll email them to you directly."
                    state['conversation_stage'] = 'forms'
            else:
                # Returning patient - no forms needed
                state['forms_sent'] = True
                response = f"""Welcome back, {state['patient_name']}! 

Since you're a returning patient, you don't need to complete new intake forms. Your existing information in our system will be used.

WHAT TO BRING:
✅ A valid photo ID
✅ Your current insurance card
✅ List of any new medications or changes since your last visit
✅ Any relevant medical records from other providers (if applicable)

Your appointment is confirmed for {state.get('appointment_date')} at {state.get('appointment_time')} with {state.get('preferred_doctor')}.

Now I'll set up your appointment reminder system!"""
                
                state['conversation_stage'] = 'reminders'
        
        # Add the response to messages
        if 'messages' not in state:
            state['messages'] = []
        state['messages'].append(AIMessage(content=response))
        
        return state
    
    def _send_intake_forms(self, state: Dict[str, Any]) -> bool:
        """Simulate sending intake forms to patient email"""
        try:
            # Check if the form file exists
            form_path = 'forms/New Patient Intake Form.pdf'
            form_exists = os.path.exists(form_path)
            
            # Simulate email with form attachment
            email_content = self._generate_form_email(state, form_exists)
            
            # Log the simulated email
            self._log_form_email(state, email_content)
            
            # Create a reminder in the system about forms sent
            self._create_form_tracking(state)
            
            return True
            
        except Exception as e:
            print(f"Error sending intake forms: {e}")
            return False
    
    def _generate_form_email(self, state: Dict[str, Any], form_exists: bool) -> str:
        """Generate the email content for sending forms"""
        
        # Format appointment details
        try:
            date_obj = datetime.strptime(state['appointment_date'], '%Y-%m-%d')
            formatted_date = date_obj.strftime('%A, %B %d, %Y')
        except ValueError:
            formatted_date = state['appointment_date']
        
        try:
            time_obj = datetime.strptime(state['appointment_time'], '%H:%M')
            formatted_time = time_obj.strftime('%I:%M %p')
        except ValueError:
            formatted_time = state['appointment_time']
        
        email_content = f"""
Subject: New Patient Intake Forms - Appointment {formatted_date}

Dear {state['patient_name']},

Welcome to our medical practice! We're looking forward to seeing you for your appointment with {state['preferred_doctor']} on {formatted_date} at {formatted_time}.

As a new patient, please complete the attached intake forms before your visit:

ATTACHED FORMS:
• New Patient Intake Form (PDF)

INSTRUCTIONS:
1. Complete all sections of the form
2. Please return the forms at least 24 hours before your appointment
3. You can email the completed forms back to us or bring them with you
4. If you prefer, you can arrive 30 minutes early to complete forms in our office

WHAT TO BRING TO YOUR APPOINTMENT:
• Completed intake forms (if not already submitted)
• Valid photo identification (driver's license, passport, etc.)
• Current insurance card
• List of current medications (including dosages)
• Any relevant medical records from previous doctors
• Method of payment for any copay or deductible

APPOINTMENT DETAILS:
Date: {formatted_date}
Time: {formatted_time}
Doctor: {state['preferred_doctor']}
Location: {state['location']}
Duration: {state['appointment_duration']} minutes
Patient Type: New Patient Consultation

OFFICE POLICIES:
• Please arrive 15 minutes early for check-in
• Appointment cancellations require 24-hour notice
• Bring insurance card and ID to every visit

If you have any questions or need to reschedule, please call our office.

Thank you,
Medical Clinic Scheduling Team

---
This is an automated message from our appointment scheduling system.
"""
        
        if not form_exists:
            email_content += "\n\nNOTE: The intake form PDF will be attached when sent from our secure email system."
        
        return email_content
    
    def _log_form_email(self, state: Dict[str, Any], email_content: str) -> None:
        """Log the simulated form email"""
        try:
            log_file = 'data/form_emails_log.txt'
            
            with open(log_file, 'a') as f:
                f.write(f"\n{'='*50}\n")
                f.write(f"FORM EMAIL SENT: {datetime.now()}\n")
                f.write(f"TO: {state['email']}\n")
                f.write(f"PATIENT: {state['patient_name']} (ID: {state.get('patient_id', 'N/A')})\n")
                f.write(f"APPOINTMENT: {state['appointment_date']} at {state['appointment_time']}\n")
                f.write(f"{'='*50}\n")
                f.write(email_content)
                f.write(f"\n{'='*50}\n")
                
        except Exception as e:
            print(f"Error logging form email: {e}")
    
    def _create_form_tracking(self, state: Dict[str, Any]) -> None:
        """Create tracking record for forms sent"""
        try:
            tracking_file = 'data/form_tracking.csv'
            
            # Prepare tracking data
            tracking_data = {
                'patient_id': state.get('patient_id', ''),
                'patient_name': state['patient_name'],
                'email': state['email'],
                'appointment_date': state['appointment_date'],
                'appointment_time': state['appointment_time'],
                'forms_sent_date': datetime.now().strftime('%Y-%m-%d'),
                'forms_sent_time': datetime.now().strftime('%H:%M:%S'),
                'forms_completed': 'Pending',
                'forms_returned': 'No',
                'reminder_count': 0
            }
            
            # Check if tracking file exists
            if os.path.exists(tracking_file):
                # Read existing data
                import pandas as pd
                try:
                    existing_df = pd.read_csv(tracking_file)
                    new_df = pd.DataFrame([tracking_data])
                    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                except Exception:
                    combined_df = pd.DataFrame([tracking_data])
            else:
                combined_df = pd.DataFrame([tracking_data])
            
            # Save tracking data
            combined_df.to_csv(tracking_file, index=False)
            
        except Exception as e:
            print(f"Error creating form tracking: {e}")
