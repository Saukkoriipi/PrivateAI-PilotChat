import torch
import soundfile as sf
import torchaudio.functional as F
from transformers import WhisperProcessor, WhisperForConditionalGeneration
import time
import logging
import os
from datetime import datetime
import re

class ASR:
    def __init__(self, model_name, device, logger):
        """
        Initialize Whisper ASR model and processor.
        """
        self.logger = logger
        self.device = device
        self.processor = WhisperProcessor.from_pretrained(model_name)
        self.model = WhisperForConditionalGeneration.from_pretrained(model_name).to(self.device)
        self.logger.info(f"[ASR] Init Ok! Device: {self.device}")

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
        inputs = self.processor(audio, sampling_rate=16000, return_tensors="pt")
        input_features = inputs.input_features.to(self.device)

        # Generate transcription
        predicted_ids = self.model.generate(
            input_features,
            language="en",
            task="transcribe",
            max_new_tokens=256
        )
        transcription = self.processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]

        # Clean transcription
        transcription = re.sub(r'[^a-zA-Z0-9\s]', '', transcription).strip().upper()
    
        # Print results
        elapsed = time.time() - start_time
        self.logger.info(f"[ASR] Transcription result '({elapsed:.2f}s)': '{transcription}'")
        print(f"[ASR] Pilot command: '({elapsed:.2f}s)': '{transcription}'")

        return transcription


if __name__ == "__main__":
    # Manual test: run with `python3 pipeline/audio_to_text.py`
    audio_file = "demo/input/atc2.wav"

    # Initialize logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        filename="demo/output/speech_to_text.log"
    )
    logger = logging.getLogger("ASR_Test")

    # Initialize model
    model_name = "openai/whisper-small"
    device = "cuda"
    asr = ASR(model_name=model_name, device=device, logger=logger)

    # Run transcription
    transcription = asr.transcribe(audio_file)

    # Optional console output for verification
    print("Transcription:", transcription)
