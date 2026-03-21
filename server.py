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
import yt_dlp
import whisper
import torch
import base64
from fastapi import Query

from kokoro import KPipeline

device = "cuda" if torch.cuda.is_available() else "cpu"
whisper_model = whisper.load_model("large", device=device)  


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

class YoutubeRequest(BaseModel):
    url: str


@app.post("/yt/formats")
def get_formats(req: YoutubeRequest):

    ydl_opts = {"quiet": True}

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(req.url, download=False)

    formats = []

    for f in info["formats"]:
        formats.append({
            "format_id": f.get("format_id"),
            "ext": f.get("ext"),
            "resolution": f.get("resolution"),
            "filesize": f.get("filesize"),
            "acodec": f.get("acodec"),
            "vcodec": f.get("vcodec")
        })

    return {
        "title": info.get("title"),
        "formats": formats
    }


@app.get("/yt/download")
def download_video(url: str = Query(...), format_id: str = Query(...)):

    tmp_dir = tempfile.mkdtemp()

    ydl_opts = {
        "format": f"{format_id}+bestaudio/best",  # combine audio+video
        "outtmpl": f"{tmp_dir}/video.%(ext)s",
        "quiet": True,
        "noplaylist": True,
        "merge_output_format": "mp4",
        "extractor_args": {
            "youtube": {
                "player_client": ["android"]
            }
        }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url)
        filename = ydl.prepare_filename(info)

    return FileResponse(
        filename,
        media_type="video/mp4",
        filename="video.mp4",
        headers={
            "Content-Disposition": "attachment; filename=video.mp4"
        }
    )

@app.post("/yt/audio")
def download_audio(req: YoutubeRequest):

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    output_path = tmp.name + ".%(ext)s"

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "quiet": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(req.url)
        filename = ydl.prepare_filename(info)

    return FileResponse(filename, media_type="audio/mpeg")


class YoutubeProcessRequest(BaseModel):
    url: str
    voice: str
    speed: float = 1.0


import os

@app.post("/yt/process")
def process_youtube(req: YoutubeProcessRequest):

    # STEP 1: Download audio (NO ffmpeg conversion)
    tmp_dir = tempfile.mkdtemp()

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{tmp_dir}/audio.%(ext)s",
        "quiet": True,
        "noplaylist": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["android"]
            }
        }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(req.url)
        audio_path = ydl.prepare_filename(info)

    print("Audio downloaded:", audio_path)

    # STEP 2: Whisper (works with any format: webm/m4a/mp3)
    result = whisper_model.transcribe(audio_path)

    text = result["text"]
    print("Transcription done")

    # STEP 3: Kokoro TTS
    chunks = split_text(text)

    all_audio = []

    for chunk in tqdm(chunks, desc="Generating AI Voice"):
        generator = pipeline(chunk, voice=req.voice, speed=req.speed)
        for _, _, audio in generator:
            all_audio.append(audio)

    final_audio = np.concatenate(all_audio)

    tts_path = os.path.join(tmp_dir, "tts.wav")
    sf.write(tts_path, final_audio, 24000)

    print("TTS generated")

    # STEP 4: Convert to base64
    import base64
    with open(tts_path, "rb") as f:
        audio_base64 = base64.b64encode(f.read()).decode()

    return {
        "text": text,
        "audio": audio_base64
    }