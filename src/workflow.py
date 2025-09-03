from typing import Dict, Any, TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
import pandas as pd
from datetime import datetime, timedelta
import json
import os

class AppointmentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    patient_name: str
    date_of_birth: str
    phone: str
    email: str
    preferred_doctor: str
    location: str
    patient_type: str  # new or returning
    patient_id: str
    insurance_carrier: str
    member_id: str
    group_number: str
    appointment_date: str
    appointment_time: str
    appointment_duration: int  # 30 or 60 minutes
    forms_sent: bool
    confirmation_sent: bool
    reminders_scheduled: bool
    conversation_stage: str
    available_slots: list
    
class MedicalSchedulingWorkflow:
    def __init__(self):
        self.patients_df = self.load_patient_data()
        self.schedule_df = self.load_schedule_data()
        self.workflow = self.create_workflow()
        
    def load_patient_data(self):
        """Load patient data from CSV"""
        try:
            return pd.read_csv('data/patients.csv')
        except FileNotFoundError:
            return pd.DataFrame()
    
    def load_schedule_data(self):
        """Load doctor schedule data"""
        try:
            # Try Excel first, fallback to CSV
            if os.path.exists('data/doctor_schedule.xlsx'):
                return pd.read_excel('data/doctor_schedule.xlsx')
            else:
                return pd.read_csv('data/doctor_schedule.csv')
        except FileNotFoundError:
            return pd.DataFrame()
    
    def greeting_agent(self, state: AppointmentState) -> AppointmentState:
        """Handle initial patient greeting and data collection"""
        from src.agents.greeting_agent import GreetingAgent
        agent = GreetingAgent()
        return agent.process(state)
    
    def lookup_agent(self, state: AppointmentState) -> AppointmentState:
        """Look up patient in database and determine if new or returning"""
        from src.agents.lookup_agent import LookupAgent
        agent = LookupAgent(self.patients_df)
        return agent.process(state)
    
    def scheduler_agent(self, state: AppointmentState) -> AppointmentState:
        """Handle appointment scheduling with doctor availability"""
        from src.agents.scheduler_agent import SchedulerAgent
        agent = SchedulerAgent(self.schedule_df)
        return agent.process(state)
    
    def insurance_agent(self, state: AppointmentState) -> AppointmentState:
        """Collect and validate insurance information"""
        from src.agents.insurance_agent import InsuranceAgent
        agent = InsuranceAgent()
        return agent.process(state)
    
    def confirmation_agent(self, state: AppointmentState) -> AppointmentState:
        """Confirm appointment and export to Excel"""
        from src.agents.confirmation_agent import ConfirmationAgent
        agent = ConfirmationAgent()
        return agent.process(state)
    
    def form_agent(self, state: AppointmentState) -> AppointmentState:
        """Send patient intake forms after confirmation"""
        from src.agents.form_agent import FormAgent
        agent = FormAgent()
        return agent.process(state)
    
    def reminder_agent(self, state: AppointmentState) -> AppointmentState:
        """Schedule reminder system"""
        from src.agents.reminder_agent import ReminderAgent
        agent = ReminderAgent()
        return agent.process(state)
    
    def should_continue_to_lookup(self, state: AppointmentState) -> str:
        """Decide if we have enough info to proceed to lookup"""
        if state.get('patient_name') and state.get('date_of_birth'):
            return "lookup"
        return "greeting"
    
    def should_continue_to_scheduling(self, state: AppointmentState) -> str:
        """Decide if we can proceed to scheduling"""
        if state.get('patient_type') and state.get('preferred_doctor'):
            return "scheduler"
        return "lookup"
    
    def should_continue_to_insurance(self, state: AppointmentState) -> str:
        """Decide if we can proceed to insurance collection"""
        if state.get('appointment_date') and state.get('appointment_time'):
            return "insurance"
        return "scheduler"
    
    def should_continue_to_confirmation(self, state: AppointmentState) -> str:
        """Decide if we can proceed to confirmation"""
        if state.get('insurance_carrier') and state.get('member_id'):
            return "confirmation"
        return "insurance"
    
    def should_continue_to_forms(self, state: AppointmentState) -> str:
        """Decide if we can send forms"""
        if state.get('confirmation_sent'):
            return "forms"
        return "confirmation"
    
    def should_continue_to_reminders(self, state: AppointmentState) -> str:
        """Decide if we can schedule reminders"""
        if state.get('forms_sent'):
            return "reminders"
        return "forms"
    
    def create_workflow(self):
        """Create the LangGraph workflow"""
        workflow = StateGraph(AppointmentState)
        
        # Add nodes
        workflow.add_node("greeting", self.greeting_agent)
        workflow.add_node("lookup", self.lookup_agent)
        workflow.add_node("scheduler", self.scheduler_agent)
        workflow.add_node("insurance", self.insurance_agent)
        workflow.add_node("confirmation", self.confirmation_agent)
        workflow.add_node("forms", self.form_agent)
        workflow.add_node("reminders", self.reminder_agent)
        
        # Add edges
        workflow.add_edge(START, "greeting")
        workflow.add_conditional_edges(
            "greeting",
            self.should_continue_to_lookup,
            {"greeting": "greeting", "lookup": "lookup"}
        )
        workflow.add_conditional_edges(
            "lookup",
            self.should_continue_to_scheduling,
            {"lookup": "lookup", "scheduler": "scheduler"}
        )
        workflow.add_conditional_edges(
            "scheduler",
            self.should_continue_to_insurance,
            {"scheduler": "scheduler", "insurance": "insurance"}
        )
        workflow.add_conditional_edges(
            "insurance",
            self.should_continue_to_confirmation,
            {"insurance": "insurance", "confirmation": "confirmation"}
        )
        workflow.add_conditional_edges(
            "confirmation",
            self.should_continue_to_forms,
            {"confirmation": "confirmation", "forms": "forms"}
        )
        workflow.add_conditional_edges(
            "forms",
            self.should_continue_to_reminders,
            {"forms": "forms", "reminders": "reminders"}
        )
        workflow.add_edge("reminders", END)
        
        return workflow.compile()
    
    def run_workflow(self, initial_message: str) -> Dict[str, Any]:
        """Run the complete appointment scheduling workflow"""
        initial_state = AppointmentState(
            messages=[],
            patient_name="",
            date_of_birth="",
            phone="",
            email="",
            preferred_doctor="",
            location="",
            patient_type="",
            patient_id="",
            insurance_carrier="",
            member_id="",
            group_number="",
            appointment_date="",
            appointment_time="",
            appointment_duration=0,
            forms_sent=False,
            confirmation_sent=False,
            reminders_scheduled=False,
            conversation_stage="greeting",
            available_slots=[]
        )
        
        result = self.workflow.invoke(initial_state)
        return result
