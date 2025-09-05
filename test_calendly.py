import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

CALENDLY_API_KEY = os.getenv("CALENDLY_API_KEY")
CALENDLY_API_BASE_URL = "https://api.calendly.com"

def test_calendly_scheduling_link():
    """
    Tests the Calendly API integration by creating a scheduling link.
    """
    if not CALENDLY_API_KEY:
        print("Error: CALENDLY_API_KEY environment variable not set.")
        print("Please create a .env file in the root directory and add your Calendly API key:")
        print("CALENDLY_API_KEY=your_api_key")
        return

    headers = {
        "Authorization": f"Bearer {CALENDLY_API_KEY}",
        "Content-Type": "application/json"
    }

    # --- 1. Get User Information (Token Verification) ---
    try:
        print("Fetching user information to verify token...")
        user_response = requests.get(f"{CALENDLY_API_BASE_URL}/users/me", headers=headers)
        user_response.raise_for_status()
        user_data = user_response.json()
        user_uri = user_data["resource"]["uri"]
        print(f"Successfully fetched user: {user_data['resource']['name']} ({user_uri})")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching user information (Invalid Token?): {e}")
        return

    # --- 2. Get Event Types ---
    try:
        print("\nFetching event types...")
        event_types_response = requests.get(
            f"{CALENDLY_API_BASE_URL}/event_types",
            headers=headers,
            params={"user": user_uri}
        )
        event_types_response.raise_for_status()
        event_types_data = event_types_response.json().get("collection", [])
        if not event_types_data:
            print("No event types found for this user.")
            return
        print(f"Found {len(event_types_data)} event types.")
        for et in event_types_data:
            print(f"- {et['name']} (Active: {et['active']})")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching event types: {e}")
        return

    # --- 3. Create a Scheduling Link for the first event type ---
    if event_types_data:
        target_event_type_uri = event_types_data[0]["uri"]
        target_event_type_name = event_types_data[0]["name"]
        print(f"\nCreating a scheduling link for: '{target_event_type_name}'...")

        payload = {
            "max_event_count": 1,
            "owner": target_event_type_uri,
            "owner_type": "EventType"
        }

        try:
            link_response = requests.post(
                f"{CALENDLY_API_BASE_URL}/scheduling_links",
                headers=headers,
                json=payload,
            )
            link_response.raise_for_status()
            link_data = link_response.json()
            booking_url = link_data.get("resource", {}).get("booking_url")

            if booking_url:
                print(f"\nSuccessfully created a single-use scheduling link:")
                print(booking_url)
            else:
                print("\nCould not create a scheduling link.")

        except requests.exceptions.RequestException as e:
            print(f"\nError creating scheduling link: {e}")
            if e.response:
                print(f"Response Body: {e.response.text}")


if __name__ == "__main__":
    test_calendly_scheduling_link()