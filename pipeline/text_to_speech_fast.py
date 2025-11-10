import torch
import time
import logging
import numpy as np
import scipy.io.wavfile
from transformers import VitsModel, AutoTokenizer
from scipy.signal import resample


class MMSTTS:
    def __init__(self, model_name="facebook/mms-tts-eng", device="cuda", logger=None):
        # Define device and speed_factor
        self.device = torch.device(device)
        self.speed_factor = 1.15

        # Logger setup
        if logger:
            self.logger = logger
        else:
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger("MMSTTS")

        # Load model and tokenizer
        self.model = VitsModel.from_pretrained(model_name).to(self.device)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

        self.logger.info(f"[Text-to-speech-fast] '{model_name}' init ok! Device '{self.device}'")

    def _adjust_speed(self, waveform: np.ndarray) -> np.ndarray:
        """Adjust playback speed (resample, pitch not preserved)."""
        if self.speed_factor <= 0:
            raise ValueError("Speed factor must be > 0")

        sr = self.model.config.sampling_rate
        original_len_s = len(waveform) / sr

        num_samples = int(len(waveform) / self.speed_factor)
        waveform_fast = resample(waveform, num_samples)

        new_len_s = len(waveform_fast) / sr

        self.logger.info(
            f"[Text-to-speech-fast] Applied speed factor '{self.speed_factor:.2f}' — 'duration {original_len_s:.2f}s → {new_len_s:.2f}s'"
        )

        return waveform_fast

    def synthesize(self, text: str, description: str):
        """Generate waveform from text with timing."""
        start_time = time.time()

        # Generate audio from text
        inputs = self.tokenizer(text, return_tensors="pt").to(self.device)
        with torch.no_grad():
            waveform = self.model(**inputs).waveform.squeeze(0).cpu().numpy()

        # Make speaking faster. Default is too slow.
        if self.speed_factor > 1:
            waveform = self._adjust_speed(waveform)

        # Log time
        self.inference_time = time.time() - start_time
        self.logger.info(f"[Text-to-speech-fast] Audio generated '({self.inference_time:.2f}s)' for '{text}'")

        return waveform

    def save(self, waveform: np.ndarray, filename="output.wav"):
        """Save waveform to a WAV file."""
        wave_int16 = (waveform * 32767).astype(np.int16)
        scipy.io.wavfile.write(filename, rate=self.model.config.sampling_rate, data=wave_int16)
        self.logger.info(f"[Text-to-speech-fast] Audio saved: '{filename}'")
        return filename


if __name__ == "__main__":
    """Main execution entry point."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("MMSTTS_Main")

    # User-defined device
    device = "cuda"  # or "cpu"

    tts = MMSTTS(device=device, logger=logger)

    text = "Finnair five five two papa, turn left heading two seven zero, descend to flight level two eight zero."
    speed_factor = 1.15
    filename = "pilot.wav"

    waveform = tts.synthesize(text, speed_factor=speed_factor)
    tts.save(waveform, filename)

    logger.info(f"Run completed. Output: {filename}")