# Kokoro TTS Studio

Kokoro TTS Studio is a lightweight **Text-to-Speech (TTS) narration generator** built using **FastAPI** and the **Kokoro-82M model**.
It provides a simple web interface where users can convert text into high-quality speech with voice selection, speed control, and audio download.

The system supports **long narration generation** by automatically splitting large text into smaller chunks before processing.

---

# Features

* High-quality **Text-to-Speech generation**
* **Kokoro-82M voice model**
* Dynamic **voice selection**
* **Voice sample preview**
* **Speed control**
* **Word and character counter**
* **Estimated narration duration**
* **Long text support** (automatic chunking)
* **Download generated audio**
* Lightweight **FastAPI backend**
* Simple **Web UI**

---

# Project Structure

```
kokoro-tts-studio
│
├── server.py           # FastAPI backend
├── index.html          # Web UI
├── requirements.txt    # Python dependencies
├── .gitignore
└── README.md
```

---

# Requirements

* Python **3.10+**
* pip
* FFmpeg (recommended)

---

# Install Dependencies

Install Python libraries:

```
pip install -r requirements.txt
```

Then install Kokoro separately:

```
pip install kokoro --no-build-isolation
```

---

# Running the Server

Start the FastAPI server:

```
uvicorn server:app --host 0.0.0.0 --port 8000
```

Server will start at:

```
http://localhost:8000
```

---

# Running the Web UI

Open the UI file directly:

```
index.html
```

Or serve it locally:

```
python -m http.server 3000
```

Open in browser:

```
http://localhost:3000
```

---

# API Endpoints

## Generate Speech

```
POST /generate
```

Request Example:

```
{
  "text": "Hello world",
  "voice": "af_heart",
  "speed": 1
}
```

Response:
Returns generated **WAV audio file**.

---

## Get Available Voices

```
GET /voices
```

Example response:

```
[
  "af_heart",
  "af_alloy",
  "af_sarah",
  "af_nicole"
]
```

---

## Voice Sample

```
POST /voice-sample
```

Request:

```
{
  "voice": "af_heart"
}
```

Returns a short **audio preview** of the selected voice.

---

## Estimate Narration Time

```
POST /estimate
```

Request:

```
{
  "text": "This is a sample text."
}
```

Response:

```
{
  "words": 5,
  "estimated_seconds": 2
}
```

---

# How It Works

1. User enters text in the UI.
2. Backend splits long text into smaller chunks.
3. Each chunk is processed by the **Kokoro TTS pipeline**.
4. Generated audio chunks are merged together.
5. Final narration is returned as a **WAV file**.

This allows the system to generate **long narrations without memory crashes**.

---

# Hardware Compatibility

The project is optimized to run on:

* CPU
* Low-memory GPUs
* 8GB RAM systems

Chunking ensures stable generation even for large text.

---

# Future Improvements

Possible upgrades:

* Audiobook generation
* Batch narration processing
* PDF / DOCX input
* Dark mode UI
* Waveform visualization
* Multi-language support
* Docker deployment

---

# License

Please follow the licensing terms of the **Kokoro-82M model** when using this project.

---

# Author

Shashank Singh Bisht
Software Developer | AI Enthusiast

---
