from fastapi import FastAPI, WebSocket, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from api.websocket import ChatWebSocket
from core.config import get_settings
from services.audio_service import AudioService
import logging

app = FastAPI()
settings = get_settings()

# 로깅 설정 추가
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 정적 파일과 템플릿 설정
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# WebSocket 핸들러 설정
chat_websocket = ChatWebSocket()

# 메인 페이지 라우트 추가
@app.get("/")
async def get_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket):
    await chat_websocket.handle_connection(websocket)

@app.post("/change-voice/{voice_name}")
async def change_voice(voice_name: str):
    if voice_name not in AudioService.AVAILABLE_VOICES:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid voice. Available voices: {list(AudioService.AVAILABLE_VOICES.keys())}"
        )
    
    for websocket, chat_handler in chat_websocket.active_connections.items():
        chat_handler.audio_service.change_voice(voice_name)
    
    return JSONResponse({
        "message": f"Voice changed to {voice_name}",
        "description": AudioService.AVAILABLE_VOICES[voice_name]
    })

@app.get("/available-voices")
async def get_available_voices():
    return JSONResponse(AudioService.AVAILABLE_VOICES)

# 서버 실행을 위한 코드 추가
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 