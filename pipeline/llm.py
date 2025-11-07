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
        self.logger.info(f"[ATCParserLLM] Init Ok! Device: {self.device}")

    def generate_json(self, atc_text, json_path, max_new_tokens=128):
        """
        Convert ATC command to structured JSON
        """

        start_time = time.time()

        # Define prompts
        system_prompt = (
            "You are an ATC parser. Text is an ATC controller-to-pilot message. "
            "Convert messages into structured JSON commands. Do NOT include explanations. "
            "Rules:\n"
            "- 'callsign' is REQUIRED. If the callsign contains spelling mistakes, select the closest valid ICAO callsign.\n"
            "- Optional fields: 'heading', 'turn_direction', 'to_altitude', 'rate_of_climb', 'vertical_movement'.\n"
            "- 'vertical_movement' must be 'climb' or 'descent' if indicated in the text.\n"
            "- 'turn_direction' must be 'left' or 'right' if a turn is mentioned.\n"
            "- Return only valid JSON, do not add extra text or commentary."
        )
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

        # Save JSON
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, "w") as f:
            json.dump(parsed, f, indent=4)
        self.logger.info(f"[ATCParserLLM] JSON saved to {json_path}")

        # Log result JSON and elapsed time
        elapsed = time.time() - start_time
        self.logger.info(f"[ATCAssistantLLM] Generate JSON ({elapsed:.2f}s): {json.dumps(parsed, indent=4, ensure_ascii=False)}")

        return parsed

    def generate_pilot_answer(self, atc_json, max_new_tokens=128):
        """
        Generate a pilot response text based on structured ATC JSON command.
        """
        start_time = time.time()

        system_prompt = (
            "You are a pilot receiving ATC commands. "
            "Based on the provided ATC JSON command, generate a concise, natural response the pilot would say. "
            "Convert ICAO callsigns to radio callsigns using the following mapping:\n"
            "- FIN -> Finnair\n"
            "- BAW -> Speedbird\n"
            "- DLH -> Lufthansa\n"
            "- AFR -> Air France\n"
            "- UAL -> United\n"
            "Do NOT include explanations or extra commentary."
        )

        user_prompt = f"ATC command JSON: {json.dumps(atc_json)}"
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        inputs = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(self.model.device)

        outputs = self.model.generate(**inputs, max_new_tokens=max_new_tokens)
        response_text = self.tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:],
                                              skip_special_tokens=True
                                              ).strip()
        
        elapsed = time.time() - start_time
        self.logger.info(f"[ATCAssistantLLM] Pilot reply ({elapsed:.2f}s): {response_text}")
        return response_text


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
    logger = logging.getLogger("ATCAssistantLLM_Test")

    # Initialize LLM assistant
    llm = ATCAssistantLLM(logger)

    # Generate JSON from text commaand
    command_json = llm.generate_json(atc_command)
    
    # Generate pilot reply from JSON
    pilot_reply = llm.generate_pilot_answer(command_json)
