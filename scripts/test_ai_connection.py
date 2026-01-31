import os
import sys
from dotenv import load_dotenv
import google.generativeai as genai

# Add parent path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load env
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

print(f"Checking API Key...")
if not api_key:
    print("❌ GEMINI_API_KEY is missing in .env")
    sys.exit(1)

print(f"✅ Key found: {api_key[:4]}...{api_key[-4:]}")

try:
    print("Connecting to Gemini...")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
    
    print("Sending test prompt...")
    response = model.generate_content("Say 'Hello' in JSON format like: {'msg': 'Hello'}")
    
    print(f"✅ Response received: {response.text}")
except Exception as e:
    print(f"❌ Error calling Gemini: {e}")
