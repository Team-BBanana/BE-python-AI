from fastapi import WebSocket, WebSocketDisconnect
from services.audio_service import AudioService
from services.chat_service import ChatService
from typing import Dict, Set
import logging
import re
import base64
from PIL import Image
from io import BytesIO

logger = logging.getLogger(__name__)

class ChatWebSocket:
    def __init__(self):
        self.audio_service = AudioService()
        self.active_connections: Dict[WebSocket, ChatService] = {}
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[websocket] = ChatService()
        logger.info(f"Client connected. Active connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            del self.active_connections[websocket]
        logger.info(f"Client disconnected. Active connections: {len(self.active_connections)}")
    
    @staticmethod
    def split_into_sentences(text: str) -> list[str]:
        """텍스트를 문장 단위로 분리"""
        sentences = re.split(r'([.!?。]+)\s*', text)
        result = []
        
        for i in range(0, len(sentences)-1, 2):
            if i+1 < len(sentences):
                result.append(sentences[i] + sentences[i+1])
            else:
                result.append(sentences[i])
                
        return [s.strip() for s in result if s.strip()]
    
    async def handle_connection(self, websocket: WebSocket):
        await self.connect(websocket)
        
        try:
            while True:
                try:
                    # 메시지 수신
                    data = await websocket.receive()
                    
                    if "bytes" in data:  # 음성 데이터
                        audio_data = data["bytes"]
                        text = await self.audio_service.transcribe_audio(audio_data)
                        
                        if websocket.client_state.CONNECTED:  # 연결 상태 확인
                            await websocket.send_json({"text": text, "isUser": True})
                        
                        chat_service = self.active_connections[websocket]
                        async for sentence in chat_service.generate_response_stream(text):
                            if websocket.client_state.CONNECTED:
                                await websocket.send_json({
                                    "text": sentence,
                                    "isUser": False,
                                    "isPartial": False
                                })
                                
                                speech = await self.audio_service.text_to_speech(sentence)
                                await websocket.send_bytes(speech)
                            
                    elif "text" in data:  # 이미지 데이터
                        image_data = data["text"]
                        if image_data.startswith('data:image'):
                            chat_service = self.active_connections[websocket]
                            feedback = await chat_service.analyze_image(image_data)
                            
                            if websocket.client_state.CONNECTED:
                                # 피드백을 문장 단위로 분리하여 전송
                                sentences = self.split_into_sentences(feedback)
                                for sentence in sentences:
                                    await websocket.send_json({
                                        "text": sentence,
                                        "isUser": False,
                                        "isPartial": False
                                    })
                                    
                                    speech = await self.audio_service.text_to_speech(sentence)
                                    await websocket.send_bytes(speech)
                
                except WebSocketDisconnect:
                    logger.info("WebSocket disconnected")
                    break
                except Exception as e:
                    logger.error(f"Error in handle_connection: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                    if websocket.client_state.CONNECTED:
                        await websocket.send_json({
                            "error": "처리 중 오류가 발생했습니다.",
                            "details": str(e)
                        })
                    break
        finally:
            self.disconnect(websocket) 