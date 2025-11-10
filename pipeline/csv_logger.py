import pandas as pd
import os
import logging
from datetime import datetime

class CommandCSVLogger:
    """
    Logs parsed ATC command JSONs to a CSV file.
    Keeps a dataframe in memory and saves after each append.
    Automatically adds missing columns and timestamps.
    """

    def __init__(self, csv_path="commands_log.csv", logger: logging.Logger = None):
        """
        Initialize CSV logger.

        Args:
            csv_path (str): Path to the CSV log file.
            logger (logging.Logger, optional): Logger instance. If None, creates default.
        """
        self.csv_path = csv_path

        # Initialize logger
        if logger is None:
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger("CommandCSVLogger")
        else:
            self.logger = logger

        # Load existing CSV if exists, else initialize empty dataframe
        if os.path.exists(self.csv_path):
            self.df = pd.read_csv(self.csv_path, sep=";")
            self.logger.info(f"[CommandCSVLogger] Loaded existing CSV with {len(self.df)} rows.")
        else:
            self.df = pd.DataFrame()
            # Ensure timestamp column exists
            self.df["timestamp"] = []
            # Save initial CSV
            self.df.to_csv(self.csv_path, sep=";", index=False)
            self.logger.info(f"[CommandCSVLogger] Created new CSV at '{self.csv_path}'.")

    def append(self, atc_command: str, command_json: dict):
        """
        Append a new command JSON to the CSV log.
        Adds timestamp, stores the raw ATC command, and creates new columns if missing.
        Ensures 'timestamp' is column 1 and 'atc_command' is column 2.

        Args:
            atc_command (str): The raw ATC text command.
            command_json (dict): Parsed ATC command JSON.
        """
        # Make a copy to avoid mutating the original dict
        command_json = command_json.copy()

        # Add timestamp and raw ATC command
        command_json["timestamp"] = datetime.utcnow().isoformat()
        command_json["atc_command"] = atc_command

        # Add any new columns to the dataframe
        for key in command_json.keys():
            if key not in self.df.columns:
                self.df[key] = ""

        # Append the new row
        self.df = pd.concat([self.df, pd.DataFrame([command_json])], ignore_index=True)

        # Reorder columns: timestamp first, atc_command second, then others sorted alphabetically
        other_cols = [col for col in self.df.columns if col not in ("timestamp", "atc_command")]
        self.df = self.df[["timestamp", "atc_command"] + sorted(other_cols)]

        # Save to CSV
        self.df.to_csv(self.csv_path, sep=";", index=False)

        self.logger.info(f"[CommandCSVLogger] Appended command with timestamp {command_json['timestamp']}.")
