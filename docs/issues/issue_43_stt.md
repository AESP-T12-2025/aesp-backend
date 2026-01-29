# Issue #43: Real-time Speech-to-Text (STT) Integration

## 📋 Description
Implement real-time Speech-to-Text functionality to enable live pronunciation feedback for learners.

## 🎯 Requirements
- **REQ-LEARNER-15**: Real-time pronunciation practice with AI
- Integrate with a speech recognition service (Google Cloud STT, Azure, or Whisper)
- Support common audio formats: WAV, MP3, WebM, OGG
- Low latency response (< 2 seconds for short clips)

## 📌 Acceptance Criteria
- [ ] `POST /ai/stt` endpoint accepts audio data (base64 or file upload)
- [ ] Returns transcription with confidence score
- [ ] Supports multiple audio formats
- [ ] Integrates with speaking sessions for feedback
- [ ] Error handling for invalid/unsupported audio

## 🔧 Technical Details
```python
# Expected Request
POST /ai/stt
{
    "audio_data": "base64_encoded_audio",
    "format": "wav",
    "sample_rate": 16000,
    "session_id": 123  # optional
}

# Expected Response
{
    "text": "Hello, how are you?",
    "confidence": 0.95,
    "words": [
        {"word": "Hello", "start": 0.0, "end": 0.5, "confidence": 0.98}
    ],
    "pronunciation_score": 85
}
```

## 🧪 Tests
Tests are prepared in: `tests/unit/test_issue_43_speech_to_text.py`

## 📊 Priority
🔴 **Critical** - Required for core pronunciation practice feature

## 🏷️ Labels
`enhancement`, `backend`, `ai`, `priority-high`
