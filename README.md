# AI Scheduling Agent (RagaAI Case Study)

This project is a medical appointment scheduling AI agent built using **LangChain + LangGraph**.  
It automates patient booking, reduces no-shows, and integrates with mock data sources.

## Features
- Patient greeting & validation
- Patient lookup (CSV database)
- Smart scheduling (60/30 min logic)
- Calendar integration (Excel)
- Insurance collection
- Appointment confirmation + Excel export
- Form distribution (New Patient Intake Form PDF)
- 3-step reminder system (email/SMS simulation)

## Tech Stack
- LangChain + LangGraph
- Streamlit (UI)
- Pandas + OpenPyXL (CSV/Excel operations)
- APScheduler (reminders)

## Getting Started
```bash
git clone https://github.com/<your-username>/ragaai-scheduling-agent.git
cd ragaai-scheduling-agent
pip install -r requirements.txt
streamlit run src/ui_app.py
