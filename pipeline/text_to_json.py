# atc_llm.py
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import json
import os
import logging
import re
import time

class ATCAssistantLLM:
    """
    LLM wrapper for ATC tasks:
    - Converting ATC messages to structured JSON commands.
    - Generating pilot response text.
    """
    def __init__(self, logger, model_name="google/gemma-3-4b-it", device="cuda"):
        self.logger = logger
        self.device = device
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name).to(self.device)
        self.logger.info(f"[Generate-JSON] Init Ok! Device: {self.device}")

    def generate_json(self, atc_text, json_path=None, max_new_tokens=128):
        """
        Convert ATC command to structured JSON
        """

        start_time = time.time()

        # Define prompts
        system_prompt = """
        You are an ATC (Air Traffic Control) parser. The text provided is an ATC controller-to-pilot message. 
        The text may contain spelling and grammar mistakes, which you need to correct. 
        Convert the message into a structured JSON format without including any explanations. 

        Follow these rules:
        - The 'icao_callsign' and 'callsign' are REQUIRED. If the callsign contains spelling mistakes, select the closest possible ICAO callsign.
        - Optional fields include: 'heading', 'turn_direction', 'to_altitude', 'rate_of_climb', 'vertical_movement', 'speed', 'speed_movement'.
        - 'vertical_movement' must be either 'climb' or 'descent' if indicated in the text.
        - If a turn is mentioned, 'turn_direction' must be either 'left' or 'right'.
        - If a speed change is mentioned, include 'speed' (numeric value with units) and 'speed_movement' ('increase' or 'reduce').
        - Return ONLY valid JSON. Do not add any extra text or commentary.

        Example:
        Text: ***Finnair522 turn left heading 250 descent to 3000 feet reduce speed to 220 knots***
        JSON:
        {
        "callsign": "Finnair522",
        "turn_direction": "left",
        "heading": 250,
        "to_altitude": "3000ft",
        "vertical_movement": "descent",
        "speed": "220kts",
        "speed_movement": "reduce"
        }
        """
        self.logger.info(f"[Generate-JSON] Input text: '{atc_text}'")

        user_prompt = f"Convert the following ATC message to JSON: {atc_text}"
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # Tokenize
        inputs = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(self.model.device)

        # Convert to JSON
        outputs = self.model.generate(**inputs, max_new_tokens=max_new_tokens)
        generated_text = self.tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:])

        # Clean output
        match = re.search(r"\{.*\}", generated_text, re.DOTALL)
        if match:
            json_text = match.group(0)
            try:
                parsed = json.loads(json_text)
            except json.JSONDecodeError:
                parsed = json_text
        else:
            parsed = generated_text

        # Save JSON for later use
        if json_path is not None:
            os.makedirs(os.path.dirname(json_path), exist_ok=True)
            with open(json_path, "w") as f:
                json.dump(parsed, f, indent=4)
            self.logger.info(f"[Generate-JSON] JSON saved to {json_path}")

        # Log result JSON and elapsed time
        elapsed = time.time() - start_time
        self.logger.info(f"[Generate-JSON] Generated JSON '({elapsed:.2f}s)': {json.dumps(parsed, indent=4, ensure_ascii=False)}")

        return parsed


if __name__ == "__main__":
    # Manual test: run with `python3 pipeline/llm.py`
    atc_command = "DLH5 Climb and maintain FL350, heading 270"

    # Init logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        filename="demo/output/llm.log"
    )
    logger = logging.getLogger("Generate-JSON-Test")

    # Initialize LLM assistant
    llm = ATCAssistantLLM(logger)

    # Generate JSON from text command
    command_json = llm.generate_json(atc_command)

    # Pretty-print JSON
    print(f"\nATC command: {atc_command}")
    print("Generated JSON:")
    print(json.dumps(command_json, indent=4))