import os
import google.generativeai as genai
from dotenv import load_dotenv

def test_gemini():
    load_dotenv()
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        print("❌ GEMINI_API_KEY not found in .env")
        return

    print(f"🔑 Using API Key: {key[:5]}...{key[-5:]}")
    
    try:
        genai.configure(api_key=key)
        print("📋 Available models:")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
        
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("Hello AI, are you working?")
        print(f"✅ AI Response: {response.text.strip()}")
    except Exception as e:
        print(f"❌ Gemini Error: {str(e)}")

if __name__ == "__main__":
    test_gemini()
