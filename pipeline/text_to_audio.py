# pilot_tts.py
import torch
from transformers import CsmForConditionalGeneration, AutoProcessor
import librosa
import numpy as np

class PilotTTS:
    def __init__(self, model_id="sesame/csm-1b", device="cuda", sample_rate=24000):
        """
        Initialize the Sesame CSM TTS model.

        Args:
            model_id (str): Hugging Face model name.
            device (str): "cuda" or "cpu".
            sample_rate (int): Output audio sample rate.
        """
        self.device = device
        self.sample_rate = sample_rate

        # Load processor and model
        self.processor = AutoProcessor.from_pretrained(model_id)
        self.model = CsmForConditionalGeneration.from_pretrained(model_id, device_map=self.device)
        print(f"[PilotTTS] Init Ok! Device: {self.device}")

    def synthesize(self, text, voice_id=0, speed=1.2, save_path=None):
        """
        Generate speech from text.

        Args:
            text (str): Input text.
            voice_id (int): Speaker/voice selection (0-based ID).
            save_path (str): Path to save WAV file (optional).

        Returns:
            audio (numpy.ndarray), sample_rate (int)
        """
        # Add speaker ID prefix
        speaker_text = f"[{voice_id}]{text}"

        # Prepare conversation input
        conversation = [
            {"role": str(voice_id), "content": [{"type": "text", "text": text}]}
        ]
        inputs = self.processor.apply_chat_template(
            conversation,
            tokenize=True,
            return_dict=True
        ).to(self.device)

        # Generate audio
        audio = self.model.generate(**inputs, output_audio=True, max_new_tokens=2000)

        # Move to CPU and convert to numpy float32
        audio_float = audio[0].cpu().numpy().astype(np.float32)

        # Post-process: speed up
        if speed != 1.0:
            audio_float = librosa.effects.time_stretch(audio_float, rate=speed)

        # Save if path given
        self.processor.save_audio(audio_float, save_path)
        print(f"[PilotTTS] Audio saved to {save_path}")

        return audio


if __name__ == "__main__":
    tts = PilotTTS(device="cuda")
    text = "Finnair522 turn left heading 250 decent to flight level 360"
    audio = tts.synthesize(text, voice_id=1, save_path="demo/input/atc2.wav")
