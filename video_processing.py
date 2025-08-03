import os
import traceback
import httpx
import requests
import re
from youtube_transcript_api import YouTubeTranscriptApi
from dotenv import load_dotenv

load_dotenv()

# def get_video_id(video_url: str) -> str:
#     """Extract video ID from various YouTube URL formats"""
#     parsed = urlparse(video_url)
#     pdb.set_trace
    
#     if parsed.hostname == 'youtu.be':
#         return parsed.path[1:]
#     if parsed.hostname in ('www.youtube.com', 'youtube.com'):
#         if parsed.path == '/watch':
#             return parse_qs(parsed.query).get('v', [None])[0]
#         if parsed.path.startswith(('/embed/', '/v/')):
#             return parsed.path.split('/')[2]
#     return video_url.split('v=')[-1].split('&')[0]



def get_video_id(url: str) -> str | None:
    """
    Extracts the 11-char YouTube video ID from any of these formats:
      • https://youtu.be/<id>
      • https://www.youtube.com/watch?v=<id>
      • https://www.youtube.com/embed/<id>
    Returns None if it can’t find a match.
    """
    pattern = r'(?:v=|youtu\.be/|embed/)([A-Za-z0-9_-]{11})'
    pdb.set_trace()
    m = re.search(pattern, url)
    return m.group(1) if m else None

# def get_transcript(video_url: str) -> str:
    """Fetch and process YouTube transcript"""
    try:
        video_id = get_video_id(video_url)

        if not video_id:
            return "Error: Invalid YouTube URL"

        proxies  = {
        'http': "socks5://host.docker.internal:9050",
        'https': "socks5://host.docker.internal:9050",
        }

        transcript = YouTubeTranscriptApi.get_transcript(video_id, proxies=proxies)

        return " ".join([item['text'] for item in transcript])

    except Exception as e:
        return f"Error: {str(e)}"

# def get_transcript(video_url: str) -> str:
#     video_id = get_video_id(video_url)
#     if not video_id:
#         return "Error: Invalid YouTube URL"
#     try:
#         transcript = YouTubeTranscriptApi.get_transcript(video_id)
#         return " ".join(item["text"] for item in transcript)
#     except Exception as e:
#         return f"Error: {e}"

# def safe_transcript(video_id: str) -> str | None:
#     try:
        
#         ts = YouTubeTranscriptApi.list_transcripts(video_id)
#         for t in ts:
#             print(f"{t.language} ({t.language_code}), generated: {t.is_generated}")
#         # try manual or auto captions (preferring English)
#         segments = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
#         return " ".join(seg['text'] for seg in segments)
#     except (TranscriptsDisabled, NoTranscriptFound):
#         # no captions available at all
#         return None
#     except VideoUnavailable:
#         # bad ID or removed video
#         return None
#     except Exception as e:
#         # log any other parsing/network errors
#         print(f"[safe_transcript] unexpected error for {video_id!r}: {e}")
#         return None

def safe_transcript(video_id: str) -> str | None:
    try:
        # Add headers to mimic browser request
        YouTubeTranscriptApi._session = requests.Session()
        YouTubeTranscriptApi._session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        segments = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        return " ".join(seg['text'] for seg in segments)
    except Exception as e:
        print(f"[safe_transcript] error for {video_id!r}: {e}")
        return None

async def summarize_video(transcript: str) -> str:
    """Generate summary using Hugging Face model"""
    TOGETHER_AI_API_KEY = os.environ["TOGETHER_AI_API_KEY"]    
    
    body = {
    "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
    "messages": [
        {
            "role": "system", 
            "content": "You are an assistant summarizing video transcripts. Summarize the following transcript in 1-3 concise paragraphs. Focus on key points, main arguments, and important details."
        },
        {
            "role": "user",
            "content": f"Transcript: {transcript}"
        }
    ],
    "max_tokens": 512
}
    
    
    try:        
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
         response = await client.post(
                "https://api.together.xyz/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {TOGETHER_AI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=body
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