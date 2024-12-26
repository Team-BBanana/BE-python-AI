export class AudioHandler {
    constructor() {
        this.mediaRecorder = null;
        this.isRecording = false;
    }
    
    async startRecording(onDataAvailable) {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        this.mediaRecorder = new MediaRecorder(stream);
        
        this.mediaRecorder.ondataavailable = onDataAvailable;
        this.mediaRecorder.start();
        this.isRecording = true;
    }
    
    stopRecording() {
        if (this.mediaRecorder) {
            this.mediaRecorder.stop();
            this.isRecording = false;
        }
    }
} 