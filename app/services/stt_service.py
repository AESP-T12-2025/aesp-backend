"""
STT Service
===========
Provides Speech-to-Text functionality for real-time pronunciation feedback.

Uses Google Cloud Speech-to-Text or falls back to Whisper (OpenAI).
"""
import logging
import base64
import io
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from app.core.config import settings


# =============================================================================
# CONFIGURATION
# =============================================================================

logger = logging.getLogger(__name__)

# Supported audio formats
SUPPORTED_FORMATS = {"wav", "mp3", "webm", "ogg", "flac", "m4a"}

# Get API configuration
STT_PROVIDER = getattr(settings, 'STT_PROVIDER', 'mock')  # mock, google, whisper
GOOGLE_CLOUD_KEY = getattr(settings, 'GOOGLE_CLOUD_API_KEY', None)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class WordTiming:
    """Timing information for a single word."""
    word: str
    start_time: float
    end_time: float
    confidence: float


@dataclass
class TranscriptionResult:
    """Result of speech-to-text transcription."""
    text: str
    confidence: float
    words: List[WordTiming]
    language: str = "en-US"
    duration_seconds: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "text": self.text,
            "confidence": self.confidence,
            "words": [
                {
                    "word": w.word,
                    "start": w.start_time,
                    "end": w.end_time,
                    "confidence": w.confidence
                }
                for w in self.words
            ],
            "language": self.language,
            "duration_seconds": self.duration_seconds
        }


# =============================================================================
# SERVICE CLASS
# =============================================================================

class STTService:
    """
    Speech-to-Text service for transcribing audio to text.
    
    Supports multiple providers:
    - mock: Returns mock transcription (development)
    - google: Google Cloud Speech-to-Text
    - whisper: OpenAI Whisper API
    """
    
    def __init__(self, provider: str = STT_PROVIDER):
        """
        Initialize STT service.
        
        Args:
            provider: STT provider to use (mock, google, whisper)
        """
        self.provider = provider
        self._initialize_provider()
    
    def _initialize_provider(self):
        """Initialize the STT provider based on configuration."""
        if self.provider == "google" and GOOGLE_CLOUD_KEY:
            try:
                # Dynamic import to avoid dependency issues
                from google.cloud import speech
                self.google_client = speech.SpeechClient()
                logger.info("✅ Google Cloud STT initialized")
            except ImportError:
                logger.warning("⚠️ google-cloud-speech not installed, falling back to mock")
                self.provider = "mock"
            except Exception as e:
                logger.error(f"❌ Failed to initialize Google STT: {e}")
                self.provider = "mock"
        else:
            logger.info(f"📢 STT using provider: {self.provider}")
    
    async def transcribe(
        self,
        audio_data: str,
        audio_format: str = "wav",
        sample_rate: int = 16000,
        language: str = "en-US"
    ) -> TranscriptionResult:
        """
        Transcribe audio data to text.
        
        Args:
            audio_data: Base64-encoded audio data
            audio_format: Audio format (wav, mp3, webm, ogg)
            sample_rate: Audio sample rate in Hz
            language: Language code (e.g., en-US)
            
        Returns:
            TranscriptionResult with text and word timings
            
        Raises:
            ValueError: If audio format is not supported
        """
        # Validate format
        if audio_format.lower() not in SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported audio format: {audio_format}")
        
        # Decode base64 audio
        try:
            audio_bytes = base64.b64decode(audio_data)
        except Exception as e:
            logger.error(f"Failed to decode base64 audio: {e}")
            raise ValueError("Invalid base64-encoded audio data")
        
        # Route to provider
        if self.provider == "google":
            return await self._transcribe_google(audio_bytes, audio_format, sample_rate, language)
        elif self.provider == "whisper":
            return await self._transcribe_whisper(audio_bytes, audio_format, language)
        else:
            return await self._transcribe_mock(audio_bytes, language)
    
    async def _transcribe_mock(
        self,
        audio_bytes: bytes,
        language: str
    ) -> TranscriptionResult:
        """
        Mock transcription for development/testing.
        
        Returns a realistic mock response.
        """
        # Estimate duration from audio size (rough approximation)
        duration = len(audio_bytes) / 32000  # ~2 bytes per sample at 16kHz
        
        # Mock response
        mock_text = "Hello, how are you today?"
        mock_words = [
            WordTiming("Hello", 0.0, 0.5, 0.98),
            WordTiming("how", 0.6, 0.8, 0.95),
            WordTiming("are", 0.85, 1.0, 0.97),
            WordTiming("you", 1.05, 1.3, 0.96),
            WordTiming("today", 1.35, 1.8, 0.94),
        ]
        
        logger.info(f"📝 Mock STT: '{mock_text}' ({duration:.1f}s)")
        
        return TranscriptionResult(
            text=mock_text,
            confidence=0.95,
            words=mock_words,
            language=language,
            duration_seconds=duration
        )
    
    async def _transcribe_google(
        self,
        audio_bytes: bytes,
        audio_format: str,
        sample_rate: int,
        language: str
    ) -> TranscriptionResult:
        """
        Transcribe using Google Cloud Speech-to-Text.
        """
        try:
            from google.cloud import speech
            
            # Map format to encoding
            encoding_map = {
                "wav": speech.RecognitionConfig.AudioEncoding.LINEAR16,
                "mp3": speech.RecognitionConfig.AudioEncoding.MP3,
                "flac": speech.RecognitionConfig.AudioEncoding.FLAC,
                "ogg": speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
                "webm": speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            }
            
            encoding = encoding_map.get(audio_format.lower(), speech.RecognitionConfig.AudioEncoding.LINEAR16)
            
            audio = speech.RecognitionAudio(content=audio_bytes)
            config = speech.RecognitionConfig(
                encoding=encoding,
                sample_rate_hertz=sample_rate,
                language_code=language,
                enable_word_time_offsets=True,
                enable_automatic_punctuation=True,
            )
            
            response = self.google_client.recognize(config=config, audio=audio)
            
            # Process results
            if not response.results:
                return TranscriptionResult(text="", confidence=0.0, words=[], language=language)
            
            result = response.results[0]
            alternative = result.alternatives[0]
            
            words = []
            for word_info in alternative.words:
                words.append(WordTiming(
                    word=word_info.word,
                    start_time=word_info.start_time.total_seconds(),
                    end_time=word_info.end_time.total_seconds(),
                    confidence=alternative.confidence
                ))
            
            duration = words[-1].end_time if words else 0.0
            
            return TranscriptionResult(
                text=alternative.transcript,
                confidence=alternative.confidence,
                words=words,
                language=language,
                duration_seconds=duration
            )
            
        except Exception as e:
            logger.error(f"Google STT error: {e}", exc_info=True)
            # Fallback to mock on error
            return await self._transcribe_mock(audio_bytes, language)
    
    async def _transcribe_whisper(
        self,
        audio_bytes: bytes,
        audio_format: str,
        language: str
    ) -> TranscriptionResult:
        """
        Transcribe using OpenAI Whisper API.
        """
        try:
            import openai
            
            # Create file-like object from bytes
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = f"audio.{audio_format}"
            
            response = openai.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language.split("-")[0],  # Use just the language code
                response_format="verbose_json",
                timestamp_granularities=["word"]
            )
            
            words = []
            for word_info in response.words or []:
                words.append(WordTiming(
                    word=word_info.word,
                    start_time=word_info.start,
                    end_time=word_info.end,
                    confidence=0.9  # Whisper doesn't provide per-word confidence
                ))
            
            duration = response.duration or (words[-1].end_time if words else 0.0)
            
            return TranscriptionResult(
                text=response.text,
                confidence=0.9,
                words=words,
                language=language,
                duration_seconds=duration
            )
            
        except Exception as e:
            logger.error(f"Whisper STT error: {e}", exc_info=True)
            return await self._transcribe_mock(audio_bytes, language)
    
    def get_supported_formats(self) -> List[str]:
        """Return list of supported audio formats."""
        return list(SUPPORTED_FORMATS)


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

stt_service = STTService()
