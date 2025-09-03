# 🏥 Medical Appointment Scheduling AI

An intelligent appointment booking system that automates patient scheduling, reduces no-shows, and streamlines clinic operations using LangGraph multi-agent orchestration and Google Gemini AI.

## 🎯 Project Overview

This AI-powered medical appointment scheduling system provides a complete solution for healthcare facilities to automate their booking process. Built using cutting-edge AI technologies, it handles the entire patient journey from initial contact to appointment confirmation and follow-up reminders.

### 🚀 Key Features

- **Multi-Agent Architecture**: 6 specialized AI agents handle different booking stages
- **Smart Patient Detection**: Automatically identifies new vs returning patients
- **Intelligent Scheduling**: 60-minute slots for new patients, 30-minute for returning
- **Calendar Integration**: Real-time doctor availability checking
- **Insurance Processing**: Streamlined insurance information collection
- **Form Automation**: Automatic patient intake form distribution
- **Smart Reminders**: 3-tier reminder system with conditional follow-ups
- **Excel Integration**: Automated appointment confirmations and admin reports

## 🏗️ System Architecture

### LangGraph Workflow
The system uses LangGraph to orchestrate a multi-agent conversation flow:

```
[Start] → Greeting → Lookup → Scheduler → Insurance → Confirmation → Forms → Reminders → [End]
```

### AI Agents

1. **Greeting Agent** (`src/agents/greeting_agent.py`)
   - Collects patient information (name, DOB, contact info)
   - Validates data format and completeness
   - Determines preferred doctor and location

2. **Lookup Agent** (`src/agents/lookup_agent.py`)
   - Searches patient database for existing records
   - Determines patient type (new/returning)
   - Pre-fills known information for returning patients

3. **Scheduler Agent** (`src/agents/scheduler_agent.py`)
   - Checks doctor availability based on preferences
   - Applies business logic (30/60 minute durations)
   - Presents available time slots to patients

4. **Insurance Agent** (`src/agents/insurance_agent.py`)
   - Collects insurance carrier, member ID, and group number
   - Validates insurance information format
   - Handles various insurance provider formats

5. **Confirmation Agent** (`src/agents/confirmation_agent.py`)
   - Generates appointment confirmation summary
   - Exports booking data to Excel for admin review
   - Simulates email and SMS confirmations

6. **Form Agent** (`src/agents/form_agent.py`)
   - Sends intake forms to new patients
   - Tracks form distribution and completion
   - Provides instructions for returning patients

7. **Reminder Agent** (`src/agents/reminder_agent.py`)
   - Schedules 3-tier reminder system
   - Tracks form completion and appointment confirmation
   - Handles cancellation reason collection

## 📊 Data Sources

### Patient Database (`data/patients.csv`)
- 50 synthetic patient records
- Complete contact and insurance information
- Patient type classification (new/returning)
- Medical history and preferences

### Doctor Schedule (`data/doctor_schedule.csv`)
- 3 doctors across 3 locations
- Daily availability with time slots
- Booking capacity and current reservations

### Forms (`forms/`)
- New Patient Intake Form (PDF)
- Automatically distributed after confirmation

## 🛠️ Technical Stack

- **LangGraph**: Multi-agent workflow orchestration
- **LangChain**: AI agent framework and integrations
- **Google Gemini**: Large language model for natural conversations
- **Streamlit**: Interactive web interface
- **Pandas**: Data processing and analysis
- **OpenPyXL**: Excel file operations

## 📁 Project Structure

```
medical-appointment-ai/
├── src/
│   ├── ui_app.py                 # Streamlit chatbot interface
│   ├── workflow.py               # LangGraph workflow orchestration
│   └── agents/
│       ├── greeting_agent.py     # Patient data collection
│       ├── lookup_agent.py       # Database search & patient detection
│       ├── scheduler_agent.py    # Appointment booking
│       ├── insurance_agent.py    # Insurance information collection
│       ├── confirmation_agent.py # Appointment confirmation & export
│       ├── form_agent.py         # Form distribution
│       └── reminder_agent.py     # Reminder system
├── data/
│   ├── patients.csv              # Patient database (50 records)
│   ├── doctor_schedule.csv       # Doctor availability
│   ├── appointment_confirmations.xlsx # Booking exports
│   └── remainders_log.csv        # Reminder tracking
├── forms/
│   └── New Patient Intake Form.pdf
├── requirements.txt              # Python dependencies
├── demo.html                     # Interactive demo page
└── README.md                     # Project documentation
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Google API key for Gemini
- Required Python packages (see requirements.txt)

### Installation

1. **Clone the repository**
   ```bash
   git clone [repository-url]
   cd medical-appointment-ai
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   export GOOGLE_API_KEY="your_google_api_key_here"
   ```

4. **Run the Streamlit application**
   ```bash
   streamlit run src/ui_app.py
   ```

5. **Access the application**
   - Open your browser to `http://localhost:8501`
   - Start a conversation with the AI assistant

### Demo Mode

For a quick overview, open `demo.html` in your browser to see:
- Project features and capabilities
- System architecture overview
- Sample conversation flow
- Technical implementation details

## 💬 Sample Conversation Flow

```
🤖 AI: Hello! Welcome to our medical appointment scheduling system. What's your full name?

👤 Patient: Hi, my name is John Smith

🤖 AI: Nice to meet you, John Smith! Could you please provide your date of birth?

👤 Patient: 03/15/1985

🤖 AI: Let me check our records... I found you! You're a returning patient. Your last visit was with Dr. Johnson. I can schedule a 30-minute follow-up. Would you like to see Dr. Johnson again?

👤 Patient: Yes, that works

🤖 AI: Great! Dr. Johnson has these slots available:
1. Wednesday, September 4th at 9:00 AM
2. Wednesday, September 4th at 10:30 AM
3. Thursday, September 5th at 2:00 PM

Which would you prefer?

[Conversation continues through insurance, confirmation, and reminder setup...]
```

## 📈 Business Logic

### Appointment Duration
- **New Patients**: 60 minutes (comprehensive consultation)
- **Returning Patients**: 30 minutes (follow-up care)

### Reminder Schedule
1. **3 days before**: Standard appointment reminder
2. **1 day before**: Form completion check + confirmation
3. **Day of appointment**: Final confirmation + cancellation tracking

### Data Export
- Real-time Excel export of all confirmed appointments
- Admin dashboard for tracking and reporting
- Reminder logs for follow-up management

## 🔧 Configuration

### Doctor and Location Setup
Edit `data/doctor_schedule.csv` to modify:
- Doctor names and specialties
- Clinic locations
- Available time slots
- Booking capacity

### Patient Database
Modify `data/patients.csv` to:
- Add/remove patient records
- Update insurance information
- Change patient preferences

## 📊 Admin Features

### Real-time Dashboards
- Appointment confirmation tracking
- Reminder system status
- Form completion rates
- Patient type analytics

### Data Export Capabilities
- Excel export of all bookings
- CSV export of patient data
- Reminder logs and analytics
- System performance metrics

## 🛡️ Security & Privacy

- Simulated communications (no real SMS/email sent)
- Local data processing (no external data sharing)
- HIPAA-compliant data handling practices
- Secure API key management

## 🚀 Advanced Features

### Multi-Language Support (Future)
- Configurable language models
- Multilingual patient interactions
- Localized appointment confirmations

### Integration Capabilities (Future)
- EHR system integration
- Real calendar system connectivity
- Actual SMS/email providers
- Payment processing integration

## 🤝 Contributing

This project was developed as part of a medical AI case study. For contributions or improvements:

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add comprehensive tests
5. Submit a pull request

## 📋 Success Metrics

- ✅ **Functional Demo**: Complete patient booking workflow
- ✅ **Data Accuracy**: Correct patient classification and scheduling
- ✅ **Integration Success**: Excel exports and calendar management
- ✅ **Code Quality**: Clean, documented, executable codebase
- ✅ **User Experience**: Natural conversation flow and error handling
- ✅ **Business Logic**: Accurate appointment duration and reminder system

## 📞 Support

For technical support or questions about the implementation:
- Review the code documentation
- Check the demo.html for feature overview
- Examine the test cases and examples

---

**Built with ❤️ using LangGraph, LangChain, and Google Gemini AI**

*This project demonstrates the power of multi-agent AI systems in healthcare automation.*
