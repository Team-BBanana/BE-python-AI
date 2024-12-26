import { AudioHandler } from './audio_handler.js';

export class VoiceChat {
    constructor() {
        this.socket = new WebSocket('ws://localhost:8000/chat');
        this.audioHandler = new AudioHandler();
        this.audioQueue = [];
        this.isPlaying = false;
        this.initializeWebSocket();
        this.onMessage = null;
    }
    
    async playNextAudio() {
        if (this.isPlaying || this.audioQueue.length === 0) return;
        
        this.isPlaying = true;
        const audioBlob = this.audioQueue.shift();
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        
        audio.onended = () => {
            this.isPlaying = false;
            URL.revokeObjectURL(audioUrl);
            this.playNextAudio();
        };
        
        try {
            await audio.play();
        } catch (error) {
            console.error('오디오 재생 실패:', error);
            this.isPlaying = false;
            this.playNextAudio();
        }
    }
    
    initializeWebSocket() {
        this.socket.onmessage = async (event) => {
            try {
                if (event.data instanceof Blob) {
                    // 음성 데이터를 큐에 추가하고 재생 시도
                    this.audioQueue.push(event.data);
                    this.playNextAudio();
                } else {
                    const data = JSON.parse(event.data);
                    if (data.text) {
                        // 부분 응답인 경우 임시 메시지로 표시
                        this.onMessage?.(
                            data.text,
                            data.isUser,
                            data.isPartial
                        );
                    }
                }
            } catch (error) {
                console.error('메시지 처리 중 오류:', error);
            }
        };

        this.socket.onerror = (error) => {
            console.error('WebSocket 오류:', error);
        };
    }
    
    async startRecording() {
        await this.audioHandler.startRecording((event) => {
            this.socket.send(event.data);
        });
    }
    
    stopRecording() {
        this.audioHandler.stopRecording();
    }
} 