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
        
        if not patient_name or not date_of_birth:
            # Still need more information
            response = "I still need your complete information before I can look up your records. Let me get those details from you."
            state['conversation_stage'] = 'greeting'
        else:
            # Search for patient in database
            patient_record = self._search_patient(patient_name, date_of_birth)
            
            if patient_record is not None:
                # Returning patient found
                state['patient_type'] = 'returning'
                state['patient_id'] = patient_record['patient_id']
                
                # Pre-fill known information
                if not state.get('phone'):
                    state['phone'] = patient_record['phone']
                if not state.get('email'):
                    state['email'] = patient_record['email']
                if not state.get('preferred_doctor'):
                    state['preferred_doctor'] = patient_record['preferred_doctor']
                if not state.get('location'):
                    state['location'] = patient_record['location']
                
                last_visit = patient_record.get('last_visit_date', 'N/A')
                preferred_doctor = patient_record.get('preferred_doctor', 'N/A')
                
                response = f"Welcome back, {patient_name}! I found your records. Your last visit was on {last_visit} with {preferred_doctor}. I can schedule you for a 30-minute follow-up appointment. Would you like to see {preferred_doctor} again at the same location?"
                
                state['conversation_stage'] = 'scheduling'
            else:
                # New patient
                state['patient_type'] = 'new'
                state['patient_id'] = self._generate_patient_id()
                
                response = f"Welcome to our clinic, {patient_name}! I don't see you in our system, so you'll be scheduled as a new patient with a 60-minute appointment. This will give the doctor extra time to review your medical history and perform a comprehensive examination."
                
                # Check if we have doctor and location preferences
                if state.get('preferred_doctor') and state.get('location'):
                    response += f" I see you'd like to see {state['preferred_doctor']} at {state['location']}. Let me check their availability."
                    state['conversation_stage'] = 'scheduling'
                else:
                    response += " Which doctor would you prefer to see, and at which location?"
                    state['conversation_stage'] = 'lookup'  # Stay here until we have preferences
        
        # Add the response to messages
        if 'messages' not in state:
            state['messages'] = []
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
        
        # Convert DOB to match format in CSV
        try:
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
        existing_ids = self.patients_df['patient_id'].str.extract(r'P(\d+)')[0].astype(int)
        next_id = existing_ids.max() + 1
        
        return f"P{next_id:03d}"
