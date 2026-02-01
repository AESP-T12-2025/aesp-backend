
import os
import google.generativeai as genai
from dotenv import load_dotenv

def test():
    load_dotenv()
    key = os.getenv("GEMINI_API_KEY")
    print(f"Testing key: {key[:10]}...")
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    try:
        response = model.generate_content("Say: KEY IS WORKING")
        print(f"SUCCESS: {response.text.strip()}")
    except Exception as e:
        print(f"FAILURE: {e}")

if __name__ == "__main__":
    test()
