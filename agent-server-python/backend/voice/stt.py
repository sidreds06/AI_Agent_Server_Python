import openai
import io

async def transcribe_audio(audio_bytes: bytes, file_ext: str = ".m4a") -> str:
    file_obj = io.BytesIO(audio_bytes)
    file_obj.name = "audio" + file_ext
    transcript_resp = openai.audio.transcriptions.create(
        model="whisper-1",
        file=file_obj,
        response_format="text"
    )
    # transcript_resp is just a string if you use response_format="text"
    return transcript_resp
