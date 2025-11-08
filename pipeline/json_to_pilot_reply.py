#!/usr/bin/env python3
import time
import logging
import json

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
        Convert digits in a string to ICAO-style spoken words, preserving letters.

        Each digit is replaced with its ICAO phonetic equivalent, while letters and
        other characters remain unchanged. Round-thousand numbers (e.g., "3000") are
        converted to "<digit> thousand".

        Examples:
            "Finnair1"     -> "Finnair WUN"
            "1C"           -> "WUN C"
            "3000"         -> "TREE thousand"
            "Finnair522"   -> "Finnair FIFE TOO TOO"
        """
        digit_map = {
            "0": "ZERO",
            "1": "WUN",
            "2": "TOO",
            "3": "TREE",
            "4": "FOWER",
            "5": "FIFE",
            "6": "SIX",
            "7": "SEVEN",
            "8": "AIT",
            "9": "NINER"
        }

        # Handle pure round-thousands numbers
        if text.isdigit() and text.endswith("000") and len(text) <= 4:
            return f"{digit_map[text[0]]} thousand"

        result = []
        current_chunk = ""

        for c in text:
            if c.isdigit():
                if current_chunk:
                    result.append(current_chunk)
                    current_chunk = ""
                result.append(digit_map[c])
            else:
                current_chunk += c

        if current_chunk:
            result.append(current_chunk)

        return " ".join(result)

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

        # Turn instruction
        if json_data.get("turn_direction") and json_data.get("heading"):
            heading = self.num_to_words(str(json_data["heading"]))
            parts.append(f"TURN {json_data['turn_direction'].upper()} HEADING {heading}")
        elif json_data.get("heading"):
            heading = self.num_to_words(str(json_data["heading"]))
            parts.append(f"FLY HEADING {heading}")

        # Vertical movement
        if json_data.get("vertical_movement") and json_data.get("to_altitude"):
            movement = json_data["vertical_movement"].upper()
            altitude = json_data["to_altitude"].upper().replace("FT", "").replace("FL", "").strip()
            altitude_words = self.num_to_words(altitude)
            if "FL" in json_data["to_altitude"].upper():
                parts.append(f"{movement} TO FLIGHT LEVEL {altitude_words}")
            else:
                parts.append(f"{movement} TO {altitude_words} FEET")

        # Speed control
        if json_data.get("speed_movement") and json_data.get("speed"):
            speed_val = str(json_data["speed"]).replace("kts", "").strip()
            speed_words = self.num_to_words(speed_val)
            parts.append(f"{json_data['speed_movement'].upper()} SPEED TO {speed_words} KNOTS")

        # Add callsign
        callsign = json_data.get("callsign", "").replace(" ", "")
        callsign_string = self.num_to_words(callsign)
        parts.append(callsign_string)

        # Generate response
        response_text = ", ".join(parts).upper()
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
