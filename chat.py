#!/usr/bin/env python3
"""
Interactive ATC-to-Pilot Chat using pipeline/pipeline.py
Records ATC commands manually (start/stop) and plays pilot readback.
"""

import os
import tempfile
import threading
import numpy as np
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

        # Recording state
        self.recording = False
        self.audio_buffer = []


    def _callback(self, indata, frames, time, status):
        if self.recording:
            self.audio_buffer.append(indata.copy())


    def record_audio_manual(self, fs=24000):
        """Record audio manually until user presses Enter to stop."""
        self.audio_buffer = []
        self.recording = True

        self.logger.info("Recording started. Press Enter to stop...")
        with sd.InputStream(samplerate=fs, channels=1, callback=self._callback):
            input()  # Wait for user to press Enter
        self.recording = False
        self.logger.info("Recording stopped.")

        # Concatenate buffer to single array
        audio = np.concatenate(self.audio_buffer, axis=0).squeeze()
        return audio


    def run(self):
        """Interactive loop: manual recording → run pipeline → play pilot response."""
        try:
            while True:
                cmd = input(
                    "Press Enter to start recording ATC command (or type 'q' to quit): "
                )
                if cmd.lower() == 'q':
                    self.logger.info("Exiting ATC-to-Pilot Chat.")
                    break

                # Record audio manually
                atc_command = self.record_audio_manual()

                # Save temporary WAV file
                tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                sf.write(tmp_file.name, atc_command, 24000)
                self.logger.info(f"[Recorder] Saved temporary atc_command to {tmp_file.name}")

                # Run pipeline
                pilot_answer, samplerate = self.pipeline.run(tmp_file.name, sample_id="temp")

                # Play the pilot speech immediately at correct samplerate
                self.logger.info("[TTS] Playing pilot response...")
                sd.play(pilot_answer, samplerate=samplerate)
                sd.wait()
                self.logger.info("[TTS] Playback finished.")

        except KeyboardInterrupt:
            self.logger.info("Exiting ATC-to-Pilot Chat.")


if __name__ == "__main__":
    chat = ATCtoPilotChat(results_folder="demo/output", device="cpu")
    chat.run()
