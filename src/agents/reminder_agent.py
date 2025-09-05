import os
import sendgrid
from sendgrid.helpers.mail import Mail
from twilio.rest import Client
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from typing import Dict, Any, List
from datetime import datetime, timedelta
import json



class ReminderAgent:
    def __init__(self, llm, sendgrid_api_key: str, sendgrid_from_email: str,
                 twilio_account_sid: str, twilio_auth_token: str, twilio_phone_number: str):
        self.llm = llm
        self.sendgrid_api_key = sendgrid_api_key
        self.sendgrid_from_email = sendgrid_from_email
        self.twilio_account_sid = twilio_account_sid
        self.twilio_auth_token = twilio_auth_token
        self.twilio_phone_number = twilio_phone_number
        
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule automated reminder system"""
        
        if not state.get('forms_sent'):
            response = "I need to send the intake forms before setting up reminders."
            state['conversation_stage'] = 'forms'
        else:
            # Schedule the 3-reminder system
            success = self._schedule_reminders(state)
            
            if success:
                state['reminders_scheduled'] = True
                
                # Calculate reminder dates
                reminder_schedule = self._calculate_reminder_dates(state['appointment_date'])
                
                response = f"""🔔 REMINDER SYSTEM ACTIVATED

Perfect! I've set up your automated reminder system with 3 reminders:

📅 REMINDER SCHEDULE:
1️⃣ **First Reminder** - {reminder_schedule[0]['date']} at {reminder_schedule[0]['time']}
   • Standard appointment reminder
   • Email + SMS notification

2️⃣ **Second Reminder** - {reminder_schedule[1]['date']} at {reminder_schedule[1]['time']}
   • Form completion check
   • "Have you completed your intake forms?"
   • Email + SMS notification

3️⃣ **Final Reminder** - {reminder_schedule[2]['date']} at {reminder_schedule[2]['time']}
   • Appointment confirmation check
   • "Is your visit still confirmed? If not, please provide cancellation reason."
   • Email + SMS notification

📱 COMMUNICATION PREFERENCES:
✅ Email reminders: {state['email']}
✅ SMS reminders: {state['phone']}

🎉 **APPOINTMENT BOOKING COMPLETE!** 🎉

SUMMARY:
👤 Patient: {state['patient_name']} ({state.get('patient_type', 'new').title()} Patient)
📅 Appointment: {state['appointment_date']} at {state['appointment_time']}
🏥 Provider: {state['preferred_doctor']} at {state['location']}
⏱️  Duration: {state['appointment_duration']} minutes
💳 Insurance: {state['insurance_carrier']}

Is there anything else I can help you with regarding your appointment?"""
                
                state['conversation_stage'] = 'complete'
                
            else:
                response = "I encountered an issue setting up the reminder system. Your appointment is still confirmed, but please call our office to ensure you receive reminders."
                state['conversation_stage'] = 'reminders'
        
        # Add the response to messages
        if 'messages' not in state:
            state['messages'] = []
        state['messages'].append(AIMessage(content=response))
        
        return state
    
    def _schedule_reminders(self, state: Dict[str, Any]) -> bool:
        """Schedule the 3-reminder system and simulate sending"""
        try:
            # Calculate reminder dates and times
            reminder_schedule = self._calculate_reminder_dates(state['appointment_date'])
            
            # Create reminder records
            reminders = []
            for i, reminder in enumerate(reminder_schedule, 1):
                reminder_data = {
                    'reminder_id': f"REM-{state.get('patient_id', 'UNK')}-{i}",
                    'patient_id': state.get('patient_id', ''),
                    'patient_name': state['patient_name'],
                    'email': state['email'],
                    'phone': state['phone'],
                    'appointment_date': state['appointment_date'],
                    'appointment_time': state['appointment_time'],
                    'doctor': state['preferred_doctor'],
                    'location': state['location'],
                    'reminder_number': i,
                    'reminder_date': reminder['date'],
                    'reminder_time': reminder['time'],
                    'reminder_type': reminder['type'],
                    'message_template': reminder['message'],
                    'status': 'scheduled',
                    'sent': False, # Will be set to True after sending
                    'response_received': False,
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                reminders.append(reminder_data)
                
                # Simulate sending the reminder immediately for demonstration
                # In a real system, this would be handled by a background scheduler
                self._send_reminder_notification(reminder_data, state)
                reminder_data['sent'] = True # Mark as sent after simulation
            
            # Save reminders to log file
            self._save_reminders(reminders)
            
            # Create a summary in the remainders log (matching the existing file name)
            self._update_remainders_log(state, reminders)
            
            return True
            
        except Exception as e:
            print(f"Error scheduling reminders: {e}")
            return False
    
    def _send_reminder_notification(self, reminder_data: Dict[str, Any], state: Dict[str, Any]) -> None:
        """Sends a single reminder notification via email and SMS."""
        patient_email = reminder_data.get('email')
        patient_phone = reminder_data.get('phone')
        patient_name = reminder_data.get('patient_name')
        
        messages = self.generate_reminder_messages(reminder_data['reminder_type'], state)
        email_subject = messages['email_subject'] # Assuming generate_reminder_messages returns subject
        email_body = messages['email']
        sms_body = messages['sms']
        
        # Email (SendGrid)
        if self.sendgrid_api_key and self.sendgrid_from_email and patient_email:
            message = Mail(
                from_email=self.sendgrid_from_email,
                to_emails=patient_email,
                subject=email_subject,
                html_content=email_body
            )
            try:
                sg = sendgrid.SendGridAPIClient(self.sendgrid_api_key)
                response = sg.send(message)
                print(f"✅ Reminder email ({reminder_data['reminder_type']}) sent to {patient_email}. Status Code: {response.status_code}")
            except Exception as e:
                print(f"❌ Error sending reminder email to {patient_email}: {e}")
        else:
            print(f"Skipping reminder email ({reminder_data['reminder_type']}): Missing SendGrid credentials or patient email.")
            
        # SMS (Twilio)
        if self.twilio_account_sid and self.twilio_auth_token and self.twilio_phone_number and patient_phone:
            try:
                client = Client(self.twilio_account_sid, self.twilio_auth_token)
                message = client.messages.create(
                    to=patient_phone,
                    from_=self.twilio_phone_number,
                    body=sms_body
                )
                print(f"✅ Reminder SMS ({reminder_data['reminder_type']}) sent to {patient_phone}. SID: {message.sid}")
            except Exception as e:
                print(f"❌ Error sending reminder SMS to {patient_phone}: {e}")
        else:
            print(f"Skipping reminder SMS ({reminder_data['reminder_type']}): Missing Twilio credentials or patient phone number.")
            
        # Log actual communications (optional, but good for debugging/auditing)
        try:
            with open('data/communication_log.txt', 'a') as f:
                f.write(f"\n--- {datetime.now()} ---\\n")
                f.write(f"REMINDER EMAIL ({reminder_data['reminder_type']}) to {patient_email}: Subject: {email_subject}\n")
                f.write(f"REMINDER SMS ({reminder_data['reminder_type']}) to {patient_phone}: Body: {sms_body}\n")
                f.write("--- END ---\\n")
        except Exception as e:
            print(f"Error logging reminder communication: {e}")
    
    def _calculate_reminder_dates(self, appointment_date: str) -> List[Dict[str, Any]]:
        """Calculate reminder dates based on appointment date"""
        try:
            appt_date = datetime.strptime(appointment_date, '%Y-%m-%d')
        except ValueError:
            # Fallback to current date + 7 days if parsing fails
            appt_date = datetime.now() + timedelta(days=7)
        
        reminders = [
            {
                'date': (appt_date - timedelta(days=3)).strftime('%Y-%m-%d'),
                'time': '10:00 AM',
                'type': 'standard',
                'message': 'Standard appointment reminder'
            },
            {
                'date': (appt_date - timedelta(days=1)).strftime('%Y-%m-%d'),
                'time': '2:00 PM',
                'type': 'form_check',
                'message': 'Form completion verification'
            },
            {
                'date': appt_date.strftime('%Y-%m-%d'),
                'time': '8:00 AM',
                'type': 'confirmation',
                'message': 'Final confirmation and cancellation check'
            }
        ]
        
        return reminders
    
    def _save_reminders(self, reminders: List[Dict[str, Any]]) -> None:
        """Save reminder records to file"""
        try:
            reminders_file = 'data/scheduled_reminders.json'
            
            # Load existing reminders
            existing_reminders = []
            if os.path.exists(reminders_file):
                try:
                    with open(reminders_file, 'r') as f:
                        existing_reminders = json.load(f)
                except (json.JSONDecodeError, FileNotFoundError):
                    existing_reminders = []
            
            # Add new reminders
            existing_reminders.extend(reminders)
            
            # Save updated reminders
            with open(reminders_file, 'w') as f:
                json.dump(existing_reminders, f, indent=2)
                
        except Exception as e:
            print(f"Error saving reminders: {e}")
    
    def _update_remainders_log(self, state: Dict[str, Any], reminders: List[Dict[str, Any]]) -> None:
        """Update the remainders log CSV file"""
        try:
            import pandas as pd
            
            # Prepare log data
            log_data = {
                'patient_id': state.get('patient_id', ''),
                'patient_name': state['patient_name'],
                'appointment_date': state['appointment_date'],
                'appointment_time': state['appointment_time'],
                'doctor': state['preferred_doctor'],
                'location': state['location'],
                'email': state['email'],
                'phone': state['phone'],
                'reminder_1_date': reminders[0]['reminder_date'],
                'reminder_1_status': 'scheduled',
                'reminder_2_date': reminders[1]['reminder_date'],
                'reminder_2_status': 'scheduled',
                'reminder_3_date': reminders[2]['reminder_date'],
                'reminder_3_status': 'scheduled',
                'forms_completed': 'pending',
                'appointment_confirmed': 'pending',
                'cancellation_reason': '',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Create or update remainders log
            log_file = 'data/remainders_log.csv'
            
            if os.path.exists(log_file):
                try:
                    existing_df = pd.read_csv(log_file)
                    new_df = pd.DataFrame([log_data])
                    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                except Exception:
                    combined_df = pd.DataFrame([log_data])
            else:
                combined_df = pd.DataFrame([log_data])
            
            # Save to CSV
            combined_df.to_csv(log_file, index=False)
            
        except Exception as e:
            print(f"Error updating remainders log: {e}")
    
    def generate_reminder_messages(self, reminder_type: str, state: Dict[str, Any]) -> Dict[str, str]:
        """Generate specific reminder messages for each type"""
        
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
        
        email_subject = ""
        email_msg = ""
        sms_msg = ""

        if reminder_type == 'standard':
            email_subject = f"Appointment Reminder - {formatted_date}"
            email_msg = f"""
Subject: Appointment Reminder - {formatted_date}

Dear {state['patient_name']},

This is a reminder of your upcoming appointment:

📅 Date: {formatted_date}
🕐 Time: {formatted_time}
🏥 Doctor: {state['preferred_doctor']}
📍 Location: {state['location']}

Please arrive 15 minutes early for check-in.

If you need to reschedule, please call our office at least 24 hours in advance.

Thank you,
Medical Clinic
"""
            
            sms_msg = f"Reminder: Appointment {formatted_date} at {formatted_time} with {state['preferred_doctor']} at {state['location']}. Arrive 15 min early."
        
        elif reminder_type == 'form_check':
            email_subject = f"Forms Check - Appointment Tomorrow"
            email_msg = f"""
Subject: Forms Check - Appointment Tomorrow

Dear {state['patient_name']},

Your appointment with {state['preferred_doctor']} is tomorrow at {formatted_time}.

IMPORTANT: Have you completed your intake forms?

If not, please complete and return them today or bring them completed tomorrow.

Please reply to confirm:
1. Forms completed: YES/NO
2. Appointment confirmed: YES/NO

Thank you,
Medical Clinic
"""
            
            sms_msg = f"Appointment tomorrow at {formatted_time}. Have you completed your intake forms? Reply: 1=Forms done 2=Not done. Appointment confirmed?"
        
        else:  # confirmation
            email_subject = f"Final Confirmation - Appointment Today"
            email_msg = f"""
Subject: Final Confirmation - Appointment Today

Dear {state['patient_name']},

Your appointment is TODAY at {formatted_time} with {state['preferred_doctor']}.

Please confirm:
1. Are you still planning to attend? YES/NO
2. If NO, please provide the reason for cancellation

If yes, please arrive 15 minutes early.

Thank you,
Medical Clinic
"""
            
            sms_msg = f"Appointment TODAY at {formatted_time}. Confirm attendance: YES/NO. If NO, reply with reason. Arrive 15 min early if attending."
        
        return {
            'email_subject': email_subject, # Added subject for email
            'email': email_msg,
            'sms': sms_msg
        }
