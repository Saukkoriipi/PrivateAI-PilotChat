# Private AI-Pilot Chat App


![PrivateAI-PilotChat](img.png)

**PrivateAI-PilotChat** is an open-source, fully offline ATC–pilot voice communication simulator. It enables you to practice realistic air traffic control phraseology and pilot exchanges entirely on your own system.  
All processing — speech recognition, command interpretation, and voice synthesis — happens locally.  
No cloud. No data sharing. No subscriptions. 100% private and free.

> ⚙️ **Development Status:**  
> The project is in active development.  
> Current limitations include high VRAM usage, imperfect command parsing, and incomplete logging — all under active improvement.

---

## Features
- **Offline operation:** all inference runs on your device.
- **Voice I/O:** converts ATC audio to text and generates pilot speech responses.
- **Structured reasoning:** ATC commands parsed into machine-readable JSON.
- **Privacy-first:** nothing is sent to the cloud.
- **Training tool:** ideal for ATC students and simulator developers.

---

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/PrivateAI-PilotChat.git
   cd PrivateAI-PilotChat
````

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Download or place models**

   * ASR (Whisper)
   * LLM (ATC Assistant)
   * TTS (Pilot voice)

   > See `models/README.md` for setup instructions.

---

## Usage

Run the main pipeline:

```bash
python pipeline/pipeline.py
```

or launch the app UI:

```bash
python app.py
```

Then:

* Speak your ATC instruction.
* The system transcribes, interprets, and responds with a synthetic pilot voice.

---

## Project Structure

```
pipeline/
 ├── audio_to_text.py      # Whisper ASR
 ├── atc_assistant_llm.py  # Command parser and response logic
 ├── text_to_audio.py      # Pilot TTS generator
 ├── utils.py              # Audio utilities
 └── pipeline.py           # Main execution pipeline
```

---

## License

Licensed under the **MIT License**.
You are free to use, modify, and distribute with attribution.

---

*Work in progress — more documentation, model configuration, and UI details coming soon.*

```