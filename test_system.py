#!/usr/bin/env python3
"""
Test script to validate the medical appointment scheduling system
"""

import sys
import os
import traceback

def test_data_files():
    """Test if data files exist and are readable"""
    print("🔍 Testing data files...")
    
    files_to_check = [
        'data/patients.csv',
        'data/doctor_schedule.csv',
        'forms/New Patient Intake Form.pdf'
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"   {file_path} - exists")
            # Check if file has content (only for text files)
            if file_path.endswith('.csv'):
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        if content.strip():
                            print(f"   ✅ File has content ({len(content)} chars)")
                        else:
                            print(f"   ⚠️  File is empty")
                except Exception as e:
                    print(f"   ❌ Error reading file: {e}")
            elif file_path.endswith('.pdf'):
                print(f"   ℹ️  Skipping content check for PDF file.")
            else:
                print(f"   ℹ️  Skipping content check for unknown file type.")
        else:
            print(f"❌ {file_path} - missing")

def test_workflow_import():
    """Test if workflow and agents can be imported"""
    print("\n🔍 Testing imports...")
    
    try:
        sys.path.append('src')
        from workflow import MedicalSchedulingWorkflow
        print("✅ MedicalSchedulingWorkflow imported successfully")
        
        # Test creating workflow instance
        workflow = MedicalSchedulingWorkflow()
        print("✅ Workflow instance created successfully")
        
        # Test individual agents
        agent_modules = [
            'agents.greeting_agent',
            'agents.lookup_agent', 
            'agents.scheduler_agent',
            'agents.insurance_agent',
            'agents.confirmation_agent',
            'agents.form_agent',
            'agents.reminder_agent'
        ]
        
        for module_name in agent_modules:
            try:
                __import__(module_name)
                print(f"✅ {module_name} imported successfully")
            except Exception as e:
                print(f"❌ {module_name} import failed: {e}")
                
    except Exception as e:
        print(f"❌ Workflow import failed: {e}")
        traceback.print_exc()

def test_patient_data():
    """Test patient data loading and parsing"""
    print("\n🔍 Testing patient data...")
    
    try:
        import pandas as pd
        df = pd.read_csv('data/patients.csv')
        print(f"✅ Patient data loaded: {len(df)} patients")
        
        # Check required columns
        required_columns = ['patient_id', 'first_name', 'last_name', 'date_of_birth', 
                          'phone_number', 'email']
        
        for col in required_columns:
            if col in df.columns:
                print(f"✅ Column '{col}' exists")
            else:
                print(f"❌ Column '{col}' missing")
                
        # Show sample data
        print("\n📊 Sample patient data:")
        print(df.head(3).to_string())
        
    except Exception as e:
        print(f"❌ Patient data test failed: {e}")

def test_doctor_schedule():
    """Test doctor schedule data"""
    print("\n🔍 Testing doctor schedule...")
    
    try:
        import pandas as pd
        
        # Try CSV first
        if os.path.exists('data/doctor_schedule.csv'):
            df = pd.read_csv('data/doctor_schedule.csv')
            print(f"✅ Schedule data loaded from CSV: {len(df)} entries")
        elif os.path.exists('data/doctor_schedule.xlsx'):
            df = pd.read_excel('data/doctor_schedule.xlsx')
            print(f"✅ Schedule data loaded from Excel: {len(df)} entries")
        else:
            print("❌ No schedule data found")
            return
        
        # Check required columns
        required_columns = ['doctor_name', 'location', 'date', 'start_time', 'end_time']
        
        for col in required_columns:
            if col in df.columns:
                print(f"✅ Column '{col}' exists")
            else:
                print(f"❌ Column '{col}' missing")
        
        # Show sample data
        print("\n📊 Sample schedule data:")
        print(df.head(3).to_string())
        
    except Exception as e:
        print(f"❌ Schedule data test failed: {e}")

def test_basic_workflow():
    """Test basic workflow functionality"""
    print("\n🔍 Testing basic workflow...")
    
    try:
        sys.path.append('src')
        from workflow import MedicalSchedulingWorkflow
        from langchain_core.messages import HumanMessage
        
        # Create workflow
        workflow = MedicalSchedulingWorkflow()
        
        # Test initial state
        initial_state = {
            'messages': [],
            'patient_name': '',
            'date_of_birth': '',
            'phone': '',
            'email': '',
            'preferred_doctor': '',
            'location': '',
            'patient_type': '',
            'patient_id': '',
            'insurance_carrier': '',
            'member_id': '',
            'group_number': '',
            'appointment_date': '',
            'appointment_time': '',
            'appointment_duration': 0,
            'forms_sent': False,
            'confirmation_sent': False,
            'reminders_scheduled': False,
            'conversation_stage': 'greeting',
            'available_slots': []
        }
        
        print("✅ Initial state created")
        
        # Test greeting agent
        try:
            result = workflow.greeting_agent(initial_state)
            print("✅ Greeting agent processed successfully")
            
            if 'messages' in result and result['messages']:
                print(f"✅ Response generated: {len(result['messages'])} messages")
            else:
                print("⚠️  No response messages generated")
                
        except Exception as e:
            print(f"❌ Greeting agent failed: {e}")
            
    except Exception as e:
        print(f"❌ Basic workflow test failed: {e}")
        traceback.print_exc()

def test_multi_turn_greeting():
    """Test multi-turn greeting functionality with user input."""
    print("\n🔍 Testing multi-turn greeting...")
    
    try:
        sys.path.append('src')
        from workflow import MedicalSchedulingWorkflow
        from langchain_core.messages import HumanMessage, AIMessage
        
        workflow = MedicalSchedulingWorkflow()
        
        # Simulate initial greeting
        initial_state = {
            'messages': [],
            'patient_name': '', 'date_of_birth': '', 'phone': '', 'email': '',
            'preferred_doctor': '', 'location': '', 'patient_type': '', 'patient_id': '',
            'insurance_carrier': '', 'member_id': '', 'group_number': '',
            'appointment_date': '', 'appointment_time': '', 'appointment_duration': 0,
            'forms_sent': False, 'confirmation_sent': False, 'reminders_scheduled': False,
            'conversation_stage': 'greeting',
            'available_slots': []
        }
        
        # First turn: AI asks for info
        state_after_initial_greeting = workflow.greeting_agent(initial_state)
        print(f"   ✅ Initial greeting response: {state_after_initial_greeting['messages'][-1].content}")
        
        # Simulate user providing demographic information
        user_message_demographics = "My name is John Doe, my date of birth is 01/15/1990, my phone number is 9876543210, and my email is john.doe@example.com."
        state_after_demographics_input = state_after_initial_greeting.copy()
        state_after_demographics_input['messages'].append(HumanMessage(content=user_message_demographics))
        
        # Second turn: AI processes demographics and asks for doctor/location
        state_after_demographics_processed = workflow.greeting_agent(state_after_demographics_input)
        print(f"   ✅ Response after demographics: {state_after_demographics_processed['messages'][-1].content}")

        # Simulate user providing doctor and location
        user_message_doctor_location = "I'd like to see Dr. Vivek at Sparsh Hospital - Infantry Road."
        state_after_doctor_location_input = state_after_demographics_processed.copy()
        state_after_doctor_location_input['messages'].append(HumanMessage(content=user_message_doctor_location))

        # Third turn: AI processes doctor/location
        final_state = workflow.greeting_agent(state_after_doctor_location_input)
        
        print("   🔍 Checking extracted information after doctor/location input...")
        if final_state.get('patient_name') == 'John Doe':
            print("   ✅ Patient name extracted correctly.")
        else:
            print(f"   ❌ Patient name extraction failed. Expected 'John Doe', got '{final_state.get('patient_name')}'")
        
        if final_state.get('date_of_birth') == '01/15/1990':
            print("   ✅ Date of birth extracted correctly.")
        else:
            print(f"   ❌ Date of birth extraction failed. Expected '01/15/1990', got '{final_state.get('date_of_birth')}'")
            
        if final_state.get('phone') == '9876543210':
            print("   ✅ Phone number extracted correctly.")
        else:
            print(f"   ❌ Phone number extraction failed. Expected '9876543210', got '{final_state.get('phone')}'")
            
        if final_state.get('email') == 'john.doe@example.com':
            print("   ✅ Email extracted correctly.")
        else:
            print(f"   ❌ Email extraction failed. Expected 'john.doe@example.com', got '{final_state.get('email')}'")

        if final_state.get('preferred_doctor') == 'Dr. Vivek':
            print("   ✅ Preferred doctor extracted correctly.")
        else:
            print(f"   ❌ Preferred doctor extraction failed. Expected 'Dr. Vivek', got '{final_state.get('preferred_doctor')}'")

        if final_state.get('location') == 'Sparsh Hospital - Infantry Road':
            print("   ✅ Location extracted correctly.")
        else:
            print(f"   ❌ Location extraction failed. Expected 'Sparsh Hospital - Infantry Road', got '{final_state.get('location')}'")

        print(f"   ✅ Final conversation stage: {final_state.get('conversation_stage')}")
        print(f"   ✅ Final greeting stage: {final_state.get('conversation_stage_greeting')}")
        print(f"   ✅ Final AI response: {final_state['messages'][-1].content}")
            
    except Exception as e:
        print(f"❌ Multi-turn greeting test failed: {e}")
        traceback.print_exc()

def main():
    """Run all tests"""
    print("🏥 Medical Appointment Scheduling AI - System Test")
    print("=" * 60)
    
    test_data_files()
    test_workflow_import()
    test_patient_data()
    test_doctor_schedule()
    test_basic_workflow()
    test_multi_turn_greeting() # <--- Add this line
    
    print("\n" + "=" * 60)
    print("🏁 System test completed!")

if __name__ == "__main__":
    main()
