from utils import load_audio, play_audio
from audio_to_text import WhisperASR
from atc_assistant_llm import ATCAssistantLLM
from text_to_audio import PilotTTS

def init(output_path, device="cuda"):
    """
    Initialize all models used in the ATC-to-Pilot pipeline.
    Returns a dict with model instances.
    """

    models = {}

    # 1. ATC ASR model
    models["ASR"] = WhisperASR(device=device)

    # 2. Text command to JSON
    # 3. JSON to Pilot Answer
    models["LLM"] = ATCAssistantLLM(device=device, save_path=output_path)

    # 4. TTS model for pilot audio
    models["TTS"] = PilotTTS(device=device)

    return models


def run_pipeline(audio_input, audio_output, models):
    """Execute full ATC-to-Pilot voice interaction."""

    # 1. ATC audio → text
    atc_text = models["ASR"].transcribe(audio_input)

    # 2. ATC text → structured command JSON
    command_json = models["LLM"].generate_json(atc_text)

    # 3. Command JSON → pilot response text
    pilot_text = models["LLM"].generate_pilot_answer(command_json)

    # 4. Play pilot reply audio
    models["TTS"].synthesize(pilot_text, save_path=audio_output)

    # 5. Play pilot audio
    #play_audio(audio_output)


def main():
    """Run the ATC-to-Pilot pipeline in a loop or on a single audio file."""

    output_path = "demo/output"
    audio_input = "demo/input/atc2.wav"
    audio_output = "demo/output/pilot2.wav"

    # Initialize models
    models = init(output_path=output_path)

    # Run pipeline
    run_pipeline(audio_input, audio_output, models)


if __name__ == "__main__":
    main()