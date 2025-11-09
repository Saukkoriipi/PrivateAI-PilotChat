#!/usr/bin/env python3
"""
Interactive ATC-to-Pilot Chat using pipeline/pipeline.py
Records ATC commands and plays pilot readback.
"""

import os
import tempfile
import sounddevice as sd
import soundfile as sf
import logging

from pipeline.pipeline import pipeline

class ATCtoPilotChat:
    def __init__(self, results_folder="demo/output", device="cuda"):
        self.results_folder = results_folder
        os.makedirs(self.results_folder, exist_ok=True)

        # Initialize pipeline
        self.pipeline = pipeline(results_folder, device=device)

        # Set up logger
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )
        self.logger = logging.getLogger("ATCtoPilotChat")

    def record_audio(self, duration=5, fs=24000):
        """Record audio from microphone."""
        self.logger.info(f"[Recorder] Recording {duration}s of ATC command...")
        audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype="float32")
        sd.wait()
        return audio.squeeze()

    def run(self):
        """Interactive loop: record audio → run pipeline → play pilot response."""
        try:
            while True:
                input("Press Enter to start recording ATC command...")
                
                # Record audio
                audio = self.record_audio(duration=5)

                # Save temporary WAV file
                tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                sf.write(tmp_file.name, audio, 24000)
                self.logger.info(f"[Recorder] Saved temporary audio to {tmp_file.name}")

                # Run pipeline
                self.pipeline.run(tmp_file.name, sample_id="temp")

                # Cleanup temp file
                os.unlink(tmp_file.name)
                self.logger.info("[Recorder] Temporary file removed.")

        except KeyboardInterrupt:
            self.logger.info("Exiting ATC-to-Pilot Chat.")


if __name__ == "__main__":
    chat = ATCtoPilotChat(results_folder="demo/output", device="cuda")
    chat.run()
