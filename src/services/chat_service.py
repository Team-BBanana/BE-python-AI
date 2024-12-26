from openai import AsyncOpenAI
from core.config import get_settings
from typing import List, Dict, AsyncGenerator
import asyncio
import logging

logger = logging.getLogger(__name__)
settings = get_settings()
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

class ChatService:
    def __init__(self):
        self.system_prompt = """
        당신은 3~7세 아이들의 둘도 없는 친구입니다.
        어린 아이의 시각에서 자연스럽게 어울리고 대화할 수 있습니다.
        반말을 쓰며 친구답게 대화합니다.
        
        다음과 같은 특성과 전문성을 가지고 있습니다:
        1. 따뜻하고 공감적인 태도로 아이들의 감정을 섬세하게 인지하고 반응합니다.
        2. 아이의 발달 단계에 맞는 적절한 언어와 표현을 사용합니다. 
        3. 긍정적인 강화와 격려를 통해 아이의 자존감을 높여줍니다.
        4. 감정 코칭 전문가로서 아이의 감정을 인정하고 표현하도록 도와줍니다.
        5. 놀이를 통한 치료적 접근을 활용합니다.
        
        대화 시 반드시 지켜야 할 규칙:
        - 한 번의 응답에서 1-2개의 짧은 문장만 사용하도록 최대한 노력합니다.
        - 아이가 이해하기 쉬운 단순한 단어를 선택합니다.
        - 따뜻하고 친근한 어조를 유지합니다.
        - 아이의 감정을 먼저 인정하고 공감합니다.
        - 긍정적인 피드백을 제공합니다.
        - 답변이 길어질 것 같으면 여러 번의 짧은 대화로 나눕니다.
        """
        
        self.conversation_history: List[Dict] = [
            {"role": "system", "content": self.system_prompt}
        ]
        self.max_history = 10

    async def generate_response_stream(self, text: str) -> AsyncGenerator[str, None]:
        """스트리밍 방식으로 응답 생성"""
        try:
            self.conversation_history.append({"role": "user", "content": text})
            
            if len(self.conversation_history) > self.max_history + 1:
                self.conversation_history = [self.conversation_history[0]] + \
                    self.conversation_history[-(self.max_history):]
            
            stream = await client.chat.completions.create(
                model="gpt-4",
                messages=self.conversation_history,
                temperature=0.7,  # 적당한 창의성 유지
                presence_penalty=0.6,  # 다양한 표현 사용 유도
                frequency_penalty=0.3,  # 반복 표현 감소
                stream=True
            )
            
            current_sentence = ""
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    current_sentence += content
                    
                    # 문장 완성 체크 (마침표, 느낌표, 물음표 등으로 판단)
                    if any(current_sentence.endswith(end) for end in ['.', '!', '?', '。']):
                        yield current_sentence.strip()
                        current_sentence = ""
            
            # 마지막 문장 처리
            if current_sentence.strip():
                yield current_sentence.strip()
            
            # 대화 기록에 AI 응답 추가
            if full_response:
                self.conversation_history.append({
                    "role": "assistant", 
                    "content": " ".join(full_response)
                })
            
        except Exception as e:
            import traceback
            logger.error(f"Error in generate_response_stream: {str(e)}")
            logger.error(traceback.format_exc())
            yield "죄송해요, 지금은 대답하기 어려워요. 다시 말해줄 수 있나요?"

    def reset_conversation(self):
        """대화 기록 초기화"""
        self.conversation_history = [
            {"role": "system", "content": self.system_prompt}
        ]

    async def analyze_image(self, image_data: str) -> str:
        """이미지 분석 및 피드백 생성"""
        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "이 그림에 대해 아이와 대화하듯이 친근하게 피드백해주세요."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_data,
                                    "detail": "auto"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"이미지 분석 중 오류 발생: {str(e)}")
            return "그림을 분석하는데 문제가 생겼어. 다시 한 번 보여줄래?"