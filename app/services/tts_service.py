"""
TTS Service
===========
Text-to-Speech service using Edge TTS for generating audio.
"""
import logging
import uuid
import os
from pathlib import Path
from typing import Optional

import edge_tts


# =============================================================================
# CONFIGURATION
# =============================================================================

logger = logging.getLogger(__name__)

# Default voice options
DEFAULT_VOICE = "en-US-AriaNeural"
AVAILABLE_VOICES = [
    "en-US-AriaNeural",      # Female, conversational
    "en-US-GuyNeural",       # Male, conversational
    "en-GB-SoniaNeural",     # British Female
    "en-GB-RyanNeural",      # British Male
    "en-AU-NatashaNeural",   # Australian Female
]


# =============================================================================
# SERVICE CLASS
# =============================================================================

class EdgeTTSService:
    """
    Text-to-Speech service using Microsoft Edge TTS.
    
    Features:
        - Multiple voice options
        - Generates MP3 audio files
        - Serves via static file path
    """
    
    def __init__(self, output_dir: str = "app/static/audio"):
        """
        Initialize TTS service.
        
        Args:
            output_dir: Directory to save generated audio files
        """
        self.output_dir = Path(output_dir)
        self._ensure_output_dir()
        logger.info(f"✅ TTS service initialized with output dir: {self.output_dir}")

    def _ensure_output_dir(self) -> None:
        """Create output directory if it doesn't exist."""
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create output directory: {e}")

    async def generate_audio(
        self, 
        text: str, 
        voice: str = DEFAULT_VOICE
    ) -> Optional[str]:
        """
        Generate audio from text using EdgeTTS.
        
        Args:
            text: The text to convert to speech
            voice: The voice to use (default: en-US-AriaNeural)
            
        Returns:
            URL path to the generated audio file, or None if failed
        """
        if not text or not text.strip():
            logger.warning("Empty text provided to TTS service")
            return None
        
        # Validate voice
        if voice not in AVAILABLE_VOICES:
            logger.warning(f"Unknown voice '{voice}', falling back to default")
            voice = DEFAULT_VOICE
        
        try:
            # Generate unique filename
            filename = f"{uuid.uuid4()}.mp3"
            output_path = self.output_dir / filename
            
            # Generate audio
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(str(output_path))
            
            logger.info(f"✅ Generated audio: {filename} (voice={voice})")
            
            # Return URL path (served via /static)
            return f"/static/audio/{filename}"
            
        except Exception as e:
            logger.error(f"TTS generation failed: {e}", exc_info=True)
            return None

    async def get_available_voices(self) -> list:
        """Get list of available voices."""
        return AVAILABLE_VOICES

    def cleanup_old_files(self, max_age_hours: int = 24) -> int:
        """
        Remove old audio files to free up disk space.
        
        Args:
            max_age_hours: Maximum age of files to keep
            
        Returns:
            Number of files deleted
        """
        import time
        
        deleted_count = 0
        max_age_seconds = max_age_hours * 3600
        current_time = time.time()
        
        try:
            for file_path in self.output_dir.glob("*.mp3"):
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    file_path.unlink()
                    deleted_count += 1
            
            if deleted_count > 0:
                logger.info(f"🧹 Cleaned up {deleted_count} old audio files")
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        
        return deleted_count


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

tts_service = EdgeTTSService()
