import requests
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime, timedelta

CALENDLY_API_BASE_URL = "https://api.calendly.com"
CALENDLY_API_KEY = os.getenv("CALENDLY_API_KEY")

class SchedulerAgent:
    def __init__(self, schedule_df: pd.DataFrame, llm):
        self.llm = llm
        self.schedule_df = schedule_df # This will be removed or adapted later
        
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle appointment scheduling by generating a Calendly link."""
        
        patient_type = state.get('patient_type')
        
        if not patient_type:
            response = "I need to know if you are a new or returning patient before I can schedule an appointment."
            state['conversation_stage'] = 'lookup'
        else:
            # Check if the appointment is already booked
            if state.get('appointment_date'):
                state['conversation_stage'] = 'insurance'
                return state

            # Determine appointment duration and Calendly event URL
            duration = 60 if patient_type == 'new' else 30
            state['appointment_duration'] = duration
            
            calendly_event_urls = {
                "new": "https://calendly.com/ndaadhi18/new-patient-consultation",
                "returning": "https://calendly.com/ndaadhi18/returning-patient-follow-up"
            }
            event_type_url = calendly_event_urls.get(patient_type)

            if not CALENDLY_API_KEY or not event_type_url:
                response = "We are currently experiencing issues with our online scheduling system. Please call the office to book an appointment."
            else:
                try:
                    booking_url = self._create_calendly_scheduling_link(event_type_url)
                    if booking_url:
                        response = f"Please use the following link to book your {duration}-minute appointment: <a href=\"{booking_url}\" target=\"_blank\">{booking_url}</a>\n\nPlease let me know once you have successfully booked the appointment."
                        state['conversation_stage'] = 'scheduling' # Stay in scheduling stage
                    else:
                        response = "I was unable to generate a scheduling link. Please try again later or call the office."
                except Exception as e:
                    print(f"Error creating Calendly link: {e}")
                    response = "An unexpected error occurred with our scheduling system. Please call the office to book an appointment."

        if 'messages' not in state:
            state['messages'] = []
        state['messages'].append(AIMessage(content=response))
        
        # Check for user confirmation
        if state.get('messages'):
            last_message = state['messages'][-1].content.lower()
            if 'done' in last_message or 'booked' in last_message or 'scheduled' in last_message:
                try:
                    # Get user URI
                    headers = {
                        "Authorization": f"Bearer {CALENDLY_API_KEY}",
                        "Content-Type": "application/json"
                    }
                    user_response = requests.get(f"{CALENDLY_API_BASE_URL}/users/me", headers=headers)
                    user_response.raise_for_status()
                    user_uri = user_response.json()["resource"]["uri"]

                    # Get the latest event
                    latest_event = self._get_latest_scheduled_event(user_uri)
                    if latest_event:
                        start_time_str = latest_event.get("start_time")
                        if start_time_str:
                            start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
                            state['appointment_date'] = start_time.strftime('%Y-%m-%d')
                            state['appointment_time'] = start_time.strftime('%H:%M')
                    
                    response = "Great! Now, let's collect your insurance information."
                    state['conversation_stage'] = 'insurance'
                    state['messages'].append(AIMessage(content=response))

                except Exception as e:
                    print(f"Error getting latest scheduled event: {e}")
                    # Fallback to placeholder if API call fails
                    state['appointment_date'] = 'Scheduled via Calendly'
                    state['appointment_time'] = 'TBD'
                    response = "Great! Now, let's collect your insurance information."
                    state['conversation_stage'] = 'insurance'
                    state['messages'].append(AIMessage(content=response))

        return state

    def _create_calendly_scheduling_link(self, event_type_url: str) -> str:
        """Create a single-use scheduling link for the given event type URL."""
        
        headers = {
            "Authorization": f"Bearer {CALENDLY_API_KEY}",
            "Content-Type": "application/json"
        }

        # 1. Get user URI
        user_response = requests.get(f"{CALENDLY_API_BASE_URL}/users/me", headers=headers)
        user_response.raise_for_status()
        user_uri = user_response.json()["resource"]["uri"]

        # 2. Get event type URI from URL
        event_types_response = requests.get(f"{CALENDLY_API_BASE_URL}/event_types", headers=headers, params={"user": user_uri})
        event_types_response.raise_for_status()
        event_types_data = event_types_response.json().get("collection", [])
        
        event_type_uri = None
        for event_type in event_types_data:
            if event_type["scheduling_url"] == event_type_url:
                event_type_uri = event_type["uri"]
                break
        
        if not event_type_uri:
            raise Exception(f"Event type not found for URL: {event_type_url}")

        # 3. Create scheduling link
        payload = {
            "max_event_count": 1,
            "owner": event_type_uri,
            "owner_type": "EventType"
        }
        
        link_response = requests.post(f"{CALENDLY_API_BASE_URL}/scheduling_links", headers=headers, json=payload)
        link_response.raise_for_status()
        
        return link_response.json().get("resource", {}).get("booking_url")

    def _get_latest_scheduled_event(self, user_uri: str) -> Dict[str, Any]:
        """Get the most recently scheduled event for the user."""
        
        headers = {
            "Authorization": f"Bearer {CALENDLY_API_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.get(
            f"{CALENDLY_API_BASE_URL}/scheduled_events",
            headers=headers,
            params={"user": user_uri, "sort": "start_time:desc", "count": 1}
        )
        response.raise_for_status()
        events = response.json().get("collection", [])
        
        if events:
            return events[0]
        return None
    
    

