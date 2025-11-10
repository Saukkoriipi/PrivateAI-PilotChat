from .speech_to_text import ASR
from .text_to_json import ATCTextToJSON
from .text_to_speech import PilotTTS
from .text_to_speech_fast import MMSTTS
from .json_to_pilot_reply import ATCJsonConverter
from .csv_logger import CommandCSVLogger
import glob
import os
import logging
import time


class pipeline:
    def __init__(self, results_folder, device="cpu"):
        """
        Initialize all models used in the ATC-to-Pilot pipeline.
        Returns a dict with model instances.
        """
        self.results_folder = results_folder
        self.device = device
        print(f"[INFO] Using device: {self.device }")
        print(f"[INFO] Save results to: {self.results_folder}")


        # Initialize logger
        log_file = os.path.join(results_folder, "pipeline.log")
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Pipeline initialized")

        # Initialize ATC commands logger
        self.csv_logger = CommandCSVLogger(csv_path=os.path.join(results_folder, "commands_log.csv"),
                                           logger=self.logger)

        # Initialize models for the ATC-to-Pilot pipeline

        # 1. Automatic Speech Recognition (ASR)
        #    Converts ATC spoken commands into text
        self.asr = ASR(model_name="openai/whisper-small", 
                       device=device, 
                       logger=self.logger
                       )
        
        # 2. ATC Text → JSON Parser
        #    Extracts structured ATC instructions (heading, altitude, QNH, etc.) from text.
        self.parser = ATCTextToJSON(logger=self.logger)

        # 3. JSON-to-Pilot response converter
        #    Generates ICAO-style pilot readback from structured ATC JSON
        self.json_to_pilot = ATCJsonConverter(logger=self.logger)

        # 4. Text-to-Speech (TTS) for pilot readback
        #    Converts the pilot response text into audio
        #    Option 1: PilotTTS (slower, supports multiple voices/accents)
        #    Option 2: MMSTTS (faster, single voice)
        #self.tts = PilotTTS(device=device, logger=self.logger)
        self.tts = MMSTTS(device=device, logger=self.logger)

        print("[INFO] ATC-Pilot chat initialization is complete and ready for use.\n")


    def run(self, audio_input, sample_id=0):
        print("*" * 10)
        self.logger.info(f"[pipeline.run] Start processing: {audio_input}")
        start_time = time.time()  # start full pipeline timer

        # Define paths where we save all logs and conversions
        json_path = os.path.join(self.results_folder, f"{sample_id}.json")
        audio_path = os.path.join(self.results_folder, f"{sample_id}.wav")

        # 1. ATC audio → text
        atc_text = self.asr.transcribe(audio_input)

        # 2. ATC text → structured command JSON
        command_json = self.parser.generate_json(atc_text, json_path)

        # 3. Command JSON → pilot response text
        pilot_text = self.json_to_pilot.generate_pilot_readback(command_json)

        # 4. Pilot response to audio
        description = "Realistic female voice in the 20s age with british accent. Normal pitch, warm timbre, fast pacing."
        pilot_speech, samplerate = self.tts.synthesize(pilot_text, description)
        self.tts.save(pilot_speech, audio_path)

        # 5. Log parsed command to CSV
        #    Uses CommandCSVLogger to append the structured JSON to a central CSV log.
        #    Keeps a dataframe in memory for fast access and automatically adds a timestamp.
        #    Saves the CSV after each append, ensuring persistent logging of all commands.
        #    Executed after speech-to-text and JSON parsing, so it does not block the main pipeline.
        self.csv_logger.append(atc_text, command_json)

        # 6. Log total time
        self.logger.info(f"[pipeline.run] Processing ready. Run time: '{(time.time() - start_time):.2f}' seconds")
        print(f"[pipeline.run] Processing ready. Run time: '{(time.time() - start_time):.2f}' seconds")

        return pilot_speech, samplerate


if __name__ == "__main__":
    # Define params
    results_folder = "demo/output"
    input_folder = "demo/input"
    device = "cpu"

    # Initialize pipeline
    pipeline = pipeline(results_folder, device)

    # Loop files in input_folder
    audio_files = glob.glob(os.path.join(input_folder, "*.wav"))
    for audio_input in sorted(audio_files):
        print("* *" * 10)
        sample_id = os.path.splitext(os.path.basename(audio_input))[0]
        print(f"Starting pipeline for {audio_input}...")
        pipeline.run(audio_input, sample_id)
        print("* *" * 10)