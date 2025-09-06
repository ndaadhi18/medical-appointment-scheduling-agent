from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from typing import Dict, Any
import pandas as pd
import os
from datetime import datetime

class ConfirmationAgent:
    def __init__(self, llm, sendgrid_api_key: str, sendgrid_from_email: str,
                 twilio_account_sid: str, twilio_auth_token: str, twilio_phone_number: str):
        self.llm = llm
        self.sendgrid_api_key = sendgrid_api_key
        self.sendgrid_from_email = sendgrid_from_email
        self.twilio_account_sid = twilio_account_sid
        self.twilio_auth_token = twilio_auth_token
        self.twilio_phone_number = twilio_phone_number
        
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Confirm appointment and export to Excel"""
        
        # Validate all required information is present
        if not self._validate_appointment_info(state):
            response = "I'm missing some information to confirm your appointment. Let me get those details."
            state['conversation_stage'] = 'insurance'
        else:
            # Generate confirmation summary
            confirmation_summary = self._generate_confirmation_summary(state)
            
            # Export appointment to Excel
            success = self._export_to_excel(state)
            
            if success:
                state['confirmation_sent'] = True
                
                # Generate confirmation response
                response = f"""🎉 APPOINTMENT CONFIRMED! 🎉

{confirmation_summary}

✅ Your appointment has been successfully scheduled and added to our system.
✅ A confirmation record has been exported for administrative review.

NEXT STEPS:
📋 I'll now send you the new patient intake forms to complete before your visit.
📧 You'll receive email confirmations and appointment reminders.
📱 SMS reminders will be sent to {state.get('phone', 'your phone')}.

Is there anything else you'd like to know about your upcoming appointment?"""

                
                state['conversation_stage'] = 'forms'
                
                # Simulate sending email and SMS confirmations
                self._send_confirmations(state)

                # Add new patient to CSV if applicable
                if state.get('patient_type') == 'new':
                    self._add_new_patient_to_csv(state)
                
            else:
                response = "I encountered an issue while confirming your appointment. Let me try again or please contact our office directly."
                state['conversation_stage'] = 'confirmation'
        
        # Add the response to messages
        if 'messages' not in state:
            state['messages'] = []
        state['messages'].append(AIMessage(content=response))
        
        return state
    
    def _add_new_patient_to_csv(self, state: Dict[str, Any]) -> None:
        """Adds new patient data to data/patients.csv"""
        patients_file = 'data/patients.csv'
        
        # Load existing patients data
        try:
            patients_df = pd.read_csv(patients_file)
        except FileNotFoundError:
            patients_df = pd.DataFrame(columns=[
                'patient_id', 'first_name', 'last_name', 'date_of_birth', 'phone_number',
                'email', 'preferred_doctor', 'location', 'last_visit_date'
            ])

        # Generate new patient ID
        if not patients_df.empty and 'patient_id' in patients_df.columns:
            # Extract numeric part and convert to int, handling potential errors
            numeric_ids = patients_df['patient_id'].astype(str).str.extract(r'P(\d+)', expand=False)
            numeric_ids = pd.to_numeric(numeric_ids, errors='coerce').dropna()
            if not numeric_ids.empty:
                new_id_num = numeric_ids.max() + 1
            else:
                new_id_num = 1
        else:
            new_id_num = 1
        
        new_patient_id = f"P{int(new_id_num):03d}"

        # Parse name into first and last name
        patient_name_parts = state.get('patient_name', '').strip().split()
        first_name = patient_name_parts[0] if patient_name_parts else ''
        last_name = patient_name_parts[-1] if len(patient_name_parts) > 1 else ''

        # Prepare new patient record
        new_patient_record = {
            'patient_id': new_patient_id,
            'first_name': first_name,
            'last_name': last_name,
            'date_of_birth': state.get('date_of_birth', ''),
            'phone_number': state.get('phone', ''),
            'email': state.get('email', ''),
            'preferred_doctor': state.get('preferred_doctor', ''),
            'location': state.get('location', ''),
            'last_visit_date': datetime.now().strftime('%Y-%m-%d')
        }
        
        # Append new patient to DataFrame
        new_patient_df = pd.DataFrame([new_patient_record])
        updated_patients_df = pd.concat([patients_df, new_patient_df], ignore_index=True)
        
        # Save updated DataFrame to CSV
        try:
            updated_patients_df.to_csv(patients_file, index=False)
            print(f"✅ New patient {state.get('patient_name')} (ID: {new_patient_id}) added to {patients_file}")
            state['patient_id'] = new_patient_id # Update state with new patient ID
        except Exception as e:
            print(f"Error adding new patient to CSV: {e}")

    def _validate_appointment_info(self, state: Dict[str, Any]) -> bool:
        """Validate that all required appointment information is present"""
        required_fields = [
            'patient_name', 'date_of_birth', 'phone', 'email',
            'preferred_doctor', 'location', 'patient_type',
            'appointment_date', 'appointment_time', 'appointment_duration',
            'insurance_carrier', 'member_id', 'group_number'
        ]
        
        for field in required_fields:
            if not state.get(field):
                return False
        
        return True
    
    def _generate_confirmation_summary(self, state: Dict[str, Any]) -> str:
        """Generate a comprehensive appointment confirmation summary"""
        
        # Format the appointment date
        try:
            date_obj = datetime.strptime(state['appointment_date'], '%Y-%m-%d')
            formatted_date = date_obj.strftime('%A, %B %d, %Y')
        except ValueError:
            formatted_date = state['appointment_date']
        
        # Format the appointment time
        try:
            time_obj = datetime.strptime(state['appointment_time'], '%H:%M')
            formatted_time = time_obj.strftime('%I:%M %p')
        except ValueError:
            formatted_time = state['appointment_time']
        
        # Determine appointment type
        appointment_type = "New Patient Consultation" if state['patient_type'] == 'new' else "Follow-up Appointment"
        
        summary = f"""APPOINTMENT DETAILS:
👤 Patient: {state['patient_name']}
📅 Date: {formatted_date}
🕐 Time: {formatted_time}
⏱️  Duration: {state['appointment_duration']} minutes
🏥 Doctor: {state['preferred_doctor']}
📍 Location: {state['location']}
📋 Type: {appointment_type}

PATIENT INFORMATION:
📞 Phone: {state['phone']}
📧 Email: {state['email']}
🎂 Date of Birth: {state['date_of_birth']}
🆔 Patient ID: {state.get('patient_id', 'N/A')}

INSURANCE INFORMATION:
🏢 Carrier: {state['insurance_carrier']}
🆔 Member ID: {state['member_id']}
👥 Group: {state['group_number']}"""
        
        return summary
    
    def _export_to_excel(self, state: Dict[str, Any]) -> bool:
        """Export appointment data to Excel for admin review"""
        try:
            # Prepare appointment data
            appointment_data = {
                'Confirmation_ID': self._generate_confirmation_id(),
                'Patient_Name': state['patient_name'],
                'Patient_ID': state.get('patient_id', ''),
                'Date_of_Birth': state['date_of_birth'],
                'Phone': state['phone'],
                'Email': state['email'],
                'Doctor': state['preferred_doctor'],
                'Location': state['location'],
                'Appointment_Date': state['appointment_date'],
                'Appointment_Time': state['appointment_time'],
                'Duration_Minutes': state['appointment_duration'],
                'Patient_Type': state['patient_type'],
                'Insurance_Carrier': state['insurance_carrier'],
                'Member_ID': state['member_id'],
                'Group_Number': state['group_number'],
                'Booking_Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'Status': 'Confirmed'
            }
            
            # Create DataFrame
            df = pd.DataFrame([appointment_data])
            
            # Define file path
            excel_file = 'data/appointment_confirmations.xlsx'
            
            # Check if file exists and append, otherwise create new
            if os.path.exists(excel_file):
                try:
                    existing_df = pd.read_excel(excel_file)
                    combined_df = pd.concat([existing_df, df], ignore_index=True)
                except Exception:
                    combined_df = df
            else:
                combined_df = df
            
            # Save to Excel
            combined_df.to_excel(excel_file, index=False, sheet_name='Confirmations')
            
            return True
            
        except Exception as e:
            print(f"Error exporting to Excel: {e}")
            return False
    
    def _generate_confirmation_id(self) -> str:
        """Generate a unique confirmation ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"CONF-{timestamp}"
    
    def _send_confirmations(self, state: Dict[str, Any]) -> None:
        """Send email and SMS confirmations"""
        
        # Format appointment details for confirmations
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
        
        # Send email confirmation
        
        if self.sendgrid_api_key and self.sendgrid_from_email:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail

            email_content = f"""
            APPOINTMENT CONFIRMATION

            Dear {state['patient_name']},

            Your appointment has been confirmed:

            Date: {formatted_date}
            Time: {formatted_time}
            Doctor: {state['preferred_doctor']}
            Location: {state['location']}
            Duration: {state['appointment_duration']} minutes

            Please arrive 15 minutes early for check-in.

            Thank you,
            Medical Clinic Scheduling System
            """
            message = Mail(
                from_email=self.sendgrid_from_email,
                to_emails=state['email'],
                subject='Appointment Confirmation',
                html_content=email_content)
            try:
                sg = SendGridAPIClient(self.sendgrid_api_key)
                response = sg.send(message)
                print(f"✅ Email confirmation sent to {state['email']} with status code: {response.status_code}")
            except Exception as e:
                print(f"Error sending email with SendGrid: {e}")

        # Send SMS confirmation (Twilio)
        if self.twilio_account_sid and self.twilio_auth_token and self.twilio_phone_number:
            from twilio.rest import Client

            sms_content = f"Appointment confirmed: {formatted_date} at {formatted_time} with {state['preferred_doctor']} at {state['location']}. Arrive 15 min early. Reply STOP to opt out."
            
            try:
                client = Client(self.twilio_account_sid, self.twilio_auth_token)
                message = client.messages.create(
                    body=sms_content,
                    from_=self.twilio_phone_number,
                    to=state['phone']
                )
                print(f"✅ SMS confirmation sent to {state['phone']} with SID: {message.sid}")
            except Exception as e:
                print(f"Error sending SMS with Twilio: {e}")
    
    def _validate_appointment_info(self, state: Dict[str, Any]) -> bool:
        """Validate that all required appointment information is present"""
        required_fields = [
            'patient_name', 'date_of_birth', 'phone', 'email',
            'preferred_doctor', 'location', 'patient_type',
            'appointment_date', 'appointment_time', 'appointment_duration',
            'insurance_carrier', 'member_id', 'group_number'
        ]
        
        for field in required_fields:
            if not state.get(field):
                return False
        
        return True
    
    def _generate_confirmation_summary(self, state: Dict[str, Any]) -> str:
        """Generate a comprehensive appointment confirmation summary"""
        
        # Format the appointment date
        try:
            date_obj = datetime.strptime(state['appointment_date'], '%Y-%m-%d')
            formatted_date = date_obj.strftime('%A, %B %d, %Y')
        except ValueError:
            formatted_date = state['appointment_date']
        
        # Format the appointment time
        try:
            time_obj = datetime.strptime(state['appointment_time'], '%H:%M')
            formatted_time = time_obj.strftime('%I:%M %p')
        except ValueError:
            formatted_time = state['appointment_time']
        
        # Determine appointment type
        appointment_type = "New Patient Consultation" if state['patient_type'] == 'new' else "Follow-up Appointment"
        
        summary = f"""APPOINTMENT DETAILS:
👤 Patient: {state['patient_name']}
📅 Date: {formatted_date}
🕐 Time: {formatted_time}
⏱️  Duration: {state['appointment_duration']} minutes
🏥 Doctor: {state['preferred_doctor']}
📍 Location: {state['location']}
📋 Type: {appointment_type}

PATIENT INFORMATION:
📞 Phone: {state['phone']}
📧 Email: {state['email']}
🎂 Date of Birth: {state['date_of_birth']}
🆔 Patient ID: {state.get('patient_id', 'N/A')}

INSURANCE INFORMATION:
🏢 Carrier: {state['insurance_carrier']}
🆔 Member ID: {state['member_id']}
👥 Group: {state['group_number']}"""
        
        return summary
    
    def _export_to_excel(self, state: Dict[str, Any]) -> bool:
        """Export appointment data to Excel for admin review"""
        try:
            # Prepare appointment data
            appointment_data = {
                'Confirmation_ID': self._generate_confirmation_id(),
                'Patient_Name': state['patient_name'],
                'Patient_ID': state.get('patient_id', ''),
                'Date_of_Birth': state['date_of_birth'],
                'Phone': state['phone'],
                'Email': state['email'],
                'Doctor': state['preferred_doctor'],
                'Location': state['location'],
                'Appointment_Date': state['appointment_date'],
                'Appointment_Time': state['appointment_time'],
                'Duration_Minutes': state['appointment_duration'],
                'Patient_Type': state['patient_type'],
                'Insurance_Carrier': state['insurance_carrier'],
                'Member_ID': state['member_id'],
                'Group_Number': state['group_number'],
                'Booking_Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'Status': 'Confirmed'
            }
            
            # Create DataFrame
            df = pd.DataFrame([appointment_data])
            
            # Define file path
            excel_file = 'data/appointment_confirmations.xlsx'
            
            # Check if file exists and append, otherwise create new
            if os.path.exists(excel_file):
                try:
                    existing_df = pd.read_excel(excel_file)
                    combined_df = pd.concat([existing_df, df], ignore_index=True)
                except Exception:
                    combined_df = df
            else:
                combined_df = df
            
            # Save to Excel
            combined_df.to_excel(excel_file, index=False, sheet_name='Confirmations')
            
            return True
            
        except Exception as e:
            print(f"Error exporting to Excel: {e}")
            return False
    
    def _generate_confirmation_id(self) -> str:
        """Generate a unique confirmation ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"CONF-{timestamp}"
    
    def _send_confirmations(self, state: Dict[str, Any]) -> None:
        """Send email and SMS confirmations"""
        
        # Format appointment details for confirmations
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
        
        # Send email confirmation
        
        if self.sendgrid_api_key and self.sendgrid_from_email:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail

            email_content = f"""
            APPOINTMENT CONFIRMATION

            Dear {state['patient_name']},

            Your appointment has been confirmed:

            Date: {formatted_date}
            Time: {formatted_time}
            Doctor: {state['preferred_doctor']}
            Location: {state['location']}
            Duration: {state['appointment_duration']} minutes

            Please arrive 15 minutes early for check-in.

            Thank you,
            Medical Clinic Scheduling System
            """
            message = Mail(
                from_email=self.sendgrid_from_email,
                to_emails=state['email'],
                subject='Appointment Confirmation',
                html_content=email_content)
            try:
                sg = SendGridAPIClient(self.sendgrid_api_key)
                response = sg.send(message)
                print(f"✅ Email confirmation sent to {state['email']} with status code: {response.status_code}")
            except Exception as e:
                print(f"Error sending email with SendGrid: {e}")

        # Send SMS confirmation (Twilio)
        if self.twilio_account_sid and self.twilio_auth_token and self.twilio_phone_number:
            from twilio.rest import Client

            sms_content = f"Appointment confirmed: {formatted_date} at {formatted_time} with {state['preferred_doctor']} at {state['location']}. Arrive 15 min early. Reply STOP to opt out."
            
            try:
                client = Client(self.twilio_account_sid, self.twilio_auth_token)
                message = client.messages.create(
                    body=sms_content,
                    from_=self.twilio_phone_number,
                    to=state['phone']
                )
                print(f"✅ SMS confirmation sent to {state['phone']} with SID: {message.sid}")
            except Exception as e:
                print(f"Error sending SMS with Twilio: {e}")
