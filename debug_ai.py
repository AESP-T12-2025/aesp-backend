
import asyncio
import os
import sys
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Add the current directory to sys.path to import app modules
sys.path.append(os.getcwd())

from app.core.database import SessionLocal, engine
from app.models.content import Scenario
from app.services.ai_service import ai_service

async def debug_conversation():
    load_dotenv()
    db = SessionLocal()
    try:
        scenario_id = 1
        print(f"--- Debugging Conversation for Scenario ID: {scenario_id} ---")
        
        # 1. Test Database Query
        scenario = db.query(Scenario).filter(Scenario.scenario_id == scenario_id).first()
        if not scenario:
            print("❌ Scenario not found in database!")
            return
        print(f"✅ Found Scenario: {scenario.title}")
        
        # 2. Test Gemini Service
        message = "Hello, I want to practice."
        system_context = f"You are practicing: {scenario.title}"
        
        print("--- Testing Gemini Call ---")
        try:
            # Check if model is initialized
            if not ai_service.model:
                print("❌ AI Service model is NOT initialized!")
            else:
                print(f"✅ AI Service model initialized: {ai_service.model_name}")
                
            response = await ai_service.chat_with_context(message, system_context)
            print(f"--- AI Response ---\n{response}\n-------------------")
            
            if "That's interesting!" in response or "I'm processing" in response:
                print("⚠️ Received fallback response from ai_service!")
            else:
                print("✅ Received actual response from AI!")
                
        except Exception as ai_err:
            print(f"❌ AI Service crashed: {ai_err}")
            import traceback
            traceback.print_exc()

    except Exception as e:
        print(f"❌ Critical Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(debug_conversation())
