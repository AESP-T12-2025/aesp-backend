"""
AI Service
==========
Provides AI-powered features using Google Gemini for:
- Contextual chat (conversation practice)
- Speech analysis (grammar, pronunciation, fluency)
"""
import logging
import json
from typing import Optional

import google.generativeai as genai

from app.core.config import settings


# =============================================================================
# CONFIGURATION
# =============================================================================

logger = logging.getLogger(__name__)

# Get API key from settings or environment
GENAI_API_KEY = getattr(settings, 'GEMINI_API_KEY', None)

if not GENAI_API_KEY:
    import os
    GENAI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GENAI_API_KEY:
    logger.warning("⚠️ GEMINI_API_KEY not found in settings or environment")
else:
    genai.configure(api_key=GENAI_API_KEY)


# =============================================================================
# SERVICE CLASS
# =============================================================================

class GeminiService:
    """
    AI service using Google Gemini for English learning features.
    
    Features:
        - Contextual chat for conversation practice
        - Speech analysis with detailed feedback
    """
    
    def __init__(self, model_name: str = "gemini-2.0-flash"):
        """
        Initialize Gemini service.
        
        Args:
            model_name: The Gemini model to use
        """
        self.model_name = model_name
        
        # Re-fetch API key to ensure latest settings
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not api_key:
            import os
            api_key = os.getenv("GEMINI_API_KEY")
            
        if not api_key:
            logger.error("❌ GEMINI_API_KEY missing in settings and environment!")
            self.model = None
            return

        # Log masked key for debugging
        masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "INVALID"
        logger.info(f"🔑 Configuring Gemini with key: {masked_key}")
        
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name)
            logger.info(f"✅ Gemini service initialized with model: {model_name}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini model: {e}")
            self.model = None

    async def chat_with_context(
        self, 
        message: str, 
        context: str = "You are a helpful English tutor."
    ) -> str:
        """
        Generate a response based on user message and context.
        
        Args:
            message: User's message
            context: Conversation context/persona
            
        Returns:
            AI-generated response
        """
        if not self.model:
            logger.error("Gemini model not initialized")
            return "Sorry, AI service is currently unavailable."
        
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
            logger.error(f"Gemini chat error: {e}", exc_info=True)
            return "Sorry, I'm having trouble processing your request right now."

    async def generate_response_suggestion(
        self, 
        context: str
    ) -> str:
        """
        Generate a suggested response for the user to say in a given context.
        
        Args:
            context: The scenario description or roleplay context.
            
        Returns:
            A suggested English sentence or short paragraph.
        """
        if not self.model:
            logger.error("Gemini model not initialized")
            return "Hello, I would like to practice English."
        
        try:
            prompt = f"""
            The user is in a roleplay scenario described as: '{context}'. 
            
            Provide a natural, simple English sentence or short paragraph that the user could say AND START SPEAKING IMMEDIATELY to start or continue this interaction.
            
            - If it's an introduction, suggest a greeting and self-introduction.
            - If it's a specific situation (e.g., ordering coffee), suggest a relevant request.
            - Keep it simple (A1-B1 level) but natural.
            - Return ONLY the suggested English text, no quotes or explanations.
            """
            response = self.model.generate_content(prompt)
            return response.text.strip().replace('"', '')
            
        except Exception as e:
            logger.error(f"Gemini suggestion error: {e}", exc_info=True)
            return "Hello, I am ready to start the conversation."

    async def analyze_speech(self, text: str) -> dict:
        """
        Analyze user's speech text for grammar, pronunciation, and fluency.
        
        Args:
            text: The transcribed speech text to analyze
            
        Returns:
            Dict containing scores and detailed feedback
        """
        if not self.model:
            logger.error("Gemini model not initialized")
            return self._get_error_response()
        
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
            {{
                "grammar_score": (0-100),
                "pronunciation_score": (0-100),
                "fluency_score": (0-100),
                "corrections": ["list of major errors only"],
                "better_version": "A more natural native-like way to say this",
                "detailed_feedback": "A short, encouraging comment",
                "phonetic_analysis": {{
                    "transcription": "IPA transcription of user speech",
                    "mispronounced_words": [
                        {{ "word": "example", "correct_ipa": "/ɪɡˈzɑːmpəl/", "issue": "stressed wrong syllable" }}
                    ]
                }}
            }}
            """
            
            response = self.model.generate_content(prompt)
            
            # Cleanup Markdown code blocks if present
            cleaned_text = response.text.strip()
            print(f"DEBUG: Raw AI Response: {cleaned_text}") # DEBUG PRINT
            
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text.split("```")[1]
                if cleaned_text.startswith("json"):
                    cleaned_text = cleaned_text[4:]
                cleaned_text = cleaned_text.strip()
            
            result = json.loads(cleaned_text)
            logger.debug(f"Speech analysis completed: scores={result.get('grammar_score')}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            print(f"DEBUG: JSON Error: {e}")
            return self._get_error_response(f"AI Response Error: {str(e)}")
            
        except Exception as e:
            logger.error(f"Gemini analysis error: {e}", exc_info=True)
            print(f"DEBUG: General Error: {e}")
            return self._get_error_response(f"System Error: {str(e)}")

    def _get_error_response(self, message: str = "AI service unavailable.") -> dict:
        """Return a standardized error response."""
        return {
            "grammar_score": 0,
            "pronunciation_score": 0,
            "fluency_score": 0,
            "corrections": ["Error processing analysis"],
            "better_version": "",
            "detailed_feedback": message,
            "phonetic_analysis": {
                "transcription": "",
                "mispronounced_words": []
            }
        }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

ai_service = GeminiService()
