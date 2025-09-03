import streamlit as st
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

st.title("🏥 Medical Appointment AI - Test")

# Test API key
api_key = os.getenv('GOOGLE_API_KEY')
if api_key:
    st.success(f"✅ API Key loaded: {api_key[:10]}...")
else:
    st.error("❌ No API key found")

# Test Gemini
try:
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.3
    )
    
    test_message = st.text_input("Test message:", "Hello, are you working?")
    
    if st.button("Test Gemini"):
        with st.spinner("Testing..."):
            response = llm.invoke([HumanMessage(content=test_message)])
            st.success(f"🤖 Gemini Response: {response.content}")
            
except Exception as e:
    st.error(f"❌ Error: {e}")

st.write("If you can see this, Streamlit is working!")
