#!/usr/bin/env python3
import time
import logging
import json
import re

class ATCJsonConverter:
    """
    Convert structured ATC JSON data to ICAO-style pilot readbacks.
    """

    def __init__(self, logger: logging.Logger = None):
        """
        Initialize the converter with a logger.
        If no logger is provided, a default logger is created.
        """
        if logger is None:
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger("ATCJsonConverter")
        else:
            self.logger = logger

        # Log initialization confirmation
        self.logger.info("ATCJsonConverter initialized successfully ✅")


    def num_to_words(self, text: str) -> str:
        """
        Convert numbers in text to ICAO-style spoken words.
        Letters are preserved. Thousands/hundreds are pronounced only if last two digits are zeros.
        """
        print(f"[num_to_words] Input: '{text}'")

        digit_map = {
            "0": " ZERO",
            "1": " WUN",
            "2": " TOO",
            "3": " TREE",
            "4": " FOWER",
            "5": " FIFE",
            "6": " SIX",
            "7": " SEVEN",
            "8": " AIT",
            "9": " NINER"
        }

        def number_to_icao(num_str: str) -> str:
            s = num_str
            words = []

            if len(s) == 4:
                if s[1:] == "000":  # full thousands
                    return f"{digit_map[s[0]]} THOUSAND"
                elif s[2:] == "00":  # thousands + hundreds
                    return f"{digit_map[s[0]]} THOUSAND {digit_map[s[1]]} HUNDRED"

            if len(s) == 3 and s[1:] == "00":  # hundreds only
                return f"{digit_map[s[0]]} HUNDRED"

            # remaining digits (zeros pronounced normally)
            for c in s:
                words.append(digit_map[c])

            return " ".join(words)

        # Replace all numbers with ICAO-style words
        text_out = re.sub(r"\d+", lambda m: number_to_icao(m.group(0)), text)

        # Remove leading/trailing spaces and collapse multiple spaces
        text_out = " ".join(text_out.split())

        print(f"[num_to_words] Output: '{text_out}'")
        return text_out


    def generate_pilot_readback(self, json_data: dict) -> str:
        """
        Generate ICAO-style pilot readback from structured ATC JSON.

        Args:
            json_data (dict): ATC instructions (heading, altitude, speed, turn, callsign).

        Returns:
            str: Pilot readback as a natural ICAO radio message.
        """
        start_time = time.time()
        parts = []

        # --- Cleared direct fix ---
        cleared_direct = json_data.get("cleared_direct")
        if cleared_direct:
            parts.append(f"CLEARED DIRECT {cleared_direct.upper()}")

        # --- Turn and heading instructions ---
        turn_direction = json_data.get("turn_direction")
        heading = json_data.get("heading")
        if heading:
            heading = str(heading).zfill(3)  # Ensure 3 digits, e.g., 90 -> "090"
            if turn_direction:
                parts.append(f"TURN {turn_direction.upper()} HEADING {heading}")
            else:
                parts.append(f"FLY HEADING {heading}")

        # --- Vertical movement and altitude ---
        to_altitude = json_data.get("to_altitude")
        vertical_movement = json_data.get("vertical_movement")
        if to_altitude:
            alt_str = to_altitude.upper()
            altitude_val = alt_str.replace("FT", "").replace("FL", "").strip()
            if vertical_movement:
                # Normal case: climb/descent specified
                movement = vertical_movement.upper()
                if "FL" in alt_str:
                    parts.append(f"{movement} TO FLIGHT LEVEL {altitude_val}")
                else:
                    parts.append(f"{movement} TO {altitude_val} FEET")
            else:
                # Backup case: only altitude given
                if "FL" in alt_str:
                    parts.append(f"TO FLIGHT LEVEL {altitude_val}")
                else:
                    parts.append(f"TO {altitude_val} FEET")
    
        # --- Approach and runway ---
        approach = json_data.get("approach")
        runway = json_data.get("runway")
        if approach and runway:
            if runway:
                # Full instruction with approach type and runway
                parts.append(f"CLEARED {approach.upper()} APPROACH RUNWAY {runway}")
            else:
                # Approach type given, runway missing
                parts.append(f"CONFORM RUNWAY")

        # --- QNH (barometric setting) ---
        qnh = json_data.get("qnh")
        if qnh:
            parts.append(f"QNH {qnh}")

        # --- Speed control instructions ---
        speed_movement = json_data.get("speed_movement")
        speed = json_data.get("speed")

        if speed and speed_movement:
            # Normal case: speed change type specified
            speed_val = str(speed).replace("kts", "").strip()
            parts.append(f"{speed_movement.upper()} SPEED TO {speed_val} KNOTS")
        elif speed:
            # Backup case: only speed given, movement type missing
            speed_val = str(speed).replace("kts", "").strip()
            parts.append(f"SPEED {speed_val} KNOTS")

        # --- Callsign ---
        callsign = json_data.get("callsign", "")
        parts.append(callsign)

        # --- Combine all instructions into the final pilot readback ---
        # Numbers are converted to ICAO-style words so the TTS engine pronounces them correctly
        response_text = ", ".join(parts).upper()
        response_text = self.num_to_words(response_text)
        elapsed = time.time() - start_time
        self.logger.info(f"[JSON-to-PilotReply] Generated pilot readback in {elapsed:.2f}s: {response_text}")

        return response_text



if __name__ == "__main__":
    # Example usage
    converter = ATCJsonConverter()

    example_json = {
        "callsign": "Finnair522",
        "turn_direction": "left",
        "heading": 250,
        "vertical_movement": "descent",
        "to_altitude": "FL360",
        "speed_movement": "reduce",
        "speed": "220kts"
    }

    # Print JSON nicely
    print("Input JSON:")
    print(json.dumps(example_json, indent=4))

    # Convert to pilot readback
    reply = converter.generate_pilot_readback(example_json)
    print("\nPilot Readback:")
    print(reply)
