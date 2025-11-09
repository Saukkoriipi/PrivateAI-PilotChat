import re
import logging
import time
import json
import os
from airline_matcher import AirlineMatcher

class ATCTextToJSONRegex:
    """Lightweight regex-based ATC text-to-JSON parser."""
    
    def __init__(self, logger: logging.Logger = None, airlines_csv: str = "pipeline/airlines.csv"):
        if logger is None:
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger("ATCTextToJSON")
        else:
            self.logger = logger
        self.logger.info("[ATCTextToJSONRegex] Init Ok!")

        # --- Initialize airline matcher ---
        if not os.path.isfile(airlines_csv):
            raise FileNotFoundError(f"Airlines CSV not found: {airlines_csv}")
        self.airline_matcher = AirlineMatcher(csv_path=airlines_csv, logger=self.logger)
        self.logger.info("[ATCTextToJSONRegex] Airline matcher initialized")


    def generate_json(self, text: str, json_path: str = None) -> dict:
        """
        Parse ATC instruction text into structured JSON using regex rules.

        Example input:
            'DELTA 209 TURN RIGHT HEADING 180 DESCEND TO 4000 FEET QNH 9 OR 9 OR 8 REDUCE SPEED TO 210 KNOTS'

        Example output:
            {
                "callsign": "DELTA209",
                "turn_direction": "right",
                "heading": 180,
                "vertical_movement": "descent",
                "to_altitude": "4000ft",
                "speed_movement": "reduce",
                "speed": "210kts",
                "qnh": "998",
                "cleared_direct": "LAKUT",
                "approach": "ILS",
                "runway": "22"
            }
        """
        start_time = time.time()
        text = text.upper() # Convert to uppercase once       
        result = {}

        # Remove spurious "OR" tokens and normalize whitespace
        # Speech to text commonly translated 9 "niner" as "9 or"
        text = re.sub(r"\bOR\b", "", text)
        # Replace multiple spaces with one and remove leading/trailing spaces
        text = re.sub(r'\s+', ' ', text).strip() 
        # Remove spaces **between digits**
        text = re.sub(r'(?<=\d)\s+(?=\d)', '', text) # 9 9 9 -> 999

        # --- Callsign ---
        m = re.match(r"([A-Z]+)\s?(\d+)", text)
        if m:
            callsign = f"{m.group(1).capitalize()}{m.group(2)}"
            result["icao"], result["callsign"] = self.airline_matcher.match_CALLSIGN(callsign)

        # --- Turn direction and heading ---
        m = re.search(r"TURN\s+(LEFT|RIGHT)", text)
        if m:
            result["turn_direction"] = m.group(1).lower()

        m = re.search(r"HEADING\s+(\d{2,3})", text)
        if m:
            result["heading"] = int(m.group(1))

        # --- Vertical movement ---
        if re.search(r"CLIMB", text):
            result["vertical_movement"] = "climb"
        elif re.search(r"DESCEND|DECENT", text):
            result["vertical_movement"] = "descent"

        # --- Altitude ---
        m = re.search(r"(FLIGHT LEVEL|FL)\s?(\d{2,3})", text)
        if m:
            result["to_altitude"] = f"FL{m.group(2)}"
        else:
            m = re.search(r"(\d{3,5})\s*(FEET|FT)", text)
            if m:
                result["to_altitude"] = f"{m.group(1)}ft"

        # --- Speed ---
        if re.search(r"REDUCE\s+SPEED", text):
            result["speed_movement"] = "reduce"
        elif re.search(r"INCREASE\s+SPEED", text):
            result["speed_movement"] = "increase"

        m = re.search(r"SPEED\s+(?:TO\s+)?(\d{2,3})", text)
        if m:
            result["speed"] = f"{m.group(1)}kts"

        # --- QNH ---
        m = re.search(r"QNH\s*(\d{3,4})", text)
        if m:
            result["qnh"] = m.group(1)

        # --- Cleared direct fix ---
        m = re.search(r"CLEARED\s+DIRECT\s+([A-Z]{3,6})", text)
        if m:
            result["cleared_direct"] = m.group(1)

        # --- Approach and runway ---
        m = re.search(r"CLEARED\s+(ILS|VOR|RNAV)\s+APPROACH\s+(?:RWY|RUNWAY)?\s*(\d{2})", text)
        if m:
            result["approach"] = m.group(1)
            result["runway"] = m.group(2)
        else:
            # Simple runway only case (e.g., CLEARED APPROACH RWY 22)
            m = re.search(r"CLEARED\s+APPROACH\s+(?:RWY|RUNWAY)?\s*(\d{2})", text)
            if m:
                result["approach"] = "APPROACH"
                result["runway"] = m.group(1)

        # Save JSON for later use
        if json_path is not None:
            os.makedirs(os.path.dirname(json_path), exist_ok=True)
            with open(json_path, "w") as f:
                json.dump(result, f, indent=4)
            self.logger.info(f"[Generate-JSON] JSON saved to {json_path}")

        # Log result JSON and elapsed time
        elapsed = time.time() - start_time
        self.logger.info(f"[Generate-JSON] Generated JSON '({elapsed:.2f}s)': {json.dumps(result, indent=4, ensure_ascii=False)}")

        self.logger.info(f"[Text→JSON] Parsed: {result}")
        return result


if __name__ == "__main__":
    parser = ATCTextToJSONRegex()
    tests = [
        "DELTA 209 TURN RIGHT HEADING 180 DESCEND TO 4000 FEET QNH 9 OR 9 OR 8 REDUCE SPEED TO 210 KNOTS",
        "FINNAIR 522 TURN LEFT HEADING 250 DESCENT TO FLIGHT LEVEL 360",
        "RYANAIR 12 CLIMB TO FLIGHT LEVEL 200 QNH 1013",
        "FINNAIR 350 CLEARED DIRECT LAKUT",
        "SCANDINAVIAN 421 CLEARED ILS APPROACH RWY 22"
    ]
    for t in tests:
        print("* " * 10)
        print(f"\nCommand: {t}")
        print("Parsed JSON:", parser.generate_json(t))
