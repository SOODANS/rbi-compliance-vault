"""
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    # 1. Debug: Check if env var exists in the container
    api_key = os.getenv("AIzaSyB57s2hmtCq1RJ49fOitZdGBfnMkiv76f0")
    
    if not api_key:
        print("❌ Error: GOOGLE_API_KEY is not set in the environment!")
        return

    print(f"✅ Found API Key (Length: {len(api_key)})")

    try:
        # 2. Pass key explicitly to avoid SDK discovery issues
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key
        )
        
        print("Testing Gemini 2.5 Flash connection...")
        response = llm.invoke("Say 'System Online' if you can read this.")
        print(f"Response: {response.content}")
        print("✅ Success! API is active.")
        
    except Exception as e:
        print(f"❌ Connection Failed: {e}")

if __name__ == "__main__":
    test_connection()
"""

import os
from langchain_google_genai import ChatGoogleGenerativeAI

def test_connection():
    # HARDCODE JUST FOR THIS TEST
    api_key = "AIzaSyB57s2hmtCq1RJ49fOitZdGBfnMkiv76f0" 
    
    print(f"✅ Using Hardcoded Key (Length: {len(api_key)})")

    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key
        )
        
        print("Testing Gemini 2.5 Flash connection...")
        response = llm.invoke("Say 'System Online'")
        print(f"Response: {response.content}")
        print("✅ Success! API is active.")
        
    except Exception as e:
        print(f"❌ Connection Failed: {e}")

if __name__ == "__main__":
    test_connection()