import requests
import os
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

CALENDLY_API_BASE_URL = "https://api.calendly.com"
CALENDLY_API_KEY = os.getenv("CALENDLY_API_KEY")

class SchedulerAgent:
    def __init__(self, schedule_df: pd.DataFrame, llm):
        self.llm = llm
        self.schedule_df = schedule_df

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle appointment scheduling via Calendly when possible, with Excel-based fallback."""
        if 'messages' not in state:
            state['messages'] = []

        patient_type = state.get('patient_type')
        if not patient_type:
            response = "I need to know if you are a new or returning patient before I can schedule an appointment."
            state['conversation_stage'] = 'lookup'
            state['messages'].append(AIMessage(content=response))
            return state

        # Respect an already scheduled appointment
        if state.get('appointment_date') and state.get('appointment_time'):
            state['conversation_stage'] = 'insurance'
            return state

        duration = 60 if patient_type == 'new' else 30
        state['appointment_duration'] = duration

        # If patient already selected a slot from fallback list
        human_text = self._get_last_human_text(state)
        if isinstance(state.get('available_slots'), list) and state['available_slots']:
            chosen = self._parse_slot_selection(human_text, len(state['available_slots']))
            if chosen is not None:
                slot = state['available_slots'][chosen]
                state['appointment_date'] = slot['date']
                state['appointment_time'] = slot['time']
                state['conversation_stage'] = 'insurance'
                state['messages'].append(AIMessage(content=f"Booked {slot['date']} at {slot['time']} with {slot['doctor']} at {slot['location']}. Now, let's collect your insurance information."))
                return state

        # Try Calendly path first when API key is present
        calendly_response: Optional[str] = None
        calendly_ok = False
        if CALENDLY_API_KEY:
            try:
                # Create a scheduling link for one of the user's event types
                booking_url = self._create_calendly_scheduling_link_for_user()
                if booking_url:
                    calendly_response = (
                        f"Please use this link to book your {duration}-minute appointment: "
                        f"<a href=\"{booking_url}\" target=\"_blank\">{booking_url}</a>\n\n"
                        "Reply with 'booked' once you complete the booking."
                    )
                    state['messages'].append(AIMessage(content=calendly_response))
                    calendly_ok = True

                    # If patient says booked/done, try to read latest scheduled event
                    if any(w in human_text for w in ["booked", "scheduled", "done", "completed"]):
                        try:
                            headers = {
                                "Authorization": f"Bearer {CALENDLY_API_KEY}",
                                "Content-Type": "application/json",
                            }
                            user_response = requests.get(f"{CALENDLY_API_BASE_URL}/users/me", headers=headers)
                            user_response.raise_for_status()
                            user_uri = user_response.json()["resource"]["uri"]
                            latest_event = self._get_latest_scheduled_event(user_uri)
                            if latest_event:
                                start_time_str = latest_event.get("start_time")
                                if start_time_str:
                                    start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
                                    state['appointment_date'] = start_time.strftime('%Y-%m-%d')
                                    state['appointment_time'] = start_time.strftime('%H:%M')
                                    state['conversation_stage'] = 'insurance'
                                    state['messages'].append(AIMessage(content="Great! Your appointment is on "
                                                                      f"{state['appointment_date']} at {state['appointment_time']}. "
                                                                      "Now, let's collect your insurance information."))
                                    return state
                        except Exception:
                            # Fall back to simulated capture if we can't pull the event
                            pass
            except Exception:
                calendly_ok = False

        # If Calendly is not available or failed, fall back to Excel-based schedule
        if not calendly_ok:
            slots = self._generate_slots_from_schedule(
                doctor_name=state.get('preferred_doctor'),
                location=state.get('location'),
                duration=duration,
            )
            state['available_slots'] = slots

            if not slots:
                response = "We couldn't access online scheduling and no local schedule is available. Please provide your preferred doctor and location, and I'll try again."
                if not state.get('preferred_doctor') or not state.get('location'):
                    state['conversation_stage'] = 'scheduling'
                else:
                    state['conversation_stage'] = 'scheduling'
                state['messages'].append(AIMessage(content=response))
                return state

            # Present top 5 options
            top = slots[:5]
            options = "\n".join([f"{i+1}. {s['date']} at {s['time']} — {s['doctor']} ({s['location']})" for i, s in enumerate(top)])
            prompt = (
                f"I found the following available {duration}-minute slots based on our schedule:\n\n{options}\n\n"
                "Reply with the option number (e.g., '2') to select a slot, or tell me a different day/time."
            )
            state['conversation_stage'] = 'scheduling'
            state['messages'].append(AIMessage(content=prompt))
            return state

        return state

    def _get_last_human_text(self, state: Dict[str, Any]) -> str:
        for msg in reversed(state.get('messages', [])):
            if isinstance(msg, HumanMessage):
                return (msg.content or "").strip().lower()
        return ""

    def _parse_slot_selection(self, human_text: str, max_index: int) -> Optional[int]:
        if not human_text:
            return None
        # Look for phrases like 'option 2' or plain numbers
        import re
        m = re.search(r"option\s*(\d+)", human_text)
        if m:
            idx = int(m.group(1)) - 1
            if 0 <= idx < max_index:
                return idx
        m2 = re.search(r"\b(\d{1,2})\b", human_text)
        if m2:
            idx = int(m2.group(1)) - 1
            if 0 <= idx < max_index:
                return idx
        return None

    def _create_calendly_scheduling_link_for_user(self) -> Optional[str]:
        """Create a generic single-use scheduling link for the first available event type for the authenticated user."""
        headers = {
            "Authorization": f"Bearer {CALENDLY_API_KEY}",
            "Content-Type": "application/json",
        }
        user_response = requests.get(f"{CALENDLY_API_BASE_URL}/users/me", headers=headers)
        user_response.raise_for_status()
        user_uri = user_response.json()["resource"]["uri"]

        event_types_response = requests.get(
            f"{CALENDLY_API_BASE_URL}/event_types", headers=headers, params={"user": user_uri}
        )
        event_types_response.raise_for_status()
        event_types = event_types_response.json().get("collection", [])
        if not event_types:
            return None

        owner_event_type_uri = event_types[0]["uri"]
        payload = {"max_event_count": 1, "owner": owner_event_type_uri, "owner_type": "EventType"}
        link_response = requests.post(
            f"{CALENDLY_API_BASE_URL}/scheduling_links", headers=headers, json=payload
        )
        link_response.raise_for_status()
        return link_response.json().get("resource", {}).get("booking_url")

    def _get_latest_scheduled_event(self, user_uri: str) -> Optional[Dict[str, Any]]:
        headers = {
            "Authorization": f"Bearer {CALENDLY_API_KEY}",
            "Content-Type": "application/json",
        }
        response = requests.get(
            f"{CALENDLY_API_BASE_URL}/scheduled_events",
            headers=headers,
            params={"user": user_uri, "sort": "start_time:desc", "count": 1},
        )
        response.raise_for_status()
        events = response.json().get("collection", [])
        return events[0] if events else None

    def _generate_slots_from_schedule(
        self,
        doctor_name: Optional[str],
        location: Optional[str],
        duration: int,
    ) -> List[Dict[str, str]]:
        """Generate available slots from local schedule CSV/Excel.
        Returns a list of dicts: {date, time, doctor, location}.
        """
        if self.schedule_df is None or self.schedule_df.empty:
            return []

        df = self.schedule_df.copy()
        # Normalize columns
        cols = {c.lower(): c for c in df.columns}
        dc = lambda x: cols.get(x, x)

        # Apply optional filters
        if doctor_name and dc('doctor_name') in df.columns:
            df = df[df[dc('doctor_name')].astype(str).str.strip().str.lower() == doctor_name.strip().lower()]
        if location and dc('location') in df.columns:
            df = df[df[dc('location')].astype(str).str.strip().str.lower().str.contains(location.strip().lower())]

        if df.empty:
            df = self.schedule_df

        slots: List[Dict[str, str]] = []
        for _, row in df.iterrows():
            try:
                date_str = str(row.get(dc('date'), '')).strip()
                start_str = str(row.get(dc('start_time'), '')).strip()
                end_str = str(row.get(dc('end_time'), '')).strip()
                doctor = str(row.get(dc('doctor_name'), 'Doctor')).strip()
                hosp = str(row.get(dc('hospital_name'), '')).strip()
                loc = str(row.get(dc('location'), '')).strip()
                avail = row.get(dc('available_slots'), None)
                booked = row.get(dc('booked_slots'), 0)

                # Parse times
                if not date_str or not start_str or not end_str:
                    continue
                try:
                    start_dt = datetime.strptime(f"{date_str} {start_str}", "%Y-%m-%d %H:%M")
                    end_dt = datetime.strptime(f"{date_str} {end_str}", "%Y-%m-%d %H:%M")
                except ValueError:
                    # Try DD/MM/YYYY
                    try:
                        start_dt = datetime.strptime(f"{date_str} {start_str}", "%d/%m/%Y %H:%M")
                        end_dt = datetime.strptime(f"{date_str} {end_str}", "%d/%m/%Y %H:%M")
                    except ValueError:
                        continue

                # Build slot times at the requested duration
                current = start_dt
                generated: List[Dict[str, str]] = []
                while current + timedelta(minutes=duration) <= end_dt:
                    generated.append(
                        {
                            "date": current.strftime("%Y-%m-%d"),
                            "time": current.strftime("%H:%M"),
                            "doctor": doctor,
                            "location": f"{hosp}" if hosp else loc,
                        }
                    )
                    current += timedelta(minutes=duration)

                # Respect availability counts if provided
                if isinstance(avail, (int, float)):
                    try:
                        avail_count = int(avail) - int(booked or 0)
                        if avail_count > 0:
                            generated = generated[:avail_count]
                        else:
                            generated = []
                    except Exception:
                        pass

                slots.extend(generated)
            except Exception:
                continue

        # Sort by date/time ascending
        def keyer(s):
            try:
                return datetime.strptime(f"{s['date']} {s['time']}", "%Y-%m-%d %H:%M")
            except Exception:
                return datetime.max
        slots.sort(key=keyer)
        return slots
