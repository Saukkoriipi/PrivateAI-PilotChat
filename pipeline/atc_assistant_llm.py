# atc_llm.py
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import json
import os
import re

class ATCAssistantLLM:
    """
    LLM wrapper for ATC tasks:
    - Converting ATC messages to structured JSON commands.
    - Generating pilot response text.
    """
    def __init__(self, model_name="google/gemma-3-4b-it", save_path="example", device="cuda"):
        self.device = device
        self.save_path = save_path
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name).to(self.device)
        print(f"[ATCParserLLM] Init Ok! Device: {self.device}")

    def generate_json(self, atc_text, file_name="command.json", max_new_tokens=128):

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

        # Inference
        outputs = self.model.generate(**inputs, max_new_tokens=max_new_tokens)

        # Decode
        generated_text = self.tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:])

        # Clean
        match = re.search(r"\{.*\}", generated_text, re.DOTALL)
        if match:
            json_text = match.group(0)
            try:
                parsed = json.loads(json_text)
            except json.JSONDecodeError:
                parsed = json_text
        else:
            parsed = generated_text

        # Print JSON data
        if isinstance(parsed, dict):
            print("[ATCParserLLM] JSON Output:")
            print(json.dumps(parsed, indent=4, ensure_ascii=False))
        else:
            # fallback if output is a string
            print("[ATCParserLLM] Raw output:", parsed)

        # Save JSON
        save_file = os.path.join(self.save_path, file_name)
        with open(save_file, "w") as f:
            json.dump(parsed, f, indent=4)
        print(f"[ATCParserLLM] JSON saved to {save_file}")

        return parsed

    def generate_pilot_answer(self, atc_json, max_new_tokens=128):
        """
        Generate a pilot response text based on structured ATC JSON command.
        """

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
        
        print(f"[generate_pilot_answer]: {response_text}")
        return response_text


if __name__ == "__main__":
    llm = ATCAssistantLLM()
    atc_text = "DLH5 Climb and maintain FL350, heading 270"
    
    # Generate JSON
    command_json = llm.generate_json(atc_text)
    print("[ATCParserLLM] JSON Output:", command_json)
    
    # Generate pilot reply
    pilot_reply = llm.generate_pilot_answer(command_json)
    print("[ATCParserLLM] Pilot Reply:", pilot_reply)
