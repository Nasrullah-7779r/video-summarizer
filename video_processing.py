import os
import traceback
import httpx
import requests
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
from dotenv import load_dotenv

load_dotenv()


def get_video_id(video_url: str) -> str | None:
    """Extract YouTube video ID from common URL formats."""
    parsed = urlparse(video_url)
    if parsed.hostname == 'youtu.be':
        return parsed.path[1:]
    if parsed.hostname in ('www.youtube.com', 'youtube.com', 'm.youtube.com'):
        if parsed.path == '/watch':
            return parse_qs(parsed.query).get('v', [None])[0]
        if parsed.path.startswith(('/embed/', '/v/')):
            parts = parsed.path.split('/')
            return parts[2] if len(parts) > 2 else None
    # last resort, try parsing v param directly
    if 'v=' in video_url:
        return video_url.split('v=')[-1].split('&')[0]
    return None


def safe_transcript(video_id: str) -> str | None:
    """Try multiple ways to obtain an English transcript for a video ID."""
    try:
        # Prefer auto-generated English transcript if available
        transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
        try:
            t = transcripts.find_generated_transcript(['en'])
            return " ".join(seg['text'] for seg in t.fetch())
        except Exception:
            # Fallback to any English transcript
            segments = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
            return " ".join(seg['text'] for seg in segments)
    except TranscriptsDisabled:
        return None
    except Exception as e:
        print(f"[safe_transcript] error for {video_id!r}: {e}")
        return None


def get_transcript(video_url: str) -> str:
    video_id = get_video_id(video_url)
    if not video_id:
        return "Error: Invalid YouTube URL"

    transcript_text = safe_transcript(video_id)
    if transcript_text is None:
        return "Error: No transcript available or subtitles are disabled."
    return transcript_text


async def summarize_video(transcript: str) -> str:
    """Generate summary using Together AI chat completions API."""
    TOGETHER_AI_API_KEY = os.environ["TOGETHER_AI_API_KEY"]

    body = {
        "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an assistant summarizing video transcripts. "
                    "Summarize the following transcript in 1-3 concise paragraphs. "
                    "Focus on key points, main arguments, and important details."
                ),
            },
            {"role": "user", "content": f"Transcript: {transcript}"},
        ],
        "max_tokens": 512,
    }

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            response = await client.post(
                "https://api.together.xyz/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {TOGETHER_AI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=body,
            )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]

    except httpx.HTTPStatusError as http_err:
        print("HTTP error:", http_err)
        print("Response content:", http_err.response.text)
        return f"HTTP error occurred: {http_err}"
    except Exception as e:
        print("Unexpected error:", repr(e))
        traceback.print_exc()
        return f"Error: {str(e) or 'Unknown error occurred'}"
