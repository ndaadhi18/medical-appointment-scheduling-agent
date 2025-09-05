import requests
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime, timedelta

CALENDLY_API_BASE_URL = "https://api.calendly.com"

class SchedulerAgent:
    def __init__(self, schedule_df: pd.DataFrame, llm, calendly_api_key: str):
        self.llm = llm
        self.schedule_df = schedule_df # This will be removed or adapted later
        self.calendly_api_key = calendly_api_key
        
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle appointment scheduling by generating a Calendly link and confirming booking."""
        
        patient_type = state.get('patient_type')
        
        # If patient_type is missing, something went wrong in lookup, go back
        if not patient_type:
            response = "I need to know if you are a new or returning patient before I can schedule an appointment. Let's go back."
            state['conversation_stage'] = 'lookup'
            state['messages'].append(AIMessage(content=response))
            return state

        # If appointment is already booked, move to insurance
        if state.get('appointment_date') and state.get('appointment_time'):
            response = "It looks like your appointment is already confirmed. Let's proceed to insurance."
            state['conversation_stage'] = 'insurance'
            state['messages'].append(AIMessage(content=response))
            return state

        # Check if the Calendly link has already been presented in the previous turn
        # and we are now waiting for user confirmation of booking.
        # This is identified by the conversation_stage being 'scheduling'
        # and the last AI message being the Calendly link message.
        last_ai_message_content = ""
        for i in range(len(state.get('messages', [])) - 1, -1, -1):
            if isinstance(state['messages'][i], AIMessage):
                last_ai_message_content = state['messages'][i].content
                break

        # If the last AI message was the Calendly link, and the current message is from the user, 
        # then we are expecting a booking confirmation.
        if "Please use the following link to book your" in last_ai_message_content and \
           state.get('messages') and isinstance(state['messages'][-1], HumanMessage):
            
            user_last_message = state['messages'][-1].content.lower()
            print(f"DEBUG: User's last message in confirmation check: {user_last_message}")
            if 'done' in user_last_message or 'booked' in user_last_message or 'scheduled' in user_last_message:
                print("DEBUG: User confirmed booking. Attempting to fetch details from Calendly.")
                # User confirmed booking, try to fetch details from Calendly
                try:
                    headers = {
                        "Authorization": f"Bearer {self.calendly_api_key}",
                        "Content-Type": "application/json"
                    }
                    user_response = requests.get(f"{CALENDLY_API_BASE_URL}/users/me", headers=headers)
                    user_response.raise_for_status()
                    user_uri = user_response.json()["resource"]["uri"]
                    print(f"DEBUG: User URI: {user_uri}")

                    latest_event = self._get_latest_scheduled_event(user_uri)
                    if latest_event:
                        start_time_str = latest_event.get("start_time")
                        print(f"DEBUG: start_time_str from latest_event: {start_time_str}")
                        if start_time_str:
                            start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
                            state['appointment_date'] = start_time.strftime('%Y-%m-%d')
                            state['appointment_time'] = start_time.strftime('%H:%M')
                            
                            response = "Great! Your appointment details have been captured. Now, let's collect your insurance information."
                            state['conversation_stage'] = 'insurance'
                        else:
                            print("DEBUG: start_time_str is None or empty from Calendly event.")
                            response = "I couldn't retrieve the exact appointment time from Calendly, but I'll proceed assuming it's booked. Now, let's collect your insurance information."
                            state['appointment_date'] = 'Scheduled via Calendly'
                            state['appointment_time'] = 'TBD'
                            state['conversation_stage'] = 'insurance'
                    else:
                        print("DEBUG: _get_latest_scheduled_event returned None (no recent booking found).")
                        response = "I didn't find a recent booking in Calendly. Please ensure you've completed the booking process. If you have, please try saying 'booked' or 'done' again, or contact the office."
                        state['conversation_stage'] = 'scheduling' # Stay in scheduling
                except Exception as e:
                    print(f"ERROR: Exception during Calendly confirmation process: {e}")
                    response = "An error occurred while trying to confirm your booking with Calendly. Please ensure you've completed the booking process. If you have, please try saying 'booked' or 'done' again, or contact the office."
                    state['conversation_stage'] = 'scheduling' # Stay in scheduling
            else:
                print("DEBUG: User message did not contain booking confirmation keywords.")
                # User's message was not a confirmation, re-prompt for booking
                response = "I'm waiting for you to book your appointment using the Calendly link. Please let me know once you have successfully booked it by saying 'booked' or 'done'."
                state['conversation_stage'] = 'scheduling' # Stay in scheduling
        else:
            # First time entering scheduler or previous turn was not Calendly link
            # Generate and present the Calendly link
            duration = 60 if patient_type == 'new' else 30
            state['appointment_duration'] = duration
            
            calendly_event_urls = {
                "new": "https://calendly.com/ndaadhi18/new-patient-consultation",
                "returning": "https://calendly.com/ndaadhi18/returning-patient-follow-up"
            }
            event_type_url = calendly_event_urls.get(patient_type)

            if not CALENDLY_API_KEY or not event_type_url:
                response = "We are currently experiencing issues with our online scheduling system. Please call the office to book an appointment."
                state['conversation_stage'] = 'scheduling' # Stay in scheduling
            else:
                try:
                    booking_url = self._create_calendly_scheduling_link(event_type_url)
                    if booking_url:
                        response = f"Please use the following link to book your {duration}-minute appointment: <a href=\"{booking_url}\" target=\"_blank\">{booking_url}</a>\n\nPlease let me know once you have successfully booked the appointment."
                        state['conversation_stage'] = 'scheduling' # Stay in scheduling stage
                    else:
                        response = "I was unable to generate a scheduling link. Please try again later or call the office."
                        state['conversation_stage'] = 'scheduling' # Stay in scheduling
                except Exception as e:
                    print(f"Error creating Calendly link: {e}")
                    response = "An unexpected error occurred with our scheduling system. Please call the office to book an appointment."
                    state['conversation_stage'] = 'scheduling' # Stay in scheduling

        # Add the response to messages
        state['messages'].append(AIMessage(content=response))
        
        return state

    def _create_calendly_scheduling_link(self, event_type_url: str) -> str:
        """Create a single-use scheduling link for the given event type URL."""
        
        headers = {
            "Authorization": f"Bearer {self.calendly_api_key}",
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
        print(f"DEBUG: _get_latest_scheduled_event called for user_uri: {user_uri}")
        headers = {
            "Authorization": f"Bearer {self.calendly_api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.get(
                f"{CALENDLY_API_BASE_URL}/scheduled_events",
                headers=headers,
                params={"user": user_uri, "sort": "start_time:desc", "count": 1}
            )
            response.raise_for_status()
            response_json = response.json()
            print(f"DEBUG: Calendly scheduled_events API response: {response_json}")
            events = response_json.get("collection", [])
            
            if events:
                print(f"DEBUG: Found latest event: {events[0]}")
                return events[0]
            else:
                print("DEBUG: No scheduled events found for this user.")
                return None
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Calendly API request failed in _get_latest_scheduled_event: {e}")
            return None
