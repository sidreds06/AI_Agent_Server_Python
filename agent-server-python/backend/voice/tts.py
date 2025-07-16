import openai

async def synthesize_speech(text: str, voice: str = "alloy") -> bytes:
    tts_resp = openai.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text
    )
    return tts_resp.content
