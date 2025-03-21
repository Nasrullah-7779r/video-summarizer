import os
import requests
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi
from dotenv import load_dotenv

load_dotenv()

def get_video_id(video_url: str) -> str:
    """Extract video ID from various YouTube URL formats"""
    parsed = urlparse(video_url)

    if parsed.hostname == 'youtu.be':
        return parsed.path[1:]
    if parsed.hostname in ('www.youtube.com', 'youtube.com'):
        if parsed.path == '/watch':
            return parse_qs(parsed.query).get('v', [None])[0]
        if parsed.path.startswith(('/embed/', '/v/')):
            return parsed.path.split('/')[2]
    return video_url.split('v=')[-1].split('&')[0]

def get_transcript(video_url: str) -> str:
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

def summarize_video(transcript: str) -> str:
    """Generate summary using Hugging Face model"""
    HF_TOKEN = os.environ["HF_TOKEN"]
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
    prompt = f"""<s>[INST] You are an assistant summarizing video transcripts.
            Summarize the following transcript in 1-3 concise paragraphs.
            Focus on key points, main arguments, and important details.
            Transcript: {transcript} [/INST]</s>"""

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_length": 1024,
            "min_length": 30,
            "do_sample": False,
            "return_full_text": False
        }
    }

    try:
        response = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {HF_TOKEN}"},
            json=payload
        )

        if response.status_code == 200:
            return response.json()[0]['generated_text']
        return None

    except requests.exceptions.RequestException as e:
        print(f"API request failed: {str(e)}")
        return None