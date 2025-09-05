from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from typing import Dict, Any
import re
from datetime import datetime

class GreetingAgent:
    def __init__(self, llm):
        self.llm = llm
        
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process greeting and collect patient information in two stages."""
        
        # Initialize greeting stage if not set
        if 'conversation_stage_greeting' not in state:
            state['conversation_stage_greeting'] = 'demographics'

        # Extract any provided information from the latest message
        if state.get('messages'):
            last_message = state['messages'][-1].content if state['messages'] else ""
            self._extract_patient_info(state, last_message)

        missing_info = self._get_missing_info(state)
        
        if not missing_info:
            # If demographics are complete, move to doctor details stage
            if state['conversation_stage_greeting'] == 'demographics':
                state['conversation_stage_greeting'] = 'doctor_details'
                missing_info = self._get_missing_info(state) # Recalculate for next stage
                
                if not missing_info: # All info collected in one go
                    response = "Perfect! I have all your information. Let me look up your records and check appointment availability."
                    state['conversation_stage'] = 'lookup'
                else:
                    # Prompt for doctor details
                    system_prompt = self._get_system_prompt(state['conversation_stage_greeting'])
                    messages = [
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=f"Patient needs to provide: {', '.join(missing_info)}. Generate a friendly response asking for all the missing doctor details at once.")
                    ]
                    if state.get('messages'):
                        messages.extend(state['messages'][-3:])
                    ai_response = self.llm.invoke(messages)
                    response = ai_response.content

            # If doctor details are complete, move to lookup stage
            elif state['conversation_stage_greeting'] == 'doctor_details':
                response = "Perfect! I have all your information. Let me look up your records and check appointment availability."
                state['conversation_stage'] = 'lookup'
        else:
            # Generate response asking for missing information for current stage
            system_prompt = self._get_system_prompt(state['conversation_stage_greeting'])
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Patient needs to provide: {', '.join(missing_info)}. Generate a friendly response asking for all the missing information at once.")
            ]
            
            if state.get('messages'):
                messages.extend(state['messages'][-3:])

            ai_response = self.llm.invoke(messages)
            response = ai_response.content
        
        if 'messages' not in state:
            state['messages'] = []
        state['messages'].append(AIMessage(content=response))
        
        return state
    
    def _get_missing_info(self, state: Dict[str, Any]) -> list:
        """Determine what information is still missing"""
        missing = []
        
        if not state.get('patient_name'):
            missing.append("full name")
        if not state.get('date_of_birth'):
            missing.append("date of birth")
        if not state.get('phone'):
            missing.append("phone number")
        if not state.get('email'):
            missing.append("email address")
        if not state.get('preferred_doctor'):
            missing.append("preferred doctor")
        if not state.get('location'):
            missing.append("preferred location")
            
        return missing
    
    def _extract_patient_info(self, state: Dict[str, Any], message: str) -> None:
        """Extract patient information from the message."""
        
        # Extract name (look for patterns like "My name is John Doe" or "I'm Jane Smith")
        name_patterns = [
            r"(?:my name is|i'm|i am|name's)\s+([A-Za-z]+\s+[A-Za-z]+)",
            r"([A-Za-z]+\s+[A-Za-z]+)(?:\s|$)"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match and not state.get('patient_name'):
                potential_name = match.group(1).strip()
                # Validate it looks like a name (two words, alphabetic)
                if len(potential_name.split()) == 2 and all(word.isalpha() for word in potential_name.split()):
                    state['patient_name'] = potential_name.title()
                    break
        
        # Extract date of birth (MM/DD/YYYY or MM-DD-YYYY)
        dob_pattern = r"(\d{1,2}[/-]\d{1,2}[/-]\d{4})"
        dob_match = re.search(dob_pattern, message)
        if dob_match and not state.get('date_of_birth'):
            dob = dob_match.group(1).replace('-', '/')
            # Validate date format
            try:
                datetime.strptime(dob, '%m/%d/%Y')
                state['date_of_birth'] = dob
            except ValueError:
                pass
        
        # Extract phone number
        phone_pattern = r"(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})"
        phone_match = re.search(phone_pattern, message)
        if phone_match and not state.get('phone'):
            phone = re.sub(r'[-.\s]', '-', phone_match.group(1))
            if len(phone.replace('-', '')) == 10:
                state['phone'] = phone
        
        # Extract email
        email_pattern = r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"
        email_match = re.search(email_pattern, message)
        if email_match and not state.get('email'):
            state['email'] = email_match.group(1).lower()
        
        # Extract doctor preference
        doctor_patterns = {
            'Dr. Johnson': ['johnson', 'dr johnson', 'dr. johnson'],
            'Dr. Martinez': ['martinez', 'dr martinez', 'dr. martinez'],
            'Dr. Lee': ['lee', 'dr lee', 'dr. lee']
        }
        
        for doctor, patterns in doctor_patterns.items():
            for pattern in patterns:
                if pattern in message.lower() and not state.get('preferred_doctor'):
                    state['preferred_doctor'] = doctor
                    break
        
        # Extract location preference
        location_patterns = {
            'Downtown Clinic': ['downtown', 'downtown clinic'],
            'Uptown Center': ['uptown', 'uptown center'],
            'West Side Clinic': ['west side', 'westside', 'west side clinic']
        }
        
        for location, patterns in location_patterns.items():
            for pattern in patterns:
                if pattern in message.lower() and not state.get('location'):
                    state['location'] = location
                    break
