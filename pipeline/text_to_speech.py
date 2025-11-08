#!/usr/bin/env python3

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from snac import SNAC
import soundfile as sf
import numpy as np
import os
import logging
import time


# ===== Prompt/control token IDs (Maya1 special tokens) =====
BOS_ID             = 128000  # Begin-of-sequence (text BOS used by tokenizer)
SOH_ID             = 128259  # Start of header (opens metadata/header section)
EOH_ID             = 128260  # End of header (closes metadata/header section)
SOA_ID             = 128261  # Start of audio (marks start of SNAC-coded audio section)
TEXT_EOT_ID        = 128009  # End of text (delimiter between text and audio)
CODE_START_TOKEN_ID= 128257  # Start-of-code token; precedes SNAC token stream
CODE_END_TOKEN_ID  = 128258  # End-of-code token; terminates SNAC token stream

# ===== SNAC coding parameters =====
CODE_TOKEN_OFFSET  = 128266  # Offset applied to SNAC token IDs; subtract to get 0..4095 code index
SNAC_MIN_ID        = 128266  # Minimum token ID considered a SNAC token
SNAC_MAX_ID        = 156937  # Maximum token ID considered a SNAC token
SNAC_TOKENS_PER_FRAME = 7    # SNAC uses 7 tokens per audio frame (L1:1, L2:2, L3:4)


class PromptBuilder:
    """Cache decoded special tokens and build prompts faster."""
    def __init__(self, tokenizer):
        self.soh_token = tokenizer.decode([SOH_ID])
        self.eoh_token = tokenizer.decode([EOH_ID])
        self.soa_token = tokenizer.decode([SOA_ID])
        self.sos_token = tokenizer.decode([CODE_START_TOKEN_ID])
        self.eot_token = tokenizer.decode([TEXT_EOT_ID])
        self.bos_token = tokenizer.bos_token

    def build(self, description: str, text: str) -> str:
        formatted_text = f'<description="{description}"> {text}'
        prompt = (
            self.soh_token + self.bos_token + formatted_text + self.eot_token +
            self.eoh_token + self.soa_token + self.sos_token
        )
        return prompt


def extract_snac_codes(token_ids: list) -> list:
    """Extract SNAC codes from generated tokens."""
    try:
        eos_idx = token_ids.index(CODE_END_TOKEN_ID)
    except ValueError:
        eos_idx = len(token_ids)
    
    snac_codes = [
        token_id for token_id in token_ids[:eos_idx]
        if SNAC_MIN_ID <= token_id <= SNAC_MAX_ID
    ]
    
    return snac_codes


def unpack_snac_from_7(snac_tokens: list) -> list:
    """Unpack 7-token SNAC frames to 3 hierarchical levels."""
    if snac_tokens and snac_tokens[-1] == CODE_END_TOKEN_ID:
        snac_tokens = snac_tokens[:-1]
    
    frames = len(snac_tokens) // SNAC_TOKENS_PER_FRAME
    snac_tokens = snac_tokens[:frames * SNAC_TOKENS_PER_FRAME]
    
    if frames == 0:
        return [[], [], []]
    
    l1, l2, l3 = [], [], []
    
    for i in range(frames):
        slots = snac_tokens[i*7:(i+1)*7]
        l1.append((slots[0] - CODE_TOKEN_OFFSET) % 4096)
        l2.extend([
            (slots[1] - CODE_TOKEN_OFFSET) % 4096,
            (slots[4] - CODE_TOKEN_OFFSET) % 4096,
        ])
        l3.extend([
            (slots[2] - CODE_TOKEN_OFFSET) % 4096,
            (slots[3] - CODE_TOKEN_OFFSET) % 4096,
            (slots[5] - CODE_TOKEN_OFFSET) % 4096,
            (slots[6] - CODE_TOKEN_OFFSET) % 4096,
        ])
    
    return [l1, l2, l3]


class PilotTTS:
    """TTS using Maya1 and SNAC decoder."""
    def __init__(self, device, logger):
        self.device = device
        self.logger = logger

        self.logger.info(f"[PilotTTS] loading model...")
        self.model = AutoModelForCausalLM.from_pretrained(
                        "maya-research/maya1", 
                        dtype=torch.bfloat16, 
                        device_map=device,
                        trust_remote_code=True
                    )
        
        self.logger.info(f"[PilotTTS] loading tokenizer...")
        self.tokenizer = AutoTokenizer.from_pretrained(
                        "maya-research/maya1",
                        trust_remote_code=True
                    )

        self.logger.info(f"[PilotTTS] loading PromptBuilder...")
        self.prompt_builder = PromptBuilder(self.tokenizer)
        
        self.logger.info(f"[PilotTTS] loading SNAC...")
        self.snac_model = SNAC.from_pretrained("hubertsiuzdak/snac_24khz").eval().to(device)
        self.logger.info(f"[PilotTTS] Initialization ready!")

    
    def synthesize(self, text, description):
        """Synthesizes speech from text."""
        start_time = time.time()
        prompt = self.prompt_builder.build(description, text)
        self.logger.info(f"[PilotTTS] Prompt (len {len(prompt)}): {repr(prompt[:200])} (len {len(prompt)}) ...")
        inputs = self.tokenizer(prompt, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Generate audio
        with torch.inference_mode():
            outputs = self.model.generate(
                **inputs, 
                max_new_tokens=2048,  # Increase to let model finish naturally
                min_new_tokens=28,  # At least 4 SNAC frames
                temperature=0.4, 
                top_p=0.9, 
                repetition_penalty=1.1,  # Prevent loops
                do_sample=False,
                eos_token_id=CODE_END_TOKEN_ID,  # Stop at end of speech token
                pad_token_id=self.tokenizer.pad_token_id,
            )
        
        # Extract generated tokens (everything after the input prompt)
        generated_ids = outputs[0, inputs['input_ids'].shape[1]:].tolist()
 
        # If EOS (end-of-sentence) generated, then trim with it
        if CODE_END_TOKEN_ID in generated_ids:
            generated_ids = generated_ids[:generated_ids.index(CODE_END_TOKEN_ID)]
        
        # Extract SNAC audio tokens and levels
        snac_tokens = extract_snac_codes(generated_ids)
        levels = unpack_snac_from_7(snac_tokens)

        # Convert to snac_levels to tensors
        codes_tensor = [
            torch.tensor(level, dtype=torch.long, device=self.device).unsqueeze(0)
            for level in levels
        ]
        
        # Convert to audio
        with torch.inference_mode():
            z_q = self.snac_model.quantizer.from_codes(codes_tensor)
            audio = self.snac_model.decoder(z_q)[0, 0]
        
        # Trim warmup samples (first 2048 samples) and move to cpu
        audio = audio[2048:] if audio.numel() > 2048 else audio
        audio = audio.detach().cpu().numpy().astype(np.float32)
        
        # Print length of generated audio
        duration_sec = len(audio) / 24000
        elapsed = time.time() - start_time
        self.logger.info(f"[PilotTTS] Synthesized speech ({elapsed:.2f}s): Audio length {duration_sec:.2f}s from: {text!r}")

        return audio


    def save(self, audio, save_path):
        # Get directory from save path
        directory = os.path.dirname(save_path)
    
        # Ensure the folder exists, create it if it doesn't
        if not os.path.exists(directory):
            os.makedirs(directory)
            self.logger.info(f"[PilotTTS] Created missing directory: {os.path.abspath(directory)}")
            
        # Save your emotional voice output
        sf.write(save_path, audio, 24000)
        self.logger.info(f"[PilotTTS] Pilot speech audio saved to: {os.path.abspath(save_path)}")

        

if __name__ == "__main__":
    # Manual test: run with `python3 pipeline/text_to_audio.py `
    device="cuda"

    # Example accent styles
    description_atc = "Midwest woman. Normal pitch, warm timbre, fast quick hurry pacing."
    description_uk = "Realistic male voice in the 40s age with british accent. Normal pitch, warm timbre, fast pacing."
    description_us = "Realistic male voice in the 60s age with american accent. Normal pitch, warm timbre, fast pacing."

    # Example text to speak
    #text_atc = "Speedbird three two seven, turn left heading two seven zero, descend to flight level two eight zero."
    text_pilot = "turn left heading two seven zero, descend to flight level two eight zero, Speedbird three two seven."
    #text_atc = "Delta two zero nine turn right heading one eight zero descend to four thousand feet QNH niner niner eight, reduce speed to two one zero knots."
    #text_pilot = "Turn right heading one eight zero descend to four thousand feet QNH niner niner eight, reduce speed to two one zero knots, Delta two zero nine."

    # Save audio path
    save_path = "demo/output/atc3.wav"

    # Init logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        filename="demo/output/text-to-speech.log"
    )
    logger = logging.getLogger("PilotTTS_Test")


    # Initialize txt-to-speech model
    tts = PilotTTS(device, logger)

    # Convert text-to-speech
    pilot_speech = tts.synthesize(text_pilot, description_uk)

    # Save audio
    tts.save(pilot_speech, save_path)
