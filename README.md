# PrivateAI-PilotChat

PrivateAI-PilotChat is an open-source, fully offline ATC-pilot voice communication system. Practice and test how it feels to be an ATCO speaking with pilots. All transcription and responses stay local for full privacy—no cloud or external servers.

## Features
- Offline AI-powered voice communication.
- Audio-to-text transcription and text-to-audio response.
- Fully private: no data leaves your machine.
- Practice ATC-pilot interactions safely.

## Installation
1. Clone the repo:
   ```bash
   git clone https://github.com/yourusername/PrivateAI-PilotChat.git
   cd PrivateAI-PilotChat
````

2. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```
3. Download models for ASR, LLM, and TTS as per instructions in `models/`.

## Usage

Run the conversation frontend:

```bash
python app.py
```

* Press the record button to speak as ATCO.
* The AI generates pilot responses and plays them back.

## License

This project is licensed under the MIT License.

```