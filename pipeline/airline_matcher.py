import pandas as pd
from difflib import get_close_matches
import logging
import re

class AirlineMatcher:
    """
    Load known airlines (ICAO code + CALLSIGN + PRONOUNCIATION) from CSV
    and always find the closest match for a given spoken CALLSIGN.
    """
    def __init__(self, csv_path: str = "airlines.csv", logger: logging.Logger = None):
        """
        Args:
            csv_path (str): Path to CSV file containing 'ICAO', 'CALLSIGN', 'PRONOUNCIATION' columns.
            logger (logging.Logger, optional): Logger for debug/info messages.
        """
        if logger is None:
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger("AirlineMatcher")
        else:
            self.logger = logger
        
        self.logger.info(f"[AirlineMatcher] Loading airline data from {csv_path}")
        self.airlines_df = pd.read_csv(csv_path, sep=";")
        required_cols = ['ICAO', 'CALLSIGN', 'PRONOUNCIATION']
        if not all(col in self.airlines_df.columns for col in required_cols):
            raise ValueError(f"CSV must contain columns: {required_cols}")
        
        # Build a list of all pronunciations for matching
        self.pronunciations = []
        for _, row in self.airlines_df.iterrows():
            if pd.isna(row['PRONOUNCIATION']) or row['PRONOUNCIATION'].strip() == "":
                self.pronunciations.append(row['CALLSIGN'].upper())
            else:
                # Split multiple pronunciations if comma-separated
                pron_list = [p.strip().upper() for p in row['PRONOUNCIATION'].split(",")]
                self.pronunciations.extend(pron_list)
        self.pronunciations = sorted(set(self.pronunciations))
        self.logger.info(f"[AirlineMatcher] Loaded {len(self.pronunciations)} pronunciations")

    def match_CALLSIGN(self, text_CALLSIGN: str):
        """
        Return the closest matching CALLSIGN based on PRONOUNCIATION.
        Appends trailing numeric suffix if present.

        Args:
            text_CALLSIGN (str): Spoken CALLSIGN to match.

        Returns:
            tuple: (ICAO code, official CALLSIGN with numeric suffix if present)
        """
        text_CALLSIGN = text_CALLSIGN.upper().replace(" ", "")

        # Extract trailing digits (flight numbers) if present
        m = re.match(r"([A-Z]+)(\d*)", text_CALLSIGN)
        letters_part = m.group(1)
        numbers_part = m.group(2) if m else ""

        # Match against PRONOUNCIATION column
        matches = get_close_matches(letters_part, self.pronunciations, n=1)
        if matches:
            best_pron = matches[0]
        else:
            best_pron = sorted(self.pronunciations)[0]

        # Find row(s) where PRONOUNCIATION or CALLSIGN matches best_pron
        row = self.airlines_df[
            self.airlines_df.apply(
                lambda r: best_pron in [r['CALLSIGN'].upper()] + 
                          ([p.strip().upper() for p in str(r['PRONOUNCIATION']).split(",")] if pd.notna(r['PRONOUNCIATION']) else []),
                axis=1
            )
        ].iloc[0]

        icao = row['ICAO']
        CALLSIGN = row['CALLSIGN'] + numbers_part  # append numeric suffix
        self.logger.info(f"[AirlineMatcher] Input '{text_CALLSIGN}' matched to '{CALLSIGN}' ({icao})")
        return icao, CALLSIGN


# Example usage
if __name__ == "__main__":
    matcher = AirlineMatcher()
    test_CALLSIGNs = ["SPEERBIRD", "SPIRBROUGH", "FINEIR522", "LUFTTHANSSA", "AIR CHINA552"]
    for c in test_CALLSIGNs:
        icao, CALLSIGN = matcher.match_CALLSIGN(c)
        print(f"Input: {c} → Matched ICAO: {icao}, CALLSIGN: {CALLSIGN}")
