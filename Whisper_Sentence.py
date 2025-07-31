import whisper
import sounddevice as sd
import numpy as np
from pythonosc.udp_client import SimpleUDPClient
import time
import threading


# Configuración OSC
OSC_IP = "10.22.20.93"
OSC_PORT = 10001
osc_client = SimpleUDPClient(OSC_IP, OSC_PORT)

# Configuración de audio
SAMPLE_RATE = 16000
CHANNELS = 1
BLOCK_DURATION = 0.5  # segundos
SILENCE_THRESHOLD = 0.01  # ajusta este valor si hay falsos positivos

# Cargar modelo Whisper con GPU si está disponible
import torch

device = "cuda" if torch.cuda.is_available() else "cpu"
model = whisper.load_model("base", device=device)
print(f"🧠 Whisper cargado en {device}")
print(f"📦 Modelo cargado en: {next(model.parameters()).device}")

# Variables de control
buffer = []
last_voice_time = time.time()
silence_timeout = 1.0  # seg. sin voz = se considera pausa

def rms(audio_block):
    return np.sqrt(np.mean(audio_block**2))

def callback(indata, frames, time_info, status):
    global buffer, last_voice_time

    if status:
        print(f"⚠️ {status}")

    volume = rms(indata)
    if volume > SILENCE_THRESHOLD:
        buffer.append(indata.copy())
        last_voice_time = time.time()

def audio_loop():
    global buffer
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS,
                        blocksize=int(SAMPLE_RATE * BLOCK_DURATION),
                        callback=callback):
        print("🎙️ Listening... speak and pause to transcribe")
        while True:
            now = time.time()
            if buffer and (now - last_voice_time) > silence_timeout:
                audio_data = np.concatenate(buffer, axis=0).flatten()
                buffer = []

                print("📝 Transcribing...")
                try:
                    # dentro de audio_loop()
                    audio_tensor = torch.from_numpy(audio_data).to(device)
                    result = model.transcribe(audio_tensor, language="en")
                    #result = model.transcribe(audio_data, language="en")
                    text = result["text"].strip()
                    if text:
                        print(f"✅ Text: {text}")
                        osc_client.send_message("/texto", text)
                except Exception as e:
                    print(f"❌ Error al transcribir: {e}")

            time.sleep(0.1)

if __name__ == "__main__":
    audio_loop()
