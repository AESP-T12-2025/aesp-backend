import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
GENAI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GENAI_API_KEY:
    print("WARNING: GEMINI_API_KEY not found in .env")

genai.configure(api_key=GENAI_API_KEY)

class GeminiService:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    async def chat_with_context(self, message: str, context: str) -> str:
        """
        Generates a response from Gemini based on the user method and a specific context/persona.
        """
        try:
            prompt = f"""
            Context: {context}
            
            User message: {message}
            
            Respond as a friendly English tutor or the specific role defined in the context. 
            Keep the response concise (under 50 words) and helpful for learning.
            """
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Gemini Chat Error: {e}")
            return "Sorry, I'm having trouble processing your request right now."

    async def analyze_speech(self, text: str) -> dict:
        """
        Analyzes the user's speech text for grammar and simulated pronunciation feedback.
        Returns a JSON object with scores and corrections.
        """
        try:
            prompt = f"""
            Act as an encouraging English Speaking Examiner.
            Analyze the following spoken sentence (converted to text) for grammar, naturalness, and clarity:
            
            USER SAID: "{text}"

            Scoring Guidelines:
            - Give HIGH SCORES (80-100) if the sentence is grammatically correct and understandable.
            - "Pronunciation_score": 0-100 (Give >80 for clear speech).
            - "Fluency_score": 0-100 (Give >80 for natural flow).
            - Do NOT return single digit scores like 8 or 9, return 80 or 90.

            Return ONLY a JSON object with this exact structure:
            {
                "grammar_score": (0-100),
                "pronunciation_score": (0-100),
                "fluency_score": (0-100),
                "corrections": ["list of major errors only"],
                "better_version": "A more natural native-like way to say this",
                "detailed_feedback": "A short, encouraging comment",
                "phonetic_analysis": {
                    "transcription": "IPA transcription of user speech",
                    "mispronounced_words": [
                        { "word": "example", "correct_ipa": "/ɪɡˈzɑːmpəl/", "issue": "stressed wrong syllable" }
                    ]
                }
            }
            """
            response = self.model.generate_content(prompt)
            # Cleanup Markdown code blocks if present
            cleaned_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned_text)
        except Exception as e:
            print(f"Gemini Analysis Error: {e}")
            return {
                "grammar_score": 0,
                "pronunciation_score": 0,
                "fluency_score": 0,
                "corrections": ["Error processing analysis"],
                "better_version": "",
                "detailed_feedback": "AI service unavailable."
            }

ai_service = GeminiService()
