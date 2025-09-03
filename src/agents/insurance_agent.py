from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from typing import Dict, Any
import re

class InsuranceAgent:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.3
        )
        
        # Common insurance carriers
        self.insurance_carriers = [
            'Blue Cross', 'Blue Cross Blue Shield', 'BCBS',
            'Aetna', 'UnitedHealth', 'United Healthcare', 'UHC',
            'Cigna', 'Humana', 'Kaiser Permanente', 'Kaiser',
            'Anthem', 'Molina', 'Centene', 'WellCare',
            'Medicare', 'Medicaid'
        ]
        
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Collect and validate insurance information"""
        
        appointment_date = state.get('appointment_date')
        appointment_time = state.get('appointment_time')
        
        if not appointment_date or not appointment_time:
            response = "I need to confirm your appointment time before collecting insurance information."
            state['conversation_stage'] = 'scheduling'
        else:
            # Check what insurance information we still need
            missing_info = self._get_missing_insurance_info(state)
            
            if not missing_info:
                # All insurance information collected
                response = "Perfect! I have all your insurance information. Let me confirm your appointment details."
                state['conversation_stage'] = 'confirmation'
            else:
                # Extract any provided insurance info from the latest message
                if state.get('messages'):
                    last_message = state['messages'][-1].content if state['messages'] else ""
                    self._extract_insurance_info(state, last_message)
                
                # Generate response asking for missing information
                response = self._generate_insurance_request(missing_info, state)
                state['conversation_stage'] = 'insurance'
        
        # Add the response to messages
        if 'messages' not in state:
            state['messages'] = []
        state['messages'].append(AIMessage(content=response))
        
        return state
    
    def _get_missing_insurance_info(self, state: Dict[str, Any]) -> list:
        """Determine what insurance information is still missing"""
        missing = []
        
        if not state.get('insurance_carrier'):
            missing.append("insurance carrier")
        if not state.get('member_id'):
            missing.append("member ID")
        if not state.get('group_number'):
            missing.append("group number")
            
        return missing
    
    def _generate_insurance_request(self, missing_info: list, state: Dict[str, Any]) -> str:
        """Generate appropriate request for missing insurance information"""
        
        if 'insurance carrier' in missing_info:
            return """Now I need to collect your insurance information for billing purposes. 

First, what's your insurance carrier? Common carriers include:
• Blue Cross Blue Shield (BCBS)
• Aetna
• UnitedHealth/United Healthcare  
• Cigna
• Humana
• Kaiser Permanente
• Medicare/Medicaid

What insurance do you have?"""
        
        elif 'member ID' in missing_info:
            carrier = state.get('insurance_carrier', 'your insurance')
            return f"""Thank you! I have {carrier} as your insurance carrier.

Now I need your Member ID (also called Policy Number or Subscriber ID). This is usually found on the front of your insurance card. It may contain letters and numbers.

What's your Member ID?"""
        
        elif 'group number' in missing_info:
            return """Great! Last piece of insurance information I need is your Group Number. This is also found on your insurance card, often labeled as "Group #" or "GRP #".

If you don't see a group number on your card, or if you have individual insurance, just let me know and I can mark it as "Individual Plan".

What's your Group Number?"""
        
        else:
            return "I have all your insurance information. Let me proceed with the confirmation."
    
    def _extract_insurance_info(self, state: Dict[str, Any], message: str) -> None:
        """Extract insurance information from the message"""
        
        # Extract insurance carrier
        if not state.get('insurance_carrier'):
            message_lower = message.lower()
            
            # Check for exact matches first
            for carrier in self.insurance_carriers:
                if carrier.lower() in message_lower:
                    state['insurance_carrier'] = carrier
                    break
            
            # Check for common abbreviations and variations
            if not state.get('insurance_carrier'):
                carrier_mappings = {
                    'bcbs': 'Blue Cross Blue Shield',
                    'blue cross': 'Blue Cross',
                    'uhc': 'UnitedHealth',
                    'united': 'UnitedHealth',
                    'kaiser': 'Kaiser Permanente'
                }
                
                for abbrev, full_name in carrier_mappings.items():
                    if abbrev in message_lower:
                        state['insurance_carrier'] = full_name
                        break
        
        # Extract member ID (alphanumeric, often with dashes or spaces)
        if not state.get('member_id'):
            # Look for patterns like member ID, policy number, etc.
            member_id_patterns = [
                r'(?:member|policy|subscriber|id|number|#)\s*:?\s*([A-Za-z0-9\-\s]{6,20})',
                r'\b([A-Za-z0-9\-]{8,15})\b',  # Generic alphanumeric pattern
                r'([A-Za-z]{2,3}\d{6,12})',     # Common pattern: letters followed by numbers
                r'(\d{9,12})'                   # Numeric only patterns
            ]
            
            for pattern in member_id_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    potential_id = match.group(1).strip()
                    # Validate it's not too short or too long
                    if 6 <= len(potential_id.replace('-', '').replace(' ', '')) <= 20:
                        state['member_id'] = potential_id
                        break
        
        # Extract group number
        if not state.get('group_number'):
            # Check for "individual" or "no group" responses
            if any(word in message.lower() for word in ['individual', 'no group', 'none', 'n/a', 'na']):
                state['group_number'] = 'Individual Plan'
            else:
                # Look for group number patterns
                group_patterns = [
                    r'(?:group|grp|g)\s*#?\s*:?\s*([A-Za-z0-9\-]{3,15})',
                    r'group\s+([A-Za-z0-9\-]{3,15})',
                    r'grp\s*([A-Za-z0-9\-]{3,15})',
                    r'\b(GRP\d{3,6})\b',
                    r'\b([A-Za-z]{3}\d{3})\b'
                ]
                
                for pattern in group_patterns:
                    match = re.search(pattern, message, re.IGNORECASE)
                    if match:
                        state['group_number'] = match.group(1).strip()
                        break
    
    def _validate_insurance_info(self, state: Dict[str, Any]) -> bool:
        """Validate that all required insurance information is present and valid"""
        required_fields = ['insurance_carrier', 'member_id', 'group_number']
        
        for field in required_fields:
            if not state.get(field):
                return False
        
        # Additional validation
        member_id = state.get('member_id', '')
        if len(member_id.replace('-', '').replace(' ', '')) < 6:
            return False
        
        return True
