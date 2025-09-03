#!/usr/bin/env python3

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import HumanMessage
    
    print("✅ Successfully imported required modules")
    
    # Check if API key is set
    api_key = os.getenv('GOOGLE_API_KEY')
    if api_key:
        print(f"✅ Google API key is set: {api_key[:10]}...")
    else:
        print("❌ Google API key is not set")
        exit(1)
    
    # Test Gemini model
    print("🧪 Testing Gemini 2.5 Flash model...")
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.3
    )
    
    # Simple test message
    test_message = HumanMessage(content="Hello! Please respond with 'AI is working correctly' if you can hear me.")
    
    response = llm.invoke([test_message])
    print(f"✅ Gemini response: {response.content}")
    
    print("✅ All tests passed! Gemini AI model is working correctly.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error testing Gemini: {e}")
