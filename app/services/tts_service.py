import edge_tts
import uuid
import os

class EdgeTTSService:
    def __init__(self):
        self.output_dir = "app/static/audio"
        os.makedirs(self.output_dir, exist_ok=True)

    async def generate_audio(self, text: str, voice: str = "en-US-AriaNeural") -> str:
        """
        Generates an audio file from text using EdgeTTS.
        Returns the relative path to the audio file.
        """
        try:
            filename = f"{uuid.uuid4()}.mp3"
            output_path = os.path.join(self.output_dir, filename)
            
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_path)
            
            # Return URL path (assuming served via /static)
            return f"/static/audio/{filename}"
        except Exception as e:
            print(f"TTS Generation Error: {e}")
            return ""

tts_service = EdgeTTSService()
