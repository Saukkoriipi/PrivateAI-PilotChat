import torch
import soundfile as sf
import torchaudio.functional as F
from transformers import WhisperProcessor, WhisperForConditionalGeneration
import time

class WhisperASR:
    def __init__(self, model_name="openai/whisper-small", device="cuda"):
        """
        Initialize Whisper ASR model and processor.
        """
        self.device = device
        self.processor = WhisperProcessor.from_pretrained(model_name)
        self.model = WhisperForConditionalGeneration.from_pretrained(model_name).to(self.device)
        print(f"[WhisperASR] Init Ok! Device: {self.device}")

    def transcribe(self, file_path):
        """
        Transcribe a WAV audio file.
        Returns transcription string and elapsed time in seconds.
        """
        start_time = time.time()

        # Load audio
        audio, sr = sf.read(file_path)
        audio = torch.tensor(audio).float()

        # Convert to mono
        if len(audio.shape) > 1:
            audio = audio.mean(dim=1)

        # Resample if needed
        if sr != 16000:
            audio = F.resample(audio, orig_freq=sr, new_freq=16000)

        # Prepare input for Whisper
        input_features = self.processor(audio, sampling_rate=16000, return_tensors="pt").input_features.to(self.device)

        # Generate transcription
        predicted_ids = self.model.generate(input_features)
        transcription = self.processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]

        print("[ASR] Transcription:", transcription)
        print(f"[TIMER] Elapsed time: {time.time() - start_time:.2f} seconds")
        return transcription


if __name__ == "__main__":
    # Unit test
    audio_file = "demo/atc_command.wav"

    # Initialize model
    asr = WhisperASR(model_name="openai/whisper-small")

    # Run transcription
    transcription = asr.transcribe(audio_file)

