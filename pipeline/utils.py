import librosa
import sounddevice as sd
import soundfile as sf
import numpy as np
import os

def load_audio(file_path, target_sr=16000):
    """
    Load an audio file and return a 1D float32 NumPy array suitable for ASR.
    
    Args:
        file_path (str): Path to WAV/MP3/FLAC file.
        target_sr (int): Target sample rate for ASR (default 16 kHz).
        
    Returns:
        np.ndarray: 1D float32 audio array.
    """
    audio, sr = librosa.load(file_path, sr=target_sr, mono=True)  # resample + mono
    audio = audio.astype(np.float32)

    duration_sec = len(audio) / sr
    print(f"[load_audio] Loaded '{file_path}' successfully, duration: {duration_sec:.2f} seconds.")

    return audio

def play_audio(file_path):
    """
    Play a WAV/FLAC audio file from disk.
    
    Args:
        file_path (str): Path to audio file.
    """
    if not os.path.exists(file_path):
        print(f"[play_audio] File does not exist: {file_path}")
        return

    # Load audio as float32
    audio, sr = sf.read(file_path, dtype='float32')

    # If stereo, convert to mono
    if len(audio.shape) > 1:
        audio = audio.mean(axis=1)

    print(f"[play_audio] Playing '{file_path}', duration: {len(audio)/sr:.2f} seconds.")
    sd.play(audio, samplerate=sr)
    sd.wait()  # Wait until finished