import pandas as pd
from difflib import get_close_matches
import logging
import re

class AirlineMatcher:
    """
    Load known airlines (ICAO code + CALLSIGN) from CSV and always find the closest match for a given CALLSIGN.
    """
    def __init__(self, csv_path: str = "airlines.csv", logger: logging.Logger = None):
        """
        Args:
            csv_path (str): Path to CSV file containing 'ICAO' and 'CALLSIGN' columns.
            logger (logging.Logger, optional): Logger for debug/info messages.
        """
        if logger is None:
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger("AirlineMatcher")
        else:
            self.logger = logger
        
        self.logger.info(f"[AirlineMatcher] Loading airline data from {csv_path}")
        self.airlines_df = pd.read_csv(csv_path, sep=";")
        if not all(col in self.airlines_df.columns for col in ['ICAO', 'CALLSIGN']):
            raise ValueError("CSV must contain 'ICAO' and 'CALLSIGN' columns.")
        
        self.CALLSIGNs = sorted(self.airlines_df['CALLSIGN'].tolist())
        self.logger.info(f"[AirlineMatcher] Loaded {len(self.CALLSIGNs)} CALLSIGNs: {self.CALLSIGNs}")

    def match_CALLSIGN(self, text_CALLSIGN: str):
        """
        Always return the closest matching CALLSIGN from known airlines.
        If numbers are at the end of the input, append them back to the matched CALLSIGN.

        Args:
            text_CALLSIGN (str): CALLSIGN to match.

        Returns:
            tuple: (ICAO code, official CALLSIGN with numeric suffix if present)
        """
        text_CALLSIGN = text_CALLSIGN.upper().replace(" ", "")

        # Extract trailing digits (flight numbers) if present
        m = re.match(r"([A-Z]+)(\d*)", text_CALLSIGN)
        letters_part = m.group(1)
        numbers_part = m.group(2) if m else ""

        # Find closest match for letters part
        matches = get_close_matches(letters_part, self.CALLSIGNs, n=1)
        if matches:
            best_match = matches[0]
        else:
            best_match = sorted(self.CALLSIGNs)[0]

        row = self.airlines_df[self.airlines_df['CALLSIGN'] == best_match].iloc[0]
        icao = row['ICAO']
        CALLSIGN = row['CALLSIGN'] + numbers_part  # append numeric suffix
        self.logger.info(f"[AirlineMatcher] Input '{text_CALLSIGN}' matched to '{CALLSIGN}' ({icao})")
        return icao, CALLSIGN

# Example usage
if __name__ == "__main__":
    matcher = AirlineMatcher()
    test_CALLSIGNs = ["SPEERBIRD", "SPIRBROUGH", "FINEIR522", "LUFTTHANSSA"]
    for c in test_CALLSIGNs:
        icao, CALLSIGN = matcher.match_CALLSIGN(c)
        print(f"Input: {c} → Matched ICAO: {icao}, CALLSIGN: {CALLSIGN}")
