import whisper
import sounddevice as sd
import numpy as np
from pythonosc.udp_client import SimpleUDPClient
import time
import torch

# OSC Config
OSC_IP = "10.22.20.93"
OSC_PORT = 10001
osc_client = SimpleUDPClient(OSC_IP, OSC_PORT)

# Audio Config
SAMPLE_RATE = 16000
CHANNELS = 1
BLOCK_DURATION = 0.5
SILENCE_THRESHOLD = 0.01
SILENCE_TIMEOUT = 1.0  # seg

# Load Whisper model
device = "cuda" if torch.cuda.is_available() else "cpu"
model = whisper.load_model("base", device=device)

# Estado de transcripción
is_activated = False
buffer = []
last_voice_time = time.time()

def rms(audio_block):
    return np.sqrt(np.mean(audio_block**2))

def record_until_pause():
    global buffer, last_voice_time
    buffer = []
    last_voice_time = time.time()
    print("🎙️ Waiting for voice input...")

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS,
                        blocksize=int(SAMPLE_RATE * BLOCK_DURATION),
                        callback=callback):
        while True:
            if buffer and (time.time() - last_voice_time) > SILENCE_TIMEOUT:
                audio_data = np.concatenate(buffer, axis=0).flatten()
                return audio_data
            time.sleep(0.1)

def callback(indata, frames, time_info, status):
    global buffer, last_voice_time
    if status:
        print(f"⚠️ {status}")
    if rms(indata) > SILENCE_THRESHOLD:
        buffer.append(indata.copy())
        last_voice_time = time.time()

def detect_activation():
    print("🟡 Waiting for activation command...")
    while True:
        audio_data = record_until_pause()
        try:
            audio_tensor = torch.from_numpy(audio_data).to(device)
            result = model.transcribe(audio_tensor, language="en")  # usa "es" si el comando está en español ("en" para inglés)
            command = result["text"].strip().lower()
            print(f"🗣️ Detected command: {command}")
            if "activate" in command:
                print("🟢 Transcription enabled.")
                return True
        except Exception as e:
            print(f"❌ Error detecting command: {e}")

def transcribe_once():
    print("🔵 Waiting for a sentence to transcribe...")
    audio_data = record_until_pause()
    try:
        audio_tensor = torch.from_numpy(audio_data).to(device)
        result = model.transcribe(audio_tensor, language="en")
        text = result["text"].strip()
        if text:
            print(f"✅ Transcribed text: {text}")
            osc_client.send_message("/texto", text)
    except Exception as e:
        print(f"❌ Error transcribing: {e}")

if __name__ == "__main__":
    while True:
        if detect_activation():
            transcribe_once()
