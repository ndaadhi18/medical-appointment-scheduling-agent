from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime, timedelta

class SchedulerAgent:
    def __init__(self, schedule_df: pd.DataFrame, llm):
        self.llm = llm
        self.schedule_df = schedule_df
        
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle appointment scheduling with doctor availability"""
        
        patient_type = state.get('patient_type')
        preferred_doctor = state.get('preferred_doctor')
        location = state.get('location')
        
        if not patient_type or not preferred_doctor or not location:
            response = "I need to know your preferred doctor and location before I can check availability."
            state['conversation_stage'] = 'lookup'
        else:
            # Set appointment duration based on patient type
            duration = 60 if patient_type == 'new' else 30
            state['appointment_duration'] = duration
            
            # Get available slots
            available_slots = self._get_available_slots(preferred_doctor, location, duration)
            state['available_slots'] = available_slots
            
            if not available_slots:
                response = f"I'm sorry, but {preferred_doctor} doesn't have any available slots at {location} in the next two weeks for a {duration}-minute appointment. Would you like to:\n1. Choose a different doctor\n2. Choose a different location\n3. Check availability for a later date"
                state['conversation_stage'] = 'scheduling'
            else:
                # Present available slots
                slots_text = self._format_available_slots(available_slots)
                response = f"Great! {preferred_doctor} has the following {duration}-minute appointment slots available at {location}:\n\n{slots_text}\n\nWhich time slot would you prefer?"
                state['conversation_stage'] = 'scheduling'
                
                # Check if patient has selected a slot from previous interaction
                if state.get('messages'):
                    last_message = state['messages'][-1].content if state['messages'] else ""
                    selected_slot = self._extract_time_selection(last_message, available_slots)
                    if selected_slot:
                        state['appointment_date'] = selected_slot['date']
                        state['appointment_time'] = selected_slot['time']
                        response = f"Perfect! I've reserved {selected_slot['date']} at {selected_slot['time']} for your {duration}-minute appointment with {preferred_doctor} at {location}. Now I need to collect your insurance information."
                        state['conversation_stage'] = 'insurance'
        
        # Add the response to messages
        if 'messages' not in state:
            state['messages'] = []
        state['messages'].append(AIMessage(content=response))
        
        return state
    
    def _get_available_slots(self, doctor: str, location: str, duration: int) -> List[Dict[str, Any]]:
        """Get available appointment slots for the specified doctor and location"""
        if self.schedule_df.empty:
            return []
        
        # Filter schedule for the specific doctor and location
        doctor_schedule = self.schedule_df[
            (self.schedule_df['doctor_name'] == doctor) &
            (self.schedule_df['location'] == location)
        ]
        
        available_slots = []
        
        for _, row in doctor_schedule.iterrows():
            date = row['date']
            start_time = row['start_time']
            end_time = row['end_time']
            available_count = row['available_slots'] - row['booked_slots']
            
            if available_count > 0:
                # Calculate time slots based on duration
                slots = self._calculate_time_slots(date, start_time, end_time, duration, available_count)
                available_slots.extend(slots)
        
        # Sort by date and time
        available_slots.sort(key=lambda x: (x['date'], x['time']))
        
        # Return next 10 available slots
        return available_slots[:10]
    
    def _calculate_time_slots(self, date: str, start_time: str, end_time: str, duration: int, available_count: int) -> List[Dict[str, Any]]:
        """Calculate individual time slots within a day"""
        slots = []
        
        try:
            # Parse times
            start_dt = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M")
            
            current_time = start_dt
            slot_count = 0
            
            while current_time + timedelta(minutes=duration) <= end_dt and slot_count < available_count:
                slots.append({
                    'date': date,
                    'time': current_time.strftime("%H:%M"),
                    'duration': duration
                })
                
                # Move to next slot (assuming 30-minute intervals)
                current_time += timedelta(minutes=30)
                slot_count += 1
                
        except ValueError:
            pass
        
        return slots
    
    def _format_available_slots(self, slots: List[Dict[str, Any]]) -> str:
        """Format available slots for display"""
        if not slots:
            return "No available slots found."
        
        formatted_slots = []
        for i, slot in enumerate(slots, 1):
            # Convert date to readable format
            try:
                date_obj = datetime.strptime(slot['date'], '%Y-%m-%d')
                readable_date = date_obj.strftime('%A, %B %d, %Y')
            except ValueError:
                readable_date = slot['date']
            
            # Convert time to 12-hour format
            try:
                time_obj = datetime.strptime(slot['time'], '%H:%M')
                readable_time = time_obj.strftime('%I:%M %p')
            except ValueError:
                readable_time = slot['time']
            
            formatted_slots.append(f"{i}. {readable_date} at {readable_time}")
        
        return "\n".join(formatted_slots)
    
    def _extract_time_selection(self, message: str, available_slots: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract time slot selection from user message"""
        import re
        
        # Look for number selection (1, 2, 3, etc.)
        number_match = re.search(r'\b(\d+)\b', message)
        if number_match:
            try:
                selection_num = int(number_match.group(1))
                if 1 <= selection_num <= len(available_slots):
                    return available_slots[selection_num - 1]
            except (ValueError, IndexError):
                pass
        
        # Look for time patterns
        time_patterns = [
            r'(\d{1,2}:\d{2})',
            r'(\d{1,2}\s*(?:am|pm))',
            r'(\d{1,2}:\d{2}\s*(?:am|pm))'
        ]
        
        for pattern in time_patterns:
            time_match = re.search(pattern, message.lower())
            if time_match:
                selected_time = time_match.group(1)
                # Find matching slot
                for slot in available_slots:
                    if selected_time in slot['time'] or selected_time in slot['time'].lower():
                        return slot
        
        # Look for date patterns
        date_keywords = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for keyword in date_keywords:
            if keyword in message.lower():
                for slot in available_slots:
                    try:
                        date_obj = datetime.strptime(slot['date'], '%Y-%m-%d')
                        if keyword == date_obj.strftime('%A').lower():
                            return slot
                    except ValueError:
                        continue
        
        return None
