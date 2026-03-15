from kokoro import KPipeline
import soundfile as sf

pipeline = KPipeline(repo_id="hexgrad/Kokoro-82M", lang_code="a")


text = "Hello, this is a test voice generated using Kokoro text to speech."

generator = pipeline(text, voice="af_heart")

for i, (gs, ps, audio) in enumerate(generator):
    sf.write(f"output_{i}.wav", audio, 24000)

print("Audio generated successfully")