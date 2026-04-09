import pyaudio
import numpy as np
import requests
import json
import threading
from faster_whisper import WhisperModel
from context_engine import ContextEngine

# --- Configuration ---
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
MODEL_SIZE = "base.en" 

class AudioTranscriber:
    def __init__(self):
        print("Loading Whisper Model...")
        self.model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
        
        # --- NEW: Initialize the Brain ---
        self.brain = ContextEngine() 
        
        self.audio = pyaudio.PyAudio()
        self.frames = []
        self.is_recording = False

    def _record_thread(self):
        """This runs in the background to capture audio chunks."""
        stream = self.audio.open(format=FORMAT,
                                 channels=CHANNELS,
                                 rate=RATE,
                                 input=True,
                                 frames_per_buffer=CHUNK)
        
        while self.is_recording:
            data = stream.read(CHUNK)
            self.frames.append(data)
        
        stream.stop_stream()
        stream.close()

    def start_interactive(self):
        """Handles the Enter key presses to start and stop."""
        while True:
            user_input = input("\n[PRESS ENTER] to START recording (or type 'q' to quit): ")
            if user_input.lower() == 'q':
                break
            
            print("🔴 Recording... [PRESS ENTER] to STOP.")
            self.frames = []
            self.is_recording = True
            
            # Start recording in a separate thread so we don't block the Enter key listener
            record_thread = threading.Thread(target=self._record_thread)
            record_thread.start()
            
            # The script pauses here waiting for your second Enter press
            input() 
            self.is_recording = False
            record_thread.join() # Wait for the audio thread to safely close
            
            print("🟢 Recording stopped. Transcribing...")
            if len(self.frames) > 0:
                audio_data = b''.join(self.frames)
                self._transcribe(audio_data)
            else:
                print("No audio captured.")

    def _transcribe(self, audio_data):
        """Converts raw audio, passes to Whisper, then to Llama 3.2."""
        audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        
        segments, info = self.model.transcribe(audio_np, beam_size=5)
        
        # 1. Gather all the transcribed text into one string
        full_transcription = ""
        for segment in segments:
            full_transcription += segment.text + " "
            
        print("-" * 30)
        print(f"[RAW AUDIO TEXT]: {full_transcription.strip()}")
        print("-" * 30)

        # 2. Pass the text to Llama 3.2 to get structured JSON
        if full_transcription.strip():
            print("🧠 Processing with Context Engine...")
            json_result = self.brain.parse_instruction(full_transcription.strip())
            
            if json_result:
                print("\n✅ [STRUCTURED FLIGHT DATA]:")
                print(json_result)
                
                # --- NEW: Send to FastAPI Server ---
                try:
                    parsed_data = json.loads(json_result)
                    response = requests.post("http://localhost:8000/api/telemetry", json=parsed_data)
                    if response.status_code == 200:
                        print("📡 Successfully beamed data to Dashboard API!")
                except Exception as e:
                    print(f"⚠️ Could not send data to API. Is main.py running? (Error: {e})")
                    
            else:
                print("❌ Context Engine failed to parse the instruction.")
                
    def cleanup(self):
        self.audio.terminate()

if __name__ == "__main__":
    transcriber = AudioTranscriber()
    try:
        transcriber.start_interactive()
    except KeyboardInterrupt:
        print("\nForce stopping...")
    finally:
        transcriber.cleanup()