from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import pandas as pd
from typing import Dict, Any
from datetime import datetime

class LookupAgent:
    def __init__(self, patients_df: pd.DataFrame, llm):
        self.llm = llm
        self.patients_df = patients_df
        
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Look up patient in database and determine if new or returning"""
        
        patient_name = state.get('patient_name', '')
        date_of_birth = state.get('date_of_birth', '')
        
        # Ensure we have basic demographic info before proceeding
        if not patient_name or not date_of_birth:
            response = "I need your full name and date of birth to look up your records. Please provide them."
            state['conversation_stage'] = 'greeting' # Go back to greeting to collect info
            state['messages'].append(AIMessage(content=response))
            return state

        # Search for patient in database
        patient_record = self._search_patient(patient_name, date_of_birth)
        
        if patient_record is not None:
            # Returning patient found
            state['patient_type'] = 'returning'
            state['patient_id'] = patient_record['patient_id']
            
            # Pre-fill known information from patient record if not already in state
            state['phone'] = state.get('phone') or patient_record.get('phone_number', '')
            state['email'] = state.get('email') or patient_record.get('email', '')
            state['preferred_doctor'] = state.get('preferred_doctor') or patient_record.get('preferred_doctor', '')
            state['location'] = state.get('location') or patient_record.get('location', '')
            
            last_visit = patient_record.get('last_visit_date', 'N/A')
            preferred_doctor_name = patient_record.get('preferred_doctor', 'N/A')
            
            response = f"Welcome back, {patient_name}! I found your records. Your last visit was on {last_visit} with {preferred_doctor_name}. I can schedule you for a 30-minute follow-up appointment. Would you like to see {preferred_doctor_name} again at the same location?"
            
            state['conversation_stage'] = 'scheduling' # Move to scheduling
        else:
            # New patient
            state['patient_type'] = 'new'
            state['patient_id'] = self._generate_patient_id()
            
            response = f"Welcome to our clinic, {patient_name}! I don't see you in our system, so you'll be scheduled as a new patient with a 60-minute appointment. This will give the doctor extra time to review your medical history and perform a comprehensive examination."
            
            # If doctor and location preferences are already provided (from greeting agent)
            if state.get('preferred_doctor') and state.get('location'):
                response += f" I see you'd like to see {state['preferred_doctor']} at {state['location']}. Let me check their availability."
                state['conversation_stage'] = 'scheduling' # Move to scheduling
            else:
                response += " Which doctor would you prefer to see, and at which location?"
                state['conversation_stage'] = 'greeting'  # Go back to greeting to collect doctor/location
        
        # Add the response to messages
        state['messages'].append(AIMessage(content=response))
        
        return state
    
    def _search_patient(self, patient_name: str, date_of_birth: str) -> Dict[str, Any]:
        """Search for patient in the database"""
        if self.patients_df.empty:
            return None
            
        # Parse the name
        name_parts = patient_name.strip().split()
        if len(name_parts) < 2:
            return None
            
        first_name = name_parts[0].lower()
        last_name = name_parts[-1].lower()
        
        # Convert DOB to match format in CSV (YYYY-MM-DD)
        try:
            # Assuming date_of_birth from state is MM/DD/YYYY
            dob_datetime = datetime.strptime(date_of_birth, '%m/%d/%Y')
            dob_formatted = dob_datetime.strftime('%Y-%m-%d')
        except ValueError:
            return None
        
        # Search in the dataframe
        matches = self.patients_df[
            (self.patients_df['first_name'].str.lower() == first_name) &
            (self.patients_df['last_name'].str.lower() == last_name) &
            (self.patients_df['date_of_birth'] == dob_formatted)
        ]
        
        if not matches.empty:
            return matches.iloc[0].to_dict()
        
        return None
    
    def _generate_patient_id(self) -> str:
        """Generate a new patient ID"""
        if self.patients_df.empty:
            return "P001"
        
        # Get the highest existing patient ID number
        # Ensure 'patient_id' column exists and is in expected format
        if 'patient_id' in self.patients_df.columns and not self.patients_df['patient_id'].empty:
            # Extract numeric part and convert to int, handling potential errors
            numeric_ids = self.patients_df['patient_id'].astype(str).str.extract(r'P(\d+)', expand=False)
            numeric_ids = pd.to_numeric(numeric_ids, errors='coerce').dropna()
            
            if not numeric_ids.empty:
                next_id = numeric_ids.max() + 1
            else:
                next_id = 1 # Start from 1 if no valid IDs found
        else:
            next_id = 1 # Start from 1 if column is missing or empty
        
        return f"P{int(next_id):03d}"