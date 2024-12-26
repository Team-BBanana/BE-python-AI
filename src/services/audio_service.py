import io
from openai import AsyncOpenAI
from core.config import get_settings

settings = get_settings()
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

class AudioService:
    AVAILABLE_VOICES = {
        'alloy': '중성적이고 균형 잡힌 목소리',
        'echo': '깊이 있고 차분한 목소리',
        'fable': '부드럽고 따뜻한 목소리',
        'onyx': '강력하고 단호한 목소리',
        'nova': '활기차고 친근한 목소리',
        'shimmer': '맑고 밝은 목소리'
    }

    def __init__(self):
        # 아이들을 위한 상담에 적합한 목소리로 설정
        self.current_voice = 'nova'  # 또는 'fable'

    @staticmethod
    async def transcribe_audio(audio_data: bytes) -> str:
        """음성을 텍스트로 변환"""
        audio_file = io.BytesIO(audio_data)
        audio_file.name = "audio.wav"
        
        transcript = await client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="ko"
        )
        return transcript.text
    
    async def text_to_speech(self, text: str) -> bytes:
        """텍스트를 음성으로 변환"""
        response = await client.audio.speech.create(
            model="gpt-4o",
            voice=self.current_voice,  # 설정된 음성 사용
            input=text,
            speed=1.0,
            response_format="mp3",
        )
        return response.content
    
    def change_voice(self, voice_name: str) -> bool:
        """음성 변경"""
        if voice_name in self.AVAILABLE_VOICES:
            self.current_voice = voice_name
            return True
        return False