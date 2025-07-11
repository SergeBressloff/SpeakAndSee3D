import sounddevice as sd
import numpy as np
import wave
import os
from utils import resource_path

def record_audio(filename=None, duration=5, samplerate=16000):
    if filename is None:
        filename = resource_path("audio/recording.wav")

    audio_dir = os.path.dirname(filename)
    os.makedirs(audio_dir, exist_ok=True)

    print("Recording...")
    audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
    sd.wait()

    with wave.open(filename, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(samplerate)
        wf.writeframes(audio.tobytes())
        
    print("Saved:", filename)
