from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import numpy as np
import soundfile as sf
import tempfile
from tqdm import tqdm
import re

from kokoro import KPipeline

app = FastAPI()

# CORS MUST be here
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = KPipeline(
    repo_id="hexgrad/Kokoro-82M",
    lang_code="a"
)

class VoiceSampleRequest(BaseModel):
    voice: str

class EstimateRequest(BaseModel):
    text: str

class TTSRequest(BaseModel):
    text: str
    voice: str
    speed: float


def split_text(text, max_chars=350):
    sentences = re.split(r'(?<=[.!?]) +', text)
    chunks = []
    current = ""

    for s in sentences:
        if len(current) + len(s) < max_chars:
            current += s + ". "
        else:
            chunks.append(current.strip())
            current = s + ". "

    if current:
        chunks.append(current)

    return chunks


@app.post("/generate")
def generate(req: TTSRequest):

    chunks = split_text(req.text)

    all_audio = []

    print("Total chunks:", len(chunks))
    print("Generating audio...")

    for chunk in tqdm(chunks, desc="Generating narration"):

        generator = pipeline(
            chunk,
            voice=req.voice,
            speed=req.speed
        )

        for gs, ps, audio in generator:
            all_audio.append(audio)

    final_audio = np.concatenate(all_audio)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")

    sf.write(tmp.name, final_audio, 24000)

    return FileResponse(tmp.name, media_type="audio/wav")

@app.get("/voices")
def get_voices():
    # ✅ Load once at startup
    with open("voices.json", "r", encoding="utf-8") as f:
        voices = json.load(f)
    return voices

@app.post("/voice-sample")
def voice_sample(req: VoiceSampleRequest):

    text = "Hello. This is a sample voice from Kokoro."

    generator = pipeline(text, voice=req.voice, speed=1)

    audios = []

    for gs, ps, audio in generator:
        audios.append(audio)

    final_audio = np.concatenate(audios)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")

    sf.write(tmp.name, final_audio, 24000)

    return FileResponse(tmp.name, media_type="audio/wav")

@app.post("/estimate")
def estimate(req: EstimateRequest):

    words = len(req.text.split())

    duration = words / 150 * 60  # average speech

    return {
        "words": words,
        "estimated_seconds": duration
    }
