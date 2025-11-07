from utils import load_audio, play_audio
from speech_to_text import WhisperASR
from llm import ATCAssistantLLM
from text_to_speech import PilotTTS
import glob
import os
import logging


class pipeline:
    def __init__(self, results_folder, device="cuda"):
        """
        Initialize all models used in the ATC-to-Pilot pipeline.
        Returns a dict with model instances.
        """
        self.results_folder = results_folder
        self.device = device


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

        # Initialize models
        self.asr = WhisperASR(model_name="openai/whisper-small", 
                              device=device, 
                              logger=self.logger
                              )
        self.llm = ATCAssistantLLM(model_name="google/gemma-3-4b-it",
                                   device=device,
                                   logger=self.logger
                                   )
        self.tts = PilotTTS(device=device, 
                            logger=self.logger
                            )

    def run(self, audio_input, sample_id=0):
        self.logger.info(f"[pipeline.run] Start processing: {audio_input}")

        # Define paths where we save all logs and conversions
        json_path = os.path.join(self.results_folder, f"{sample_id}.json")
        audio_path = os.path.join(self.results_folder, f"{sample_id}.wav")

        # 1. ATC audio → text
        atc_text = self.asr.transcribe(audio_input)

        # 2. ATC text → structured command JSON
        command_json = self.llm.generate_json(atc_text, json_path)

        # 3. Command JSON → pilot response text
        pilot_text = self.llm.generate_pilot_answer(command_json)

        # 4. Pilot response to audio
        description = "Realistic female voice in the 20s age with british accent. Normal pitch, warm timbre, fast pacing."
        pilot_speech = self.tts.synthesize(pilot_text, description)
        self.tts.save(pilot_speech, audio_path)
        


if __name__ == "__main__":
    # Define params
    results_folder = "demo/output"
    input_folder = "demo/input"
    device = "cuda"

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