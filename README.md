# ATC-Pilot Chat

![PrivateAI-PilotChat](img.png)

**PrivateAI-PilotChat** is an open-source, fully offline ATC–pilot voice communication simulator. It enables you to practice realistic air traffic control phraseology and pilot exchanges entirely on your own system.  
All processing — speech recognition, command interpretation, and voice synthesis — happens locally.  
No cloud. No data sharing. No subscriptions. 100% private and free.


> ⚙️ **Development Status:**
> The project is in active development.

### Current Limitations

* **Audio → JSON conversion**: Not always reliable; transcription and parsing may occasionally produce spelling mistakes.
* **JSON → Pilot readback**:

  * Full-featured TTS (text_to_speech.py) is slower (~3 seconds per response) but produces high-quality multi-voice output.
  * Fast TTS (text_to_speech_fast.py) is very quick (~0.3 seconds) but only supports a single voice.

* **Pipeline runtime**: Overall pipeline takes 2–5 seconds per run, depending on system setup.


> Improvements to command parsing, transcription reliability, and pipeline speed are actively underway.


> ✈️ **Designed for IFR and Area Control:**  
> Supports key ATC commands parsed into JSON for logging, analysis, or simulator integration. Easily extendable to include additional commands.


---

## Features
- **Fully offline operation:** all processing runs locally on your device, no internet required.
- **Voice input/output:** transcribes ATC audio to text and generates realistic pilot speech responses.
- **Structured reasoning:** ATC commands are parsed into machine-readable JSON for logging, analysis, or simulator integration.
- **Privacy-first design:** no data is sent to the cloud, ensuring complete confidentiality.
- **Supported ATC commands:**
  - **Vectoring:** turn left/right, fly heading
  - **Altitudes:** climb, descend, maintain flight level
  - **Speeds:** reduce, increase, maintain
  - **Clearances:** cleared for approach, cleared direct to fix

---
## 🎧 Audio Examples

Below are sample ATC–Pilot exchanges generated locally by **PrivateAI-PilotChat**:

### Example 1 — **British Airways**

**ATC Command:** `BAW327 turn left heading 270 descend to flight level 280`

<audio controls>  
  <source src="demo/input/atc1.wav" type="audio/wav">  
</audio>  

**Pilot Response:**

<audio controls>  
  <source src="demo/output/pilot1.wav" type="audio/wav">  
</audio>  

---

### Example 2 — **Delta Airlines**

**ATC Command:** `DAL209 turn right heading 180 descend to 4000 feet qnh 998 reduce speed to 210 knots`

<audio controls>  
  <source src="demo/input/atc2.wav" type="audio/wav">  
</audio>  

**Pilot Response:**

<audio controls>  
  <source src="demo/output/pilot2.wav" type="audio/wav">  
</audio>  

---

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/PrivateAI-PilotChat.git
   cd PrivateAI-PilotChat
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Download or place models**

   * No manual download is required. All necessary models (ASR, LLM, TTS) are automatically downloaded the first time you run the pipeline or app.

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
* The system will transcribe your audio, interpret the command, save it as structured JSON, and respond with a synthetic pilot voice.

---

## Project Structure

```
pipeline/
 ├── speech_to_text.py         # Converts ATC audio commands to text (Whisper ASR)
 ├── text_to_json.py           # Converts ATC text commands into structured JSON
 ├── json_to_pilot_reply.py    # Generates ICAO-style pilot readback from JSON
 ├── text_to_speech.py         # Full-featured pilot TTS (multiple voices, slower)
 ├── text_to_speech_fast.py    # Fast pilot TTS (single voice)
 └──  pipeline.py               # Main execution pipeline orchestrating the full flow

```

---

## License

Licensed under the **MIT License**.
You are free to use, modify, and distribute with attribution.

---

*Work in progress — more documentation, model configuration, and UI details coming soon.*
---